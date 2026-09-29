import os
import sys
import logging
import sqlite3
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from screap3_yfinance import fetch_exchange_rates

# 取得目前檔案的上一層（即專案根目錄 project/）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 將 data 與 logs 定位在專案根目錄下
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. 配置 Logging 機制 (同時輸出至 Console 與 logs/etl.log 檔案)
# ---------------------------------------------------------
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_file_path = os.path.join(LOG_DIR, "etl_pipeline.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# ---------------------------------------------------------
# 2. 資料庫連線配置
# ---------------------------------------------------------
DB_USER = "root"
DB_PASS = "1234"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "ecommerce_db"

db_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

try:
    engine = create_engine(db_url, pool_recycle=3600)
    logging.info("SQLAlchemy Engine 建立成功")
except Exception as e:
    logging.critical(f"無法建立資料庫 Engine 連線: {e}")
    sys.exit(1)

# 建表 SQL (複合主鍵 Date + Currency)
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS exchange_rates (
    Date DATE NOT NULL,
    Currency VARCHAR(10) NOT NULL,
    Buy_Rate DECIMAL(10, 4),
    Sell_Rate DECIMAL(10, 4),
    Fetched_At DATETIME,
    PRIMARY KEY (Date, Currency)
);
"""

# ---------------------------------------------------------
# 3. 核心 Load 邏輯 (MariaDB Upsert)
# ---------------------------------------------------------
def load_rates_to_mariadb(df: pd.DataFrame):
    if df.empty:
        logging.warning("傳入的 DataFrame 為空，跳過 MariaDB 寫入作業。")
        return

    insert_sql = """
    INSERT INTO exchange_rates (Date, Currency, Buy_Rate, Sell_Rate, Fetched_At)
    VALUES (:Date, :Currency, :Buy_Rate, :Sell_Rate, :Fetched_At)
    ON DUPLICATE KEY UPDATE
        Buy_Rate = VALUES(Buy_Rate),
        Sell_Rate = VALUES(Sell_Rate),
        Fetched_At = VALUES(Fetched_At);
    """
    records = df.to_dict(orient='records')
    
    try:
        with engine.connect() as conn:
            conn.execute(text(CREATE_TABLE_SQL))
            result = conn.execute(text(insert_sql), records)
            conn.commit()
            logging.info(f"✅ MariaDB 數據寫入成功！受影響行數/更新筆數: {result.rowcount}")
    except Exception as e:
        logging.error(f"❌ MariaDB 數據寫入失敗: {e}")
        raise e

# ---------------------------------------------------------
# 4. 匯出邏輯 (專案目錄下的 data/ CSV & SQLite)
# ---------------------------------------------------------
def export_to_project():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        with engine.connect() as conn:
            df_all = pd.read_sql("SELECT * FROM exchange_rates ORDER BY Date DESC, Currency ASC", conn)

        # 匯出 CSV
        csv_path = os.path.join(data_dir, "exchange_rates.csv")
        df_all.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logging.info(f"📦 專案 CSV 檔同步完成: {csv_path} (總比數: {len(df_all)})")

        # 匯出 SQLite (.db)
        sqlite_path = os.path.join(data_dir, "ecommerce.db")
        with sqlite3.connect(sqlite_path) as sqlite_conn:
            df_all.to_sql("exchange_rates", sqlite_conn, if_exists="replace", index=False)
        logging.info(f"💾 專案 SQLite 檔同步完成: {sqlite_path}")

    except Exception as e:
        logging.error(f"❌ 專案檔案匯出過程發生錯誤: {e}")

# ---------------------------------------------------------
# 5. 主流程控制 (Main Entrypoint)
# ---------------------------------------------------------
def main():
    logging.info("=" * 50)
    logging.info("🚀 [ETL Pipeline 啟動] 開始執行自動化匯率更新任務...")
    
    try:
        # Step 1: Extract & Transform
        df_rates = fetch_exchange_rates()
        
        # Step 2: Load to MariaDB
        load_rates_to_mariadb(df_rates)
        
        # Step 3: Export Artifacts to project/data
        export_to_project()
        
        logging.info("🎉 [ETL Pipeline 完成] 所有自動化流程順利執行完畢！")
    except Exception as e:
        logging.critical(f"💥 [ETL Pipeline 異常終止]: {e}")
    finally:
        logging.info("=" * 50)

if __name__ == "__main__":
    main()