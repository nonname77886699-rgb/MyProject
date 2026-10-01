import io
import os
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
LOG_PATH = ROOT / "logs" / "etl_pipeline.log"
DB_PATH = DATA_DIR / "ecommerce.db"


@st.cache_data(show_spinner=False)
def load_retail_data(cleaned: bool = True) -> pd.DataFrame:
    candidates = (
        [DATA_DIR / "Online_Retail_Clean.csv", ROOT / "Online_Retail_Clean.csv", DATA_DIR / "Online_Retail.csv", ROOT / "Online_Retail.csv"]
        if cleaned
        else [DATA_DIR / "Online_Retail.csv", ROOT / "Online_Retail.csv"]
    )
    for path in candidates:
        if path.exists():
            data = pd.read_csv(
                path,
                encoding_errors="ignore",
                dtype={
                    "invoice_no": "category",
                    "InvoiceNo": "category",
                    "stock_code": "category",
                    "StockCode": "category",
                    "description": "category",
                    "Description": "category",
                    "country": "category",
                    "Country": "category",
                },
            )
            return prepare_orders(data)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_exchange_rates() -> pd.DataFrame:
    for path in [DATA_DIR / "exchange_rates.csv", ROOT / "src" / "data" / "exchange_rates.csv"]:
        if path.exists():
            rates = pd.read_csv(path, parse_dates=["Date"])
            rates["Buy_Rate"] = pd.to_numeric(rates["Buy_Rate"], errors="coerce")
            rates["Sell_Rate"] = pd.to_numeric(rates["Sell_Rate"], errors="coerce")
            return rates.sort_values("Date")
    return pd.DataFrame(columns=["Date", "Currency", "Buy_Rate", "Sell_Rate"])


