Markdown
# 電商交易事實分析與營運風險診斷 (E-Commerce Sales Analytics)

## 📌 專案簡介 (Overview)
本專案基於 Online Retail II 數據庫，透過 Python 進行 ETL 資料清理，並建構維度模型（Star Schema）。旨在使用客觀交易事實提取商業洞察，診斷產品結構與地理市場集中度風險，並提出營運優化策略。

---

## 🛠️ 技術棧 (Tech Stack)
- **Data Processing & ETL:** Python (Pandas, uv)
- **Data Modeling & Visualization:** Power BI, DAX, Star Schema
- **Version Control:** Git, GitHub

---

## 📊 核心商業事實與診斷 (Key Insights & Diagnosis)

### 1. 產品銷售結構事實
- **客觀事實：** 銷量 Top 1 之爆款商品單價極低，總營收高度依賴薄利多銷型商品帶動。
- **隱患診斷：** 倉儲與物流資源消耗大，但單筆訂單獲利貢獻有限。

### 2. 地理市場集中度事實
- **客觀事實：** 英國 (United Kingdom) 本地市場貢獻逾 85% 以上總營收，海外市場呈零星分散。
- **隱患診斷：** 過度依賴單一地理市場，抗風險能力較弱。

---

## 💡 營運優化策略建議 (Actionable Strategies)
1. **組合包 (Bundling) 策略：** 針對高頻低單價爆款推出搭配高毛利商品的捆綁方案，提升單筆客單價 (AOV)。
2. **客戶留存機制：** 導入 RFM 客戶分群，針對高潛力回購顧客進行精準再行銷，提升顧客 lifetime value (LTV)。

---

## 🖼️ 儀表板預覽 (Dashboard Preview)
*(完成 Power BI 報表後，在此處貼上視覺化截圖)*
Markdown
![地區銷售排名](first.png)
![產品銷售散佈圖](test2.png)
