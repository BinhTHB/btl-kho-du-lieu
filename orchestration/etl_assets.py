from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dagster import Definitions, ScheduleDefinition, asset, define_asset_job

from app.etl import step_audit, step_extract, step_load_facts, step_quality_gate, step_scd2


@asset
def oltp_extracted_batch(context) -> dict:
    res = step_extract()
    context.log.info(
        f"batch_id={res.get('batch_id')} src_exam={res.get('src_exam', 0)} "
        f"src_session={res.get('src_session', 0)} src_event={res.get('src_event', 0)} "
        f"has_data={res.get('has_data')}"
    )
    return res


@asset
def quality_gate_checked(context, oltp_extracted_batch: dict) -> dict:
    if not oltp_extracted_batch.get("has_data"):
        context.log.info("Không có dữ liệu mới trong OLTP")
        return oltp_extracted_batch
    q = step_quality_gate(oltp_extracted_batch["batch_id"])
    context.log.info(f"quality_gate_checked: {q}")
    return {**oltp_extracted_batch, **q}


@asset
def dim_hoc_sinh_scd2(context, quality_gate_checked: dict) -> dict:
    if not quality_gate_checked.get("has_data"):
        return quality_gate_checked
    s = step_scd2(quality_gate_checked["batch_id"])
    context.log.info(f"dim_hoc_sinh_scd2: {s}")
    return {**quality_gate_checked, **s}


@asset
def dw_fact_tables(context, dim_hoc_sinh_scd2: dict) -> dict:
    if not dim_hoc_sinh_scd2.get("has_data"):
        return dim_hoc_sinh_scd2
    f = step_load_facts(dim_hoc_sinh_scd2["batch_id"])
    context.log.info(f"dw_fact_tables: {f}")
    return {**dim_hoc_sinh_scd2, **f}


@asset
def dw_audit_and_summary(context, dw_fact_tables: dict) -> dict:
    if not dw_fact_tables.get("has_data"):
        context.log.info("Bỏ qua audit: không có dữ liệu mới")
        return {"status": "BO_QUA"}
    final_stats = step_audit(dw_fact_tables["batch_id"], dw_fact_tables)
    context.log.info(
        f"Doi soat Nguon=Nap+Loai | exam: {final_stats.get('src_exam')}="
        f"{final_stats.get('loaded_exam')}+{final_stats.get('rejected_exam')} | "
        f"session: {final_stats.get('src_session')}="
        f"{final_stats.get('loaded_session')}+{final_stats.get('rejected_session')}"
    )
    return final_stats


etl_job = define_asset_job(name="dw_quan_ly_hoc_tap_etl", selection="*")
etl_schedule = ScheduleDefinition(
    job=etl_job,
    cron_schedule="*/2 * * * *",
)
defs = Definitions(
    assets=[
        oltp_extracted_batch,
        quality_gate_checked,
        dim_hoc_sinh_scd2,
        dw_fact_tables,
        dw_audit_and_summary,
    ],
    jobs=[etl_job],
    schedules=[etl_schedule],
)
