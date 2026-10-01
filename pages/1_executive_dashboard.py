import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from dashboard_utils import (
    build_rfm,
    convert_to_twd,
    currency_rate,
    first_column,
    latest_rate_summary,
    load_exchange_rates,
    load_retail_data,
    render_header,
    render_styles,
)


render_styles()
render_header(
    "Page 1 / Executive Dashboard",
    "跨境營收與匯率敏感度儀表板",
    "把 ETL 後的交易事實轉成可閱讀的營收、匯率與市場決策訊號。",
)

orders = load_retail_data()
rates = load_exchange_rates()
currency = st.selectbox("匯率基準", ["GBP", "EUR", "USD"], format_func=lambda value: f"{value} / TWD")
orders_twd = convert_to_twd(orders, rates, currency)
rate, change = latest_rate_summary(rates, currency)
invoice = first_column(orders, "InvoiceNo", "Invoice")

total_revenue = orders_twd["Revenue_TWD"].sum() if not orders_twd.empty else 0
order_count = orders[invoice].nunique() if invoice and not orders.empty else 0
aov = total_revenue / order_count if order_count else 0
metrics = st.columns(4)
metrics[0].metric("總營收（折算 TWD）", f"NT$ {total_revenue:,.0f}")
metrics[1].metric("總訂單數", f"{order_count:,}")
metrics[2].metric("平均客單價 AOV", f"NT$ {aov:,.0f}")
metrics[3].metric(f"最新 {currency} / TWD", f"{rate:,.4f}" if rate else "--", f"{change:+.2f}%" if change is not None else "單日資料")

if orders.empty:
    st.warning("找不到交易資料，請確認 Online_Retail_Clean.csv 位於專案根目錄。")
else:
    daily = orders_twd.dropna(subset=["InvoiceDate"]).groupby("OrderDate", as_index=False).agg(Revenue_TWD=("Revenue_TWD", "sum"))
    daily["Date"] = daily["OrderDate"].astype("datetime64[ns]")
    rate_daily = rates.loc[rates["Currency"].eq(currency), ["Date", "Sell_Rate"]].rename(columns={"Sell_Rate": "Rate"})
    daily = daily.merge(rate_daily, on="Date", how="left")
    chart = make_subplots(specs=[[{"secondary_y": True}]])
    chart.add_trace(go.Scatter(x=daily["Date"], y=daily["Revenue_TWD"], name="每日營收 TWD", line={"color": "#e56b4e"}), secondary_y=False)
    chart.add_trace(go.Scatter(x=daily["Date"], y=daily["Rate"], name=f"{currency} 匯率", line={"color": "#26736a"}), secondary_y=True)
    chart.update_yaxes(title_text="營收（TWD）", secondary_y=False)
    chart.update_yaxes(title_text=f"{currency} / TWD", secondary_y=True)
    chart.update_layout(height=420, margin={"t": 30, "r": 20, "b": 20, "l": 20}, legend={"orientation": "h"})
    st.plotly_chart(chart, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("熱門商品 TOP 10")
        product = orders_twd.groupby("Description", dropna=True).agg(銷量=("Quantity", "sum"), 銷售額=("Revenue_TWD", "sum")).reset_index()
        product = product.sort_values("銷售額", ascending=False).head(10).sort_values("銷售額")
        st.bar_chart(product.set_index("Description"), y=["銷售額", "銷量"], horizontal=True)
    with right:
        st.subheader("主要買家國家")
        countries = orders_twd.groupby("Country", dropna=True)["Revenue_TWD"].sum().nlargest(10).sort_values()
        st.bar_chart(countries, horizontal=True)

    rfm = build_rfm(orders, value_column="TotalPrice", value_multiplier=currency_rate(rates, currency))
    if not rfm.empty:
        st.subheader("RFM 顧客分群")
        st.caption("Recency 以資料集最後交易日為基準；Frequency 為不同訂單數，Monetary 為折算後消費額。")
        rfm_chart = px.scatter(
            rfm,
            x="Recency",
            y="Monetary",
            size="Frequency",
            color="Segment",
            hover_name="CustomerID",
            labels={"Recency": "距最近交易天數", "Monetary": "累計消費額（TWD）", "Frequency": "訂單數", "Segment": "客群"},
        )
        rfm_chart.update_layout(height=440, margin={"t": 20, "r": 20, "b": 20, "l": 20})
        st.plotly_chart(rfm_chart, use_container_width=True)
        segments = rfm["Segment"].value_counts().rename_axis("客群").to_frame("顧客數")
        st.dataframe(segments, use_container_width=True)