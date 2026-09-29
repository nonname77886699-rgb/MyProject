import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# ==========================================
# 1. 全域配置設定
# ==========================================
CSV_FILE = "exchange_rates_history.csv"

# MariaDB / MySQL 資料庫設定 (請依個人環境調整密碼與 DB 名稱)
DB_USER = "root"
DB_PASS = "your_password"  # 👈 記得改成你的 MariaDB 密碼
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "ecommerce_db"    # 👈 請確認 MariaDB 中已有此 Database

DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ==========================================
# 2. 爬蟲與 ETL 核心邏輯
# ==========================================
def fetch_exchange_rates():
    """
    發送 HTTP 請求並解析台灣銀行牌告匯率
    """
    url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    rows = soup.select('table tbody tr')
    today_date = datetime.now().strftime('%Y-%m-%d')
    fetched_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    target_currencies = ['USD', 'GBP', 'EUR']
    extracted_data = []
    
    for row in rows:
        currency_tag = row.select_one('.visible-phone')
        if currency_tag:
            currency_code = currency_tag.text.strip().replace('(', '').replace(')', '')
            for target in target_currencies:
                if target in currency_code:
                    buy_rate = float(row.select('td')[2].text.strip())   # 即期買入
                    sell_rate = float(row.select('td')[3].text.strip())  # 即期賣出
                    
                    extracted_data.append({
                        'Date': today_date,
                        'Currency': target,
                        'Buy_Rate': buy_rate,
                        'Sell_Rate': sell_rate,
                        'Fetched_At': fetched_time
                    })
                    
    return pd.DataFrame(extracted_data)

# ==========================================
# 3. 持久化儲存：CSV 追加與去重
# ==========================================
def save_to_csv(new_df):
    """
    將資料增量寫入 CSV，並依 (Date, Currency) 自動去重
    """
    if os.path.exists(CSV_FILE):
        old_df = pd.read_csv(CSV_FILE)
        combined_df = pd.concat([old_df, new_df], ignore_index=True)
        # 去重機制：若當天已抓過，保留最新抓到的那筆
        combined_df.drop_duplicates(subset=['Date', 'Currency'], keep='last', inplace=True)
    else:
        combined_df = new_df
        
    combined_df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
    print(f"💾 [CSV] 資料已成功增量寫入至 {CSV_FILE}")

# ==========================================
# 4. 持久化儲存：MariaDB / MySQL 寫入
# ==========================================
def save_to_db(new_df):
    """
    將資料寫入 MariaDB / MySQL 資料庫，自動建表並處理主鍵限制
    """
    try:
        engine = create_engine(DB_URL)
        
        # 建立資料表 (使用 Date + Currency 複合主鍵防止重複)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS exchange_rates_history (
            Date DATE,
            Currency VARCHAR(10),
            Buy_Rate DECIMAL(10, 4),
            Sell_Rate DECIMAL(10, 4),
            Fetched_At DATETIME,
            PRIMARY KEY (Date, Currency)
        );
        """
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            
        # 寫入資料庫
        new_df.to_sql(name='exchange_rates_history', con=engine, if_exists='append', index=False)
        print("🗄️  [SQL] 資料已成功寫入 MariaDB / MySQL 資料庫！")
        
    except Exception as e:
        print(f"⚠️ [SQL] 寫入資料庫未執行或跳過 (若主鍵重複則屬正常狀況): {e}")

# ==========================================
# 主程式入口
# ==========================================
if __name__ == "__main__":
    print("🚀 開始執行匯率爬蟲與 ETL 流水線...")
    try:
        df = fetch_exchange_rates()
        print("✅ 成功抓取最新市場匯率：")
        print(df)
        
        # 1. 儲存至本地 CSV
        save_to_csv(df)
        
        # 2. 儲存至 MariaDB/MySQL (選用，若資料庫未啟動亦不影響 CSV 生成)
        save_to_db(df)
        
        print("\n🎉 ETL 任務順利完成！")
    except Exception as e:
        print(f"❌ 腳本執行過程發生錯誤: {e}")