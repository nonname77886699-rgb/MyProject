import plotly.express as px
import streamlit as st

from dashboard_utils import load_retail_data, render_date_filter, render_header, render_styles, style_chart


render_styles()
render_header(
    "客戶分析",
    "分析客戶價值、回購行為與消費頻率。",
    "查看客戶消費貢獻、訂單頻率與回購概況。",
)

orders = load_retail_data()
if orders.empty or not {"CustomerID", "InvoiceNo", "OrderDate", "TotalPrice"}.issubset(orders.columns):
    st.warning("交易資料缺少客戶分析所需欄位，請確認 Online Retail CSV。")
    st.stop()

orders = render_date_filter(orders, "customer_date_range")
if orders.empty:
    st.info("所選日期區間沒有交易資料。")
    st.stop()

customers = (
    orders.dropna(subset=["CustomerID"])
    .groupby("CustomerID", as_index=False)
    .agg(訂單數=("InvoiceNo", "nunique"), 消費金額=("TotalPrice", "sum"))
)
customers["客戶類型"] = customers["訂單數"].map(
    lambda count: "單次購買" if count == 1 else "回購客戶"
)
repeat_customers = int(customers["訂單數"].gt(1).sum())
repeat_rate = repeat_customers / len(customers) * 100 if not customers.empty else 0

metrics = st.columns(3)
metrics[0].metric("客戶數", f"{len(customers):,}")
metrics[1].metric("回購客戶", f"{repeat_customers:,}")
metrics[2].metric("回購率", f"{repeat_rate:.1f}%")

left, right = st.columns(2)
with left:
    st.subheader("高消費客戶 TOP 10")
    top_customers = customers.nlargest(10, "消費金額").sort_values("消費金額")
    top_chart = px.bar(
        top_customers,
        x="消費金額",
        y=top_customers["CustomerID"].astype("Int64").astype(str),
        orientation="h",
        labels={"x": "消費金額（GBP）", "y": "客戶編號"},
    )
    st.plotly_chart(style_chart(top_chart), width="stretch")

with right:
    st.subheader("客戶訂單頻率分布")
    frequency_chart = px.histogram(
        customers,
        x="訂單數",
        nbins=20,
        labels={"訂單數": "每位客戶的訂單數", "count": "客戶數"},
    )
    st.plotly_chart(style_chart(frequency_chart), width="stretch")

st.subheader("單次購買與回購客戶")
segments = customers.groupby("客戶類型", as_index=False).agg(客戶數=("CustomerID", "count"))
segment_chart = px.pie(segments, names="客戶類型", values="客戶數", hole=0.55)
st.plotly_chart(style_chart(segment_chart, height=360), width="stretch")