def prepare_orders(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    column_mapping = {
        "invoiceno": "InvoiceNo",
        "invoice": "InvoiceNo",
        "stockcode": "StockCode",
        "description": "Description",
        "quantity": "Quantity",
        "invoicedate": "InvoiceDate",
        "unitprice": "UnitPrice",
        "price": "UnitPrice",
        "customerid": "CustomerID",
        "country": "Country",
        "totalprice": "TotalPrice",
    }
    data = data.rename(
        columns={
            column: column_mapping.get(column.strip().lower().replace("_", "").replace(" ", ""), column)
            for column in data.columns
        }
    )
    for column in ["Quantity", "UnitPrice", "TotalPrice", "CustomerID"]:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    if "TotalPrice" not in data and {"Quantity", "UnitPrice"}.issubset(data.columns):
        data["TotalPrice"] = data["Quantity"] * data["UnitPrice"]
    if "InvoiceDate" in data:
        data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
        data["OrderDate"] = data["InvoiceDate"].dt.normalize()
    return data


def currency_rate(rates: pd.DataFrame, currency: str) -> float:
    latest = rates.loc[rates["Currency"].eq(currency)].sort_values("Date")
    if latest.empty:
        return 1.0
    return float(latest.iloc[-1]["Sell_Rate"])


def convert_to_twd(data: pd.DataFrame, rates: pd.DataFrame, currency: str) -> pd.DataFrame:
    result = data.copy()
    result["Revenue_TWD"] = result.get("TotalPrice", pd.Series(dtype=float)).fillna(0) * currency_rate(rates, currency)
    return result


def build_rfm(
    data: pd.DataFrame,
    value_column: str = "Revenue_TWD",
    value_multiplier: float = 1.0,
) -> pd.DataFrame:
    columns = ["CustomerID", "Recency", "Frequency", "Monetary", "R_Score", "F_Score", "M_Score", "Segment"]
    required = {"CustomerID", "InvoiceNo", "InvoiceDate", value_column}
    if data.empty or not required.issubset(data.columns):
        return pd.DataFrame(columns=columns)

    invoice_dates = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    reference_date = invoice_dates.max().normalize() + pd.Timedelta(days=1)
    rfm = data.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda values: (reference_date - values.max().normalize()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=(value_column, "sum"),
    )
    rfm = rfm.dropna(subset=["Recency"])
    rfm = rfm.loc[rfm["Monetary"] > 0].reset_index()
    if rfm.empty:
        return pd.DataFrame(columns=columns)
    rfm["Monetary"] *= value_multiplier

    for metric, score in [("Recency", "R_Score"), ("Frequency", "F_Score"), ("Monetary", "M_Score")]:
        rfm[score] = (rfm[metric].rank(method="average", pct=True) * 5).apply(lambda value: min(5, max(1, int(value + 0.999999))))
    rfm["R_Score"] = 6 - rfm["R_Score"]
    rfm["Segment"] = "一般客戶"
    rfm.loc[(rfm["R_Score"] >= 4) & (rfm["F_Score"] >= 4) & (rfm["M_Score"] >= 4), "Segment"] = "高價值客戶"
    rfm.loc[(rfm["F_Score"] >= 4) & (rfm["Segment"] == "一般客戶"), "Segment"] = "忠誠客戶"
    rfm.loc[(rfm["R_Score"] <= 2) & (rfm["F_Score"] >= 3), "Segment"] = "需喚回客戶"
    return rfm[columns]


def latest_rate_summary(rates: pd.DataFrame, currency: str) -> tuple[float | None, float | None]:
    current = rates.loc[rates["Currency"].eq(currency)].sort_values("Date")
    if current.empty:
        return None, None
    value = float(current.iloc[-1]["Sell_Rate"])
    change = None
    if len(current) > 1:
        previous = float(current.iloc[-2]["Sell_Rate"])
        change = ((value - previous) / previous) * 100 if previous else None
    return value, change


def to_excel_bytes(data: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data.to_excel(writer, index=False, sheet_name="orders_with_rates")
    return output.getvalue()


def file_timestamp(path: Path) -> str:
    if not path.exists():
        return "尚未建立"
    return pd.Timestamp.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def sqlite_status() -> tuple[str, int, str]:
    path = DB_PATH
    if not path.exists():
        return "未找到 SQLite", 0, "尚未建立"
    try:
        with sqlite3.connect(path) as connection:
            count = int(pd.read_sql("SELECT COUNT(*) AS count FROM exchange_rates", connection).iloc[0]["count"])
        return "SQLite 讀取正常", count, file_timestamp(path)
    except (OSError, sqlite3.Error, pd.errors.DatabaseError):
        return "SQLite 讀取失敗", 0, file_timestamp(path)


def read_log_tail(limit: int = 20) -> list[str]:
    path = LOG_PATH
    if not path.exists():
        return ["尚未找到 logs/etl_pipeline.log"]
    return path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]


def first_column(data: pd.DataFrame, *names: str) -> str | None:
    for name in names:
        if name in data.columns:
            return name
    return None


def metric_value(data: pd.DataFrame, *names: str) -> Any:
    column = first_column(data, *names)
    if column is None or data.empty:
        return None
    return data[column]


def render_header(eyebrow: str, title: str, description: str) -> None:
    st.markdown(f"<div class='eyebrow'>{eyebrow}</div>", unsafe_allow_html=True)
    st.title(title)
    st.caption(description)


def render_styles() -> None:
    st.markdown(
        """
        <style>
        :root { --ink: #172026; --muted: #64727a; --accent: #e56b4e; --cream: #f6f1e8; }
        .stApp { background: var(--cream); }
        [data-testid="stSidebar"] { background: #172026; }
        [data-testid="stSidebar"] * { color: #f6f1e8; }
        [data-testid="stSidebar"] hr { border-color: #435158; }
        .eyebrow { color: var(--accent); font-size: .78rem; font-weight: 700;
                   letter-spacing: .08em; text-transform: uppercase; }
        [data-testid="stMetric"] { background: rgba(255,255,255,.58); border: 1px solid #e3dace;
                                     border-radius: 8px; padding: 1rem; }
        .powerbi-note { background: #fffaf2; border-left: 4px solid var(--accent);
                        border-radius: 4px; padding: 1rem 1.1rem; color: var(--ink); }
         .tag { display: inline-block; background: #dce9e4; color: #21463f; padding: .35rem .7rem;
             margin: .2rem .25rem .2rem 0; border-radius: 999px; font-size: .85rem; }
         .status-ok { color: #16704b; font-weight: 700; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_powerbi_page(title: str, description: str, env_key: str) -> None:
    render_styles()
    render_header("Power BI workspace", title, description)
    url = os.getenv(env_key, "").strip()
    try:
        url = st.secrets.get(env_key, url).strip()
    except FileNotFoundError:
        pass

    if url:
        st.components.v1.iframe(url, height=720, scrolling=True)
        return

    st.markdown(
        f"""
        <div class='powerbi-note'>
        <strong>尚未設定 Power BI 報表</strong><br>
        請將此頁的公開嵌入網址放入環境變數 <code>{env_key}</code>，或放入
        <code>.streamlit/secrets.toml</code> 後重新整理頁面。
        </div>
        """,
        unsafe_allow_html=True,
    )
