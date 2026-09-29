import requests

url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

res = requests.get(url, headers=headers, timeout=10)
print("HTTP 狀態碼:", res.status_code) # 看到 200 代表連線成功！
print(res.text[:300])                  # 印出前 300 個字元確認有內容