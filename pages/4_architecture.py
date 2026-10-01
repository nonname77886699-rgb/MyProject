import streamlit as st

from dashboard_utils import render_header, render_styles


render_styles()
render_header(
    "Page 4 / Portfolio",
    "系統架構與創作者資訊",
    "從 API 擷取、Python ETL、資料庫落地到 Streamlit 交付的完整資料產品路徑。",
)

st.subheader("系統架構")
st.graphviz_chart(
    """
    digraph {
        rankdir=LR;
        graph [bgcolor="transparent", pad="0.2"];
        node [shape=box, style="rounded,filled", fontname="Microsoft JhengHei", color="#26736a", fillcolor="#dce9e4"];
        api [label="yfinance API"];
        python [label="Python\nETL + Pandas\n(src-layout)"];
        db [label="MariaDB\nSQLAlchemy"];
        sqlite [label="SQLite\nCSV artifacts"];
        app [label="Streamlit\nDashboard"];
        api -> python -> db -> sqlite -> app;
        python -> app [label="  Data delivery"];
    }
    """,
    use_container_width=True,
)

st.subheader("技術堆疊")
st.markdown("".join(f"<span class='tag'>{tag}</span>" for tag in ["Python", "Pandas", "Plotly", "SQLAlchemy", "MariaDB", "SQLite", "uv", "Git / GitHub", "Streamlit"]), unsafe_allow_html=True)

st.subheader("創作者")
left, right = st.columns([1.4, 1])
with left:
    st.markdown(
        "**業務背景 × 資料分析 × 自動化工程**\n\n"
        "擅長先釐清商業問題，再把資料清洗、匯率轉換、資料庫同步與視覺化串成可維護的解決方案。"
    )
with right:
    st.link_button("GitHub Repository", "https://github.com/")
    st.link_button("GitHub Pages 履歷", "https://pages.github.com/")