import os
import re
import threading
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pyodbc

pyodbc.pooling = False

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"

oltp_lock = threading.RLock()
dw_lock = threading.RLock()

_OLTP_DELETE = [
    "lan_lam_bai",
    "phien_hoc",
    "su_kien_hoc_vu",
    "cau_hoi",
    "de_thi",
    "bai_hoc",
    "hoc_sinh",
    "mon_hoc",
]
_DW_DELETE = [
    "fact_ket_qua_thi",
    "fact_chuyen_can",
    "etl_reject",
    "etl_batch",
    "etl_watermark",
    "dim_de_thi",
    "dim_bai_hoc",
    "dim_mon_hoc",
    "dim_hoc_sinh",
    "dim_thoi_gian",
]


class Row(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return dict.__getitem__(self, key)


class _Result:
    def __init__(self, raw, cursor, sql: str, new_id):
        self.raw = raw
        self.cursor = cursor
        self.sql = sql
        self._new_id = new_id

    def _pack(self, record):
        packed = Row()
        for column, value in zip(self.cursor.description, record):
            packed[column[0]] = _python(value)
        return packed

    def fetchone(self):
        record = self.cursor.fetchone()
        if record is None:
            return None
        return self._pack(record)

    def fetchall(self):
        return [self._pack(record) for record in self.cursor.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def lastrowid(self):
        return self._new_id


class _Empty:
    lastrowid = None

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def __iter__(self):
        return iter(())


class SqlConn:
    def __init__(self, raw):
        self.raw = raw

    def execute(self, sql: str, args=()):
        statement, mode = _translate(sql)
        if mode == "noop":
            return _Empty()
        wants_id = statement.lstrip()[:6].upper() == "INSERT" and "OUTPUT" not in statement.upper()
        if wants_id:
            statement = statement.rstrip().rstrip(";") + "; SELECT CAST(SCOPE_IDENTITY() AS INT) AS new_id"
        cursor = self.raw.cursor()
        try:
            if args:
                cursor.execute(statement, args)
            else:
                cursor.execute(statement)
        except pyodbc.Error as exc:
            if mode == "ignore" and _duplicate(exc):
                return _Empty()
            raise
        new_id = None
        if wants_id:
            while cursor.description is None:
                if not cursor.nextset():
                    break
            if cursor.description is not None:
                found = cursor.fetchone()
                if found and found[0] is not None:
                    new_id = int(found[0])
            return _Result(self.raw, cursor, statement, new_id)
        if cursor.description is None:
            try:
                while cursor.nextset():
                    pass
            except pyodbc.Error:
                pass
            return _Empty()
        return _Result(self.raw, cursor, statement, None)

    def executemany(self, sql: str, seq):
        statement, mode = _translate(sql)
        cursor = self.raw.cursor()
        rows = [tuple(row) for row in seq]
        if mode == "ignore":
            for row in rows:
                try:
                    cursor.execute(statement, row)
                except pyodbc.Error as exc:
                    if not _duplicate(exc):
                        raise
            return
        cursor.fast_executemany = True
        cursor.executemany(statement, rows)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()


def _python(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value


def _duplicate(exc: pyodbc.Error) -> bool:
    text = str(exc)
    return "2627" in text or "2601" in text


def _apply_top(sql: str) -> str:
    stripped = sql.rstrip().rstrip(";")
    match = re.search(r"(?is)\bLIMIT\s+(\d+)\s*$", stripped)
    if not match:
        return sql
    body = stripped[: match.start()].rstrip()
    depth = 0
    last = None
    for token in re.finditer(r"\bSELECT\b|\(|\)", body, re.I):
        word = token.group(0).upper()
        if word == "(":
            depth += 1
        elif word == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            last = token
    if last is None:
        return sql
    return body[: last.end()] + f" TOP ({match.group(1)})" + body[last.end() :]


def _translate(sql: str):
    text = sql.strip()
    upper = text.upper()
    if upper.startswith("RELEASE SAVEPOINT"):
        return text, "noop"
    if upper.startswith("SAVEPOINT"):
        name = text.split()[1].rstrip(";")
        return f"SAVE TRANSACTION {name}", "run"
    if upper.startswith("ROLLBACK TO SAVEPOINT"):
        name = text.split()[-1].rstrip(";")
        return f"ROLLBACK TRANSACTION {name}", "run"
    mode = "run"
    if re.search(r"(?is)\bINSERT\s+OR\s+IGNORE\b", text):
        text = re.sub(r"(?is)\bINSERT\s+OR\s+IGNORE\b", "INSERT", text, count=1)
        mode = "ignore"
    return _apply_top(text), mode


def server_name() -> str:
    return os.environ.get("MSSQL_SERVER", r"(localdb)\MSSQLLocalDB")


def db_names() -> tuple[str, str]:
    suffix = os.environ.get("LEARNDW_DB_SUFFIX", "")
    if not re.fullmatch(r"[A-Za-z0-9_]*", suffix):
        raise RuntimeError("LEARNDW_DB_SUFFIX chỉ được gồm chữ, số và dấu gạch dưới")
    return f"OLTP_QuanLyHocTap{suffix}", f"DW_QuanLyHocTap{suffix}"


def _connection_string(database: str) -> str:
    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server_name()};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


def _open(database: str) -> SqlConn:
    raw = pyodbc.connect(_connection_string(database), timeout=30, autocommit=False)
    raw.cursor().execute(
        """
        SET ANSI_NULLS ON;
        SET QUOTED_IDENTIFIER ON;
        SET ANSI_PADDING ON;
        SET ANSI_WARNINGS ON;
        SET CONCAT_NULL_YIELDS_NULL ON;
        SET ARITHABORT ON;
        SET NUMERIC_ROUNDABORT OFF;
        """
    )
    return SqlConn(raw)


def oltp_conn() -> SqlConn:
    return _open(db_names()[0])


def dw_conn() -> SqlConn:
    return _open(db_names()[1])


def rows(conn: SqlConn, sql: str, args=()):
    return [dict(record) for record in conn.execute(sql, args)]


def _master():
    raw = pyodbc.connect(_connection_string("master"), timeout=30, autocommit=True)
    return raw


def _ensure_database(name: str) -> None:
    master = _master()
    try:
        master.cursor().execute(
            f"IF DB_ID(N'{name}') IS NULL CREATE DATABASE [{name}] COLLATE Vietnamese_CI_AS"
        )
    finally:
        master.close()


def _batches(name: str):
    text = (SQL_DIR / name).read_text(encoding="utf-8")
    chunk = []
    for line in text.splitlines():
        if line.strip().upper() == "GO":
            batch = "\n".join(chunk).strip()
            if batch:
                yield batch
            chunk = []
        else:
            chunk.append(line)
    tail = "\n".join(chunk).strip()
    if tail:
        yield tail


def _object_name(batch: str, kind: str):
    if kind == "table":
        match = re.search(r"(?is)\bCREATE\s+TABLE\s+(?:dbo\.)?(\w+)", batch)
    elif kind == "view":
        match = re.search(r"(?is)\bCREATE\s+VIEW\s+(?:dbo\.)?(\w+)", batch)
    else:
        match = re.search(
            r"(?is)\bCREATE\s+(?:UNIQUE\s+)?(?:NONCLUSTERED\s+|CLUSTERED\s+)?INDEX\s+(\w+)",
            batch,
        )
    return match.group(1) if match else None


def _apply(conn: SqlConn, filename: str) -> None:
    for batch in _batches(filename):
        table = _object_name(batch, "table")
        view = _object_name(batch, "view")
        index = _object_name(batch, "index")
        if table:
            exists = conn.execute("SELECT OBJECT_ID(?, 'U')", (f"dbo.{table}",)).fetchone()[0]
            if exists:
                continue
        elif view:
            exists = conn.execute("SELECT OBJECT_ID(?, 'V')", (f"dbo.{view}",)).fetchone()[0]
            if exists:
                continue
        elif index:
            exists = conn.execute("SELECT 1 FROM sys.indexes WHERE name = ?", (index,)).fetchone()
            if exists:
                continue
        conn.execute(batch)
    conn.commit()


def init_schemas() -> None:
    oltp_name, dw_name = db_names()
    _ensure_database(oltp_name)
    _ensure_database(dw_name)
    with oltp_lock:
        conn = oltp_conn()
        try:
            _apply(conn, "app_oltp.sql")
        finally:
            conn.close()
    with dw_lock:
        conn = dw_conn()
        try:
            _apply(conn, "app_dw.sql")
        finally:
            conn.close()


def wipe(conn: SqlConn) -> None:
    marker = conn.execute("SELECT OBJECT_ID('dbo.lan_lam_bai', 'U')").fetchone()[0]
    order = _OLTP_DELETE if marker else _DW_DELETE
    existing = {row[0] for row in conn.execute("SELECT name FROM sys.tables")}
    for name in order:
        if name in existing:
            conn.execute(f"DELETE FROM dbo.[{name}]")
    conn.commit()


def drop_databases() -> None:
    oltp_name, dw_name = db_names()
    master = _master()
    try:
        cursor = master.cursor()
        for name in (dw_name, oltp_name):
            cursor.execute(
                f"""
                IF DB_ID(N'{name}') IS NOT NULL
                BEGIN
                    ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                    DROP DATABASE [{name}];
                END
                """
            )
    finally:
        master.close()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def date_key_of(ts) -> int:
    if isinstance(ts, datetime):
        return ts.year * 10000 + ts.month * 100 + ts.day
    if isinstance(ts, date):
        return ts.year * 10000 + ts.month * 100 + ts.day
    year, month, day = [int(part) for part in str(ts)[:10].split("-")]
    return year * 10000 + month * 100 + day
