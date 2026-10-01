from datetime import date

import pandas as pd
import streamlit as st

from dashboard_utils import convert_to_twd, load_exchange_rates, load_retail_data, render_header, render_styles, to_excel_bytes


render_styles()
render_header(
    "Page 3 / Data Delivery",
    "數據探索與自訂匯出",
    "用日期與消費金額快速縮小資料範圍，交付可直接分析的 orders_with_rates 主表。",
)

orders = load_retail_data()
rates = load_exchange_rates()
if orders.empty:
    st.warning("找不到交易資料。")
    st.stop()

orders = convert_to_twd(orders, rates, "GBP")
min_date = orders["OrderDate"].min() if "OrderDate" in orders else date.today()
max_date = orders["OrderDate"].max() if "OrderDate" in orders else date.today()
date_range = st.date_input("日期區間", value=(min_date, max_date), min_value=min_date, max_value=max_date)
amount_max = float(orders["Revenue_TWD"].max()) if not orders.empty else 0
amount = st.slider("單筆消費金額門檻（TWD）", 0.0, max(amount_max, 1.0), 0.0, step=max(amount_max / 100, 1.0))
if "Country" in orders.columns:
    countries = sorted(orders["Country"].dropna().unique().tolist())
    selected_countries = st.multiselect("國家", countries, default=countries)
else:
    selected_countries = []

filtered = orders.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    filtered = filtered[
        filtered["OrderDate"].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
    ]
filtered = filtered[filtered["Revenue_TWD"] >= amount]
if selected_countries:
    filtered = filtered[filtered["Country"].isin(selected_countries)]
elif "Country" in orders.columns:
    filtered = filtered.iloc[0:0]
st.metric("符合條件的資料筆數", f"{len(filtered):,}")

columns = [column for column in ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "CustomerID", "Country", "TotalPrice", "Revenue_TWD"] if column in filtered]
st.caption(f"以下預覽前 1,000 筆；匯出會包含全部 {len(filtered):,} 筆符合條件的資料。")
st.dataframe(filtered[columns].head(1000), use_container_width=True, hide_index=True, height=480)
download_csv, download_excel = st.columns(2)
download_csv.download_button(
    "下載 UTF-8-SIG CSV",
    lambda: filtered[columns].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
    "orders_with_rates.csv",
    "text/csv",
    use_container_width=True,
)
download_excel.download_button(
    "下載 Excel",
    lambda: to_excel_bytes(filtered[columns]),
    "orders_with_rates.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)