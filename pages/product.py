import plotly.express as px
import streamlit as st

from dashboard_utils import load_retail_data, render_date_filter, render_header, render_styles, style_chart


render_styles()
render_header(
    "商品分析",
    "比較商品銷量、營收貢獻與高低單價商品結構。",
    "依日期區間比較商品銷售額、銷量及平均售價。",
)

orders = load_retail_data()
required_columns = {"StockCode", "Description", "Quantity", "OrderDate", "TotalPrice"}
if orders.empty or not required_columns.issubset(orders.columns):
    st.warning("交易資料缺少商品分析所需欄位，請確認 Online Retail CSV。")
    st.stop()

orders = render_date_filter(orders, "product_date_range")
if orders.empty:
    st.info("所選日期區間沒有交易資料。")
    st.stop()

products = (
    orders.groupby(["StockCode", "Description"], dropna=True, as_index=False)
    .agg(銷量=("Quantity", "sum"), 銷售額=("TotalPrice", "sum"))
)
products["平均售價"] = products["銷售額"] / products["銷量"].where(products["銷量"].ne(0))
metrics = st.columns(3)
metrics[0].metric("商品數", f"{products['StockCode'].nunique():,}")
metrics[1].metric("總銷量", f"{orders['Quantity'].sum():,.0f}")
metrics[2].metric("商品總營收", f"£{orders['TotalPrice'].sum():,.0f}")

left, right = st.columns(2)
with left:
    st.subheader("商品營收 TOP 10")
    top_revenue = products.nlargest(10, "銷售額").sort_values("銷售額")
    revenue_chart = px.bar(
        top_revenue,
        x="銷售額",
        y="Description",
        orientation="h",
        labels={"銷售額": "銷售額（GBP）", "Description": "商品"},
    )
    st.plotly_chart(style_chart(revenue_chart), width="stretch")

with right:
    st.subheader("商品銷量 TOP 10")
    top_quantity = products.nlargest(10, "銷量").sort_values("銷量")
    quantity_chart = px.bar(
        top_quantity,
        x="銷量",
        y="Description",
        orientation="h",
        labels={"銷量": "銷量（件）", "Description": "商品"},
    )
    st.plotly_chart(style_chart(quantity_chart), width="stretch")

st.subheader("商品銷量與營收關係")
scatter = px.scatter(
    products.nlargest(100, "銷售額"),
    x="銷量",
    y="銷售額",
    hover_name="Description",
    labels={"銷量": "銷量（件）", "銷售額": "銷售額（GBP）"},
)
st.plotly_chart(style_chart(scatter), width="stretch")