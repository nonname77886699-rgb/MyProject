import requests
from bs4 import BeautifulSoup

url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"

# 完整真實瀏覽器 Headers 標頭
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1'
}

# 使用 Session 保持連線狀態
session = requests.Session()
res = session.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(res.text, 'html.parser')

# 直接抓取所有資料列
rows = soup.find_all('tr')

print(f"網頁內容總長度: {len(res.text)} 字元")

# 檢查是否依然拿到驗證頁面
if "Challenge Validation" in res.text:
    print("⚠️ 依然被防火牆攔截，嘗試備用方案...")
else:
    count = 0
    for row in rows:
        currency_tag = row.select_one('.visible-phone')
        tds = row.select('td')
        
        if currency_tag and len(tds) >= 4:
            currency = currency_tag.text.strip().replace('(', '').replace(')', '')
            buy_rate = tds[2].text.strip()   # 即期買入
            sell_rate = tds[3].text.strip()  # 即期賣出
            
            count += 1
            print(f"[{count}] 幣別: {currency:<10} | 即期買入: {buy_rate:<8} | 即期賣出: {sell_rate:<8}")
            
            if count >= 5:
                break