import plotly.express as px
import streamlit as st

from dashboard_utils import load_retail_data, render_date_filter, render_header, render_styles, style_chart


render_styles()
render_header(
    "地區分析",
    "檢視各國市場營收、訂單分布與地理集中度。",
    "比較各市場營收、訂單數與客戶分布，快速識別主要市場。",
)

orders = load_retail_data()
if orders.empty or not {"Country", "InvoiceNo", "CustomerID", "OrderDate", "TotalPrice"}.issubset(orders.columns):
    st.warning("交易資料缺少地區分析所需欄位，請確認 Online Retail CSV。")
    st.stop()

orders = render_date_filter(orders, "market_date_range")
if orders.empty:
    st.info("所選日期區間沒有交易資料。")
    st.stop()

markets = (
    orders.groupby("Country", dropna=True, as_index=False)
    .agg(營收=("TotalPrice", "sum"), 訂單數=("InvoiceNo", "nunique"), 客戶數=("CustomerID", "nunique"))
)
top_market = markets.loc[markets["營收"].idxmax()]
metrics = st.columns(3)
metrics[0].metric("市場數", f"{len(markets):,}")
metrics[1].metric("營收最高市場", str(top_market["Country"]))
metrics[2].metric("最高市場營收占比", f"{top_market['營收'] / markets['營收'].sum():.1%}")

left, right = st.columns(2)
with left:
    st.subheader("各國營收 TOP 10")
    top_revenue = markets.nlargest(10, "營收").sort_values("營收")
    revenue_chart = px.bar(
        top_revenue,
        x="營收",
        y="Country",
        orientation="h",
        labels={"營收": "營收（GBP）", "Country": "國家"},
    )
    st.plotly_chart(style_chart(revenue_chart), width="stretch")

with right:
    st.subheader("各國訂單數 TOP 10")
    top_orders = markets.nlargest(10, "訂單數").sort_values("訂單數")
    order_chart = px.bar(
        top_orders,
        x="訂單數",
        y="Country",
        orientation="h",
        labels={"訂單數": "訂單數", "Country": "國家"},
    )
    st.plotly_chart(style_chart(order_chart), width="stretch")

st.subheader("各市場營收占比")
share_chart = px.pie(
    markets.nlargest(10, "營收"),
    names="Country",
    values="營收",
    hole=0.5,
)
st.plotly_chart(style_chart(share_chart, height=380), width="stretch")