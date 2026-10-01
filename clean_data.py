import os
import pandas as pd

def clean_online_retail():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    input_file = os.path.join(DATA_DIR, "Online_Retail.csv")
    output_file = os.path.join(DATA_DIR, "Online_Retail_Clean.csv")

    if not os.path.exists(input_file):
        print(f"❌ 錯誤：找不到輸入檔案 {input_file}，請確認檔案已放置於 data/ 目錄中！")
        return

    print("🚀 正在載入原始資料集...")

    try:
        df = pd.read_csv(input_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(input_file, encoding='ISO-8859-1')

    initial_rows = len(df)
    print(f"📊 原始資料筆數：{initial_rows:,} 筆")

    # -------------------------------------------------------------
    # 欄位標準化對照表 (消除 StockCode, UnitPrice 等無底線命名差異)
    # -------------------------------------------------------------
    column_mapping = {
        'invoiceno': 'invoice_no',
        'invoice': 'invoice_no',
        'stockcode': 'stock_code',
        'description': 'description',
        'quantity': 'quantity',
        'invoicedate': 'invoice_date',
        'unitprice': 'unit_price',
        'price': 'unit_price',
        'customerid': 'customer_id',
        'country': 'country'
    }

    # 先轉小寫並去除底線與空白，再進行統一映射
    new_cols = {}
    for col in df.columns:
        clean_key = col.strip().lower().replace('_', '').replace(' ', '')
        new_cols[col] = column_mapping.get(clean_key, col.strip().lower())
    
    df = df.rename(columns=new_cols)

    # 4. 剔除 Customer ID 為空的無名氏交易
    df_clean = df.dropna(subset=['customer_id']).copy()
    df_clean['customer_id'] = df_clean['customer_id'].astype(int)

    # 5. 過濾退貨 (C 開頭) 與無效金額/數量
    df_clean['invoice_no'] = df_clean['invoice_no'].astype(str)
    df_clean = df_clean[
        (~df_clean['invoice_no'].str.startswith('C', na=False)) &
        (df_clean['quantity'] > 0) &
        (df_clean['unit_price'] > 0)
    ]

    # 6. 字串與日期格式轉換
    df_clean['stock_code'] = df_clean['stock_code'].astype(str).str.strip()
    if 'description' in df_clean.columns:
        df_clean['description'] = df_clean['description'].astype(str).str.strip()
        
    df_clean['invoice_date'] = pd.to_datetime(df_clean['invoice_date'], errors='coerce')

    # 7. 計算交易總金額 TotalPrice (保留 2 位小數)
    df_clean['total_price'] = (df_clean['quantity'] * df_clean['unit_price']).round(2)

    clean_rows = len(df_clean)
    removed_rows = initial_rows - clean_rows
    print(f"✅ 清洗完畢！保留筆數：{clean_rows:,} 筆 (已過濾 {removed_rows:,} 筆無效/退貨資料)")

    # 8. 匯出乾淨資料至 data/Online_Retail_Clean.csv
    df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"🎉 已成功匯出檔案至：{output_file}")

if __name__ == "__main__":
    clean_online_retail()