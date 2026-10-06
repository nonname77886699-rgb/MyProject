                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        import streamlit as st

from dashboard_utils import first_column, load_retail_data, render_header, render_styles


render_styles()
render_header(
    "Retail Intelligence Hub",
    "把交易資料變成下一個決策",
    "集中查看 Online Retail 資料與四個 Power BI 分析工作區。",
)

data = load_retail_data()
invoice = first_column(data, "InvoiceNo", "Invoice", "Invoice Number")
customer = first_column(data, "CustomerID", "Customer ID")
country = first_column(data, "Country")
quantity = first_column(data, "Quantity")

col1, col2, col3, col4 = st.columns(4)
col1.metric("資料筆數", f"{len(data):,}" if not data.empty else "尚未載入")
col2.metric("訂單數", f"{data[invoice].nunique():,}" if invoice else "--")
col3.metric("客戶數", f"{data[customer].nunique():,}" if customer else "--")
col4.metric("市場數", f"{data[country].nunique():,}" if country else "--")

st.divider()
left, right = st.columns([1.2, 1])
with left:
    st.subheader("資料概況")
    if data.empty:
        st.info("找不到 Online Retail CSV，請確認資料檔位於 data/ 或專案根目錄。")
    else:
        preview_columns = [column for column in [invoice, customer, country, quantity] if column]
        st.dataframe(data[preview_columns].head(10), width="stretch", hide_index=True)
with right:
    st.subheader("分析入口")
    st.markdown(
        "從左側選擇分析頁面。每個頁面都預留 Power BI 報表嵌入區，"
        "可以獨立放置不同主題的 dashboard。"
    )