# Python 興趣專案合輯

這個專案集合展示了資安、數據視覺化與網站開發的應用。

## 專案清單

### 1. OpenID 爬蟲與密碼破解工具

資安測試工具集，包含兩個主要組件：

#### OpenID 爬蟲 (openID_spider.py)
- 自動化抓取學校 OpenID 帳號資訊
- 多線程處理與錯誤重試機制
- 支援自定義區域、學校、年級設定
- CSV 格式輸出結果

#### 彩虹表破解工具 (RainbowCrack.py)
- 圖形化介面的密碼破解工具
- 支援多種破解模式：
  - 36進制6位破解
  - 常用連續字母破解
  - 大/小寫開頭破解
  - 弱口令字典破解
- 多線程並行處理
- 即時進度與統計顯示

### 2. 蝴蝶效應 - 混沌理論視覺化 (Butterfly_effect.py)

混沌理論的互動式3D視覺化：
- Lorenz系統動態模擬
- 多軌跡比較展示
- 即時參數調整
- 動畫化呈現蝴蝶效應

技術特點：
- 使用 NumPy 進行數值計算
- Matplotlib 3D 動畫渲染
- 支援多個初始條件的同時模擬

### 3. 羅盤教育平台 (how_to_codeing.html)

教育改革導向的網站專案：
- 以重新定義東方教育為目標
- 提供全面的學習資源庫
- 著重創新思維培養
- 整合現代教育技術

技術框架：
- 響應式網頁設計
- 現代化UI/UX界面
- CSS Flexbox佈局
- 互動式組件設計

## 系統需求
- Python 3.8+
- 相關套件：
  - selenium
  - numpy
  - matplotlib
  - tkinter
  - beautifulsoup4
  - requests

## 安裝方式
```bash
pip install -r requirements.txt
```

## 授權條款
MIT License

## 參與貢獻
歡迎提交Issue與PR，請遵循開發規範。

## 聯絡方式

Email
- hello.lwopan@gmail.com
- S0618231@go.edu.tw
- yes.hsiao@gmail.com