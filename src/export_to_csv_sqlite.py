import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

# 取得目前檔案的上一層（即專案根目錄 project/）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 將 data 與 logs 定位在專案根目錄下
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 1. 本機 MariaDB 連線配置 (請確認密碼)
DB_USER = "root"
DB_PASS = "1234"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "ecommerce_db"

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4")

# 2. 確保專案目錄下有 data/ 資料夾
data_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(data_dir, exist_ok=True)

# 3. 從 MariaDB 讀取最新完整資料
df_all = pd.read_sql("SELECT * FROM exchange_rates ORDER BY Date DESC, Currency ASC", engine)

# 4. 匯出 CSV 檔 (提供 Power BI / Excel 讀取)
csv_path = os.path.join(data_dir, "exchange_rates.csv")
df_all.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"📦 已成功匯出 CSV 檔至專案目錄: {csv_path}")

# 5. 同步匯出 SQLite (.db) 檔 (提供 Letos 免安裝檢視)
sqlite_path = os.path.join(data_dir, "ecommerce.db")
with sqlite3.connect(sqlite_path) as sqlite_conn:
    df_all.to_sql("exchange_rates", sqlite_conn, if_exists="replace", index=False)
print(f"💾 已成功匯出 SQLite 檔至專案目錄: {sqlite_path}")