import streamlit as st


st.set_page_config(
	page_title="Retail Intelligence Hub",
	page_icon="📊",
	layout="wide",
	initial_sidebar_state="expanded",
)


PAGES = [
	st.Page("pages/home.py", title="首頁", icon="🏠", default=True),
	st.Page("pages/revenue.py", title="營收總覽", icon="💰"),
	st.Page("pages/customer.py", title="客戶分析", icon="👥"),
	st.Page("pages/product.py", title="商品分析", icon="🛍️"),
	st.Page("pages/market.py", title="地區分析", icon="🌍"),
]


with st.sidebar:
	st.markdown("## Retail Intelligence")
	st.caption("Online Retail 分析工作台")
	st.divider()

navigation = st.navigation(PAGES)
navigation.run()
