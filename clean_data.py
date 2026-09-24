import pandas as pd
import os

def clean_online_retail(file_path):
    print("正在載入原始資料集...")
    
    # 根據檔案格式讀取 (支援 csv 或 xlsx)
    if file_path.endswith('.csv'):
        # 部分 Kaggle CSV 編碼可能是 latin1 或 ISO-8859-1
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin1')
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("不支援的檔案格式，請提供 .csv 或 .xlsx 檔案")

    initial_rows = len(df)
    print(f"原始資料筆數：{initial_rows:,} 筆")

    # 欄位名稱標準化 (去除前後空白)
    df.columns = df.columns.str.strip()

    # 1. 剔除 Customer ID 為空的無名氏交易 (RFM 分析必要條件)
    # 相容欄位名稱 Customer ID 或 CustomerID
    cust_col = 'Customer ID' if 'Customer ID' in df.columns else 'CustomerID'
    df_clean = df.dropna(subset=[cust_col]).copy()
    
    # 確保 Customer ID 為整數格式
    df_clean[cust_col] = df_clean[cust_col].astype(int)

    # 2. 過濾退貨與無效交易
    # InvoiceNo/Invoice 開頭為 'C' 代表 Cancellation，且 Quantity > 0、UnitPrice/Price > 0
    inv_col = 'Invoice' if 'Invoice' in df.columns else 'InvoiceNo'
    price_col = 'Price' if 'Price' in df.columns else 'UnitPrice'
    
    df_clean[inv_col] = df_clean[inv_col].astype(str)
    
    df_clean = df_clean[
        (~df_clean[inv_col].str.startswith('C', na=False)) &
        (df_clean['Quantity'] > 0) &
        (df_clean[price_col] > 0)
    ]

    # 3. 計算每筆明細交易總金額 TotalPrice
    df_clean['TotalPrice'] = df_clean['Quantity'] * df_clean[price_col]

    clean_rows = len(df_clean)
    removed_rows = initial_rows - clean_rows
    print(f"清洗完畢！保留資料筆數：{clean_rows:,} 筆 (已過濾 {removed_rows:,} 筆髒資料/退貨)")

    # 4. 匯出乾淨的 CSV 檔給 Power BI / SQL 使用
    output_filename = "Online_Retail_Clean.csv"
    df_clean.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"已成功匯出清洗後的檔案：{output_filename}")

if __name__ == "__main__":
    # 請確保檔名與你下載的 CSV 檔名一致
    input_file = "Online_Retail.csv" 
    
    if os.path.exists(input_file):
        clean_online_retail(input_file)
    else:
        print(f"錯誤：找不到 {input_file}，請確認檔案已放進目前的專案目錄中！")