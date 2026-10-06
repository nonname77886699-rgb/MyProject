import plotly.express as px
import pandas as pd
import streamlit as st

from dashboard_utils import load_retail_data, render_date_filter, render_header, render_styles, style_chart


render_styles()
render_header(
    "營收總覽",
    "掌握營收、訂單量、平均客單價與時間趨勢。",
    "依日期區間檢視營收走勢、訂單量與每月平均客單價。",
)

orders = load_retail_data()
if orders.empty or not {"InvoiceNo", "OrderDate", "TotalPrice"}.issubset(orders.columns):
    st.warning("交易資料缺少營收分析所需欄位，請確認 Online Retail CSV。")
    st.stop()

orders = render_date_filter(orders, "revenue_date_range")
if orders.empty:
    st.info("所選日期區間沒有交易資料。")
    st.stop()

monthly = (
    orders.assign(Month=pd.to_datetime(orders["OrderDate"]).dt.to_period("M").dt.to_timestamp())
    .groupby("Month", as_index=False)
    .agg(
        營收=("TotalPrice", "sum"),
        訂單數=("InvoiceNo", "nunique"),
        平均客單價=("TotalPrice", lambda values: values.sum() / orders.loc[values.index, "InvoiceNo"].nunique()),
    )
)
total_revenue = orders["TotalPrice"].sum()
order_count = orders["InvoiceNo"].nunique()
metrics = st.columns(3)
metrics[0].metric("總營收（GBP）", f"£{total_revenue:,.0f}")
metrics[1].metric("訂單數", f"{order_count:,}")
metrics[2].metric("平均客單價", f"£{total_revenue / order_count:,.2f}" if order_count else "£0")

st.subheader("每月營收趨勢")
revenue_chart = px.area(monthly, x="Month", y="營收", markers=True, labels={"Month": "月份", "營收": "營收（GBP）"})
st.plotly_chart(style_chart(revenue_chart), width="stretch")

st.subheader("每月訂單數與平均客單價")
monthly_long = monthly.melt(
    id_vars="Month",
    value_vars=["訂單數", "平均客單價"],
    var_name="指標",
    value_name="數值",
)
order_chart = px.line(
    monthly_long,
    x="Month",
    y="數值",
    color="指標",
    markers=True,
    labels={"Month": "月份", "數值": "訂單數／平均客單價"},
)
st.plotly_chart(style_chart(order_chart, height=360), width="stretch")