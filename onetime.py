import os
import pandas as pd
import yfinance as yf

# 1. 定義路徑 (對齊專案 BASE_DIR 結構)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FILE_PATH = os.path.join(DATA_DIR, "Online_Retail_Clean.csv")

# 2. 讀取 CSV
try:
    df = pd.read_csv(FILE_PATH, encoding="UTF-8")
except UnicodeDecodeError:
    df = pd.read_csv(FILE_PATH, encoding="ISO-8859-1")

# 3. 轉為 Datetime 格式，並擷取純日期 (去除時間部分)
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
df["Date"] = df["InvoiceDate"].dt.date

# 4. 取得唯一日期列表、剔除轉型失敗的無效空值 (NaT) 並排序
distinct_dates_df = (
    df[["Date"]]
    .dropna()
    .drop_duplicates()
    .sort_values("Date")
    .reset_index(drop=True)
)

print(f"📊 不重複交易天數: {len(distinct_dates_df)} 天")

# 5. 取得資料集的最小與最大日期
min_date = distinct_dates_df["Date"].min()
max_date = distinct_dates_df["Date"].max()

print(f"🗓️ 訂單起始日期: {min_date}")
print(f"🗓️ 訂單結束日期: {max_date}")

# 6. 調用 yfinance 一次性抓取整段區間匯率 (以 GBP/TWD 為例)
# 註：yfinance 的 end 參數不包含當天，故加 1 天確保涵蓋 max_date
end_fetch_date = max_date + pd.Timedelta(days=1)
df_rates = yf.download("GBPTWD=X", start=str(min_date), end=str(end_fetch_date))['Close'].reset_index()

# 整理欄位名稱
df_rates.columns = ['Date', 'Rate']
df_rates['Currency'] = 'GBP/TWD'

# 7. 時間序列補齊：將外匯休市（週末/假日）用前一個工作天匯率（ffill）填補
df_rates['Date'] = pd.to_datetime(df_rates['Date'])
df_rates_full = (
    df_rates.set_index('Date')
    .resample('D')
    .ffill()
    .reset_index()
)
df_rates_full['Date'] = df_rates_full['Date'].dt.date

print("\n✅ 匯率抓取與連續日期補齊完成 (前 5 筆)：")
print(df_rates_full.head())

import sqlite3
    
# 8. 存入 SQLite 資料庫 (ecommerce.db)
db_path = os.path.join(DATA_DIR, "ecommerce.db")
conn = sqlite3.connect(db_path)

# 將 df_rates_full 寫入名為 'exchange_rates' 的資料表
# if_exists='replace' 表示若資料表已存在就覆蓋更新
df_rates_full.to_sql("exchange_rates", conn, if_exists="replace", index=False)

# 關閉連線
conn.close()

print(f"🎉 匯率資料已成功寫入資料庫：{db_path} (資料表: exchange_rates)")