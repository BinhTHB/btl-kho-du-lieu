import pyodbc

cs = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\\MSSQLLocalDB;"
    "Trusted_Connection=yes;DATABASE=master"
)
conn = pyodbc.connect(cs, autocommit=True)
cur = conn.cursor()
row = cur.execute(
    "SELECT @@VERSION, CAST(DATABASEPROPERTYEX('master','Collation') AS nvarchar(128))"
).fetchone()
print(row[0].splitlines()[0])
print("collation", row[1])
found = cur.execute(
    "SELECT name FROM sys.fn_helpcollations() WHERE name = 'Vietnamese_CI_AS'"
).fetchall()
print("vietnamese", bool(found))
