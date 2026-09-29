import requests
import pandas as pd
from datetime import datetime

# 台銀官方 CSV 載點
CSV_URL = "https://rate.bot.com.tw/xrt/flcsv/0/day"

# 帶上瀏覽器 User-Agent 確保能成功下載
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

print("📥 正在從台銀下載 CSV 檔案...")
response = requests.get(CSV_URL, headers=headers)

# 1. 直接把 CSV 寫入本地檔案
with open("bot_today_rates.csv", "wb") as f:
    f.write(response.content)

print("✅ CSV 下載完成，已存為 bot_today_rates.csv！\n")

# 2. 用 Pandas 讀取剛下載好的 CSV 檔
df = pd.read_csv("bot_today_rates.csv")

# 3. 快速篩選我們要的 USD, GBP, EUR
target_currencies = ['USD', 'GBP', 'EUR']
today_date = datetime.now().strftime('%Y-%m-%d')
fetched_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

clean_data = []

for _, row in df.iterrows():
    currency_code = str(row.iloc[0]).strip()
    for target in target_currencies:
        if target in currency_code:
            clean_data.append({
                'Date': today_date,
                'Currency': target,
                'Buy_Rate': float(row.iloc[12]),   # 本行即期買入
                'Sell_Rate': float(row.iloc[13]),  # 本行即期賣出
                'Fetched_At': fetched_time
            })

df_clean = pd.DataFrame(clean_data)
print("📊 整理後的最終匯率數據：")
print(df_clean)