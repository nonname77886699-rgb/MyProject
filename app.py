import streamlit as st


st.set_page_config(
	page_title="Retail Intelligence Hub",
	page_icon="📊",
	layout="wide",
	initial_sidebar_state="expanded",
)


PAGES = [
	st.Page("pages/1_executive_dashboard.py", title="跨境營收儀表板", icon="📈", default=True),
	st.Page("pages/2_etl_monitor.py", title="ETL 品質監控", icon="⚙️"),
	st.Page("pages/3_data_explorer.py", title="數據探索與匯出", icon="🔎"),
	st.Page("pages/4_architecture.py", title="系統架構與創作者", icon="🧭"),
]


with st.sidebar:
	st.markdown("## Cross-border ETL")
	st.caption("電商數據自動化 ETL Pipeline")
	st.divider()

navigation = st.navigation(PAGES)
navigation.run()
