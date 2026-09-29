import yfinance as yf
import pandas as pd
from datetime import datetime

def fetch_exchange_rates():
    """
    從 Yahoo Finance API 擷取最新外幣對台幣 (TWD) 的匯率數據
    """
    # 1. 設定要監控的貨幣對 (yfinance 的代碼格式)
    currency_pairs = {
        'USDTWD=X': 'USD',  # 美元 / 新台幣
        'GBPTWD=X': 'GBP',  # 英鎊 / 新台幣
        'EURTWD=X': 'EUR',  # 歐元 / 新台幣
        'JPYTWD=X': 'JPY'   # 日圓 / 新台幣
    }

    # 取得當前時間戳記
    today_date = datetime.now().strftime('%Y-%m-%d')
    fetched_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    clean_rows = []

    print("🚀 [ETL-Extract] 正在從 Yahoo Finance 抓取即時匯率數據...")

    for symbol, currency in currency_pairs.items():
        try:
            ticker = yf.Ticker(symbol)
            # 抓取最近 5 天資料，避免遇到週末或連假時 1d 回傳空值
            df_hist = ticker.history(period="5d")
            
            if not df_hist.empty:
                # 取得最新一個交易日的收盤價
                latest_rate = float(df_hist['Close'].iloc[-1])
                rate_date = df_hist.index[-1].strftime('%Y-%m-%d')
                
                clean_rows.append({
                    'Date': rate_date,            # 交易日期
                    'Currency': currency,          # 幣別 (USD, GBP, EUR...)
                    'Buy_Rate': round(latest_rate, 4),  # 即時匯率 (四捨五入至小數點第 4 位)
                    'Sell_Rate': round(latest_rate, 4), # API 均價視為基準匯率
                    'Fetched_At': fetched_time     # 爬取時間戳記
                })
                print(f"  ✓ {currency}/TWD 匯率: {latest_rate:.4f} (資料日期: {rate_date})")
            else:
                print(f"  ⚠️ 無法取得 {currency} 的歷史數據")

        except Exception as e:
            print(f"  ❌ 抓取 {currency} 失敗: {e}")

    # 2. 轉為 Pandas DataFrame
    df_clean = pd.DataFrame(clean_rows)
    return df_clean


if __name__ == "__main__":
    # 執行數據抓取與清洗
    df_rates = fetch_exchange_rates()
    
    print("\n📊 [ETL-Transform] 清洗後的結構化匯率數據：")
    print("=" * 60)
    print(df_rates.to_string(index=False))
    print("=" * 60)
    
    # 備份為本地 CSV 檔案 (增量寫入時可做為 Log 使用)
    csv_file = "exchange_rates_history.csv"
    
    # 若檔案不存在則寫入 Header，若存在則 append
    try:
        df_rates.to_csv(csv_file, mode='a', index=False, header=not pd.io.common.file_exists(csv_file), encoding='utf-8-sig')
        print(f"\n💾 [ETL-Load] 數據已成功追加備份至本地檔: {csv_file}")
    except Exception as e:
        print(f"\n❌ 寫入 CSV 失敗: {e}")