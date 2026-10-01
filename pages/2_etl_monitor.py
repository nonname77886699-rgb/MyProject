from pathlib import Path

import streamlit as st

from dashboard_utils import (
    ROOT,
    file_timestamp,
    load_retail_data,
    read_log_tail,
    render_header,
    render_styles,
    sqlite_status,
)


render_styles()
render_header(
    "Page 2 / Data Engineering",
    "ETL 流水線與數據品質監控",
    "用資料筆數、檔案時間戳與 pipeline log 快速判斷自動化任務健康度。",
)

raw = load_retail_data(cleaned=False)
clean = load_retail_data(cleaned=True)
sqlite_label, sqlite_rows, sqlite_time = sqlite_status()
log_text = "\n".join(read_log_tail())
pipeline_ok = "ETL Pipeline 完成" in log_text and "SQLite" in log_text

status = st.columns(4)
status[0].metric("MariaDB", "同步正常" if pipeline_ok else "請檢查 log")
status[1].metric("SQLite", sqlite_label)
status[2].metric("最新寫入", file_timestamp(ROOT / "data" / "ecommerce.db"))
status[3].metric("SQLite 匯率筆數", f"{sqlite_rows:,}")
st.success("🟢 MariaDB / SQLite 雙向同步正常" if pipeline_ok else "🟠 最近一次 ETL 需要人工檢查")

st.subheader("Data Profiling")
invalid_customer = int(raw["CustomerID"].isna().sum()) if "CustomerID" in raw else 0
returns = int((raw["Quantity"] < 0).sum()) if "Quantity" in raw else 0
profile = st.columns(3)
profile[0].metric("原始資料筆數", f"{len(raw):,}")
profile[1].metric("清洗後資料筆數", f"{len(clean):,}", f"{len(clean) - len(raw):,}")
profile[2].metric("剔除風險筆數", f"{invalid_customer + returns:,}", f"CustomerID {invalid_customer:,} / 退貨 {returns:,}")

st.subheader("System Log Viewer")
st.code(log_text or "尚未有 ETL 日誌", language="log")