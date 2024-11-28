# Python 專案集合說明文件

本專案包含三個主要的 Python 腳本，各自具有不同的功能和應用場景。

## 目錄
1. [蝴蝶效應視覺化 (Butterfly_effect.py)](#蝴蝶效應視覺化)
2. [文件加密工具 (denial-of-access-attack.py)](#文件加密工具)
3. [學校資料爬蟲 (openID_spider.py)](#學校資料爬蟲)

## 依賴套件安裝

本專案使用 requirements.txt 管理所有依賴套件。執行以下指令即可安裝所有必要的套件：

```bash
pip install -r requirements.txt
```

注意：若使用 Chrome 瀏覽器進行爬蟲，需要額外安裝與瀏覽器版本相對應的 ChromeDriver。

## 蝴蝶效應視覺化

### 概述
`Butterfly_effect.py` 實現了洛倫茲系統（Lorenz system）的視覺化，展示了混沌理論中著名的蝴蝶效應。該程式創建了一個 3D 動畫，顯示略微不同初始條件下系統的演化過程。

### 核心數學原理
洛倫茲系統由以下三個耦合的常微分方程組成：

$$
\begin{cases}
\frac{dx}{dt} = \sigma(y-x) \\
\frac{dy}{dt} = x(\rho-z) - y \\
\frac{dz}{dt} = xy - \beta z
\end{cases}
$$

其中：
- $$\sigma$$（程式中的 p）= 10.0
- $$\rho$$（程式中的 r）= 28.0
- $$\beta$$（程式中的 b）= 3.0

### 使用方法
```bash
python Butterfly_effect.py
```

執行後會顯示一個互動式 3D 動畫，展示多個軌跡的演化過程。

### 特點
- 3D 視覺化展示
- 動態旋轉視角
- 多軌跡同時顯示
- 時間進度顯示

## 文件加密工具

### 概述
`denial-of-access-attack.py` 提供了一個簡單的文件加密系統，使用改良的凱薩密碼（Caesar Cipher）對文件進行加密。

### 主要功能
- 遞迴處理目錄中的所有文件
- 使用自定義位移量進行加密
- 支援 UTF-8 編碼
- 保留原始文件擴展名

### 使用方法
```bash
python denial-of-access-attack.py
```

執行後根據提示輸入：
1. 目標目錄路徑
2. 加密位移量（默認為 3）

### 安全注意事項
⚠️ 請注意：此工具僅供學習和研究使用，不建議用於實際的資料加密需求。

## 學校資料爬蟲

### 概述
`openID_spider.py` 是一個自動化的網頁爬蟲工具，專門用於抓取學校相關資料。

### 主要功能
- 自動化瀏覽器操作
- 分年級、班級數據抓取
- 錯誤重試機制
- CSV 格式數據導出

### 使用方法
```bash
python openID_spider.py
```

### 配置說明
可在程式中修改以下默認值：
```python
default_values = {
    "district": "802",    # 預設區域
    "school": "wfjh",     # 預設學校
    "grade": "8",         # 預設年級
    "silent": True        # 是否靜默模式
}
```

### 注意事項
- 需要確保 Chrome 瀏覽器和 ChromeDriver 版本相符
- 建議在穩定的網路環境下運行
- 遵守網站使用規範和爬蟲禮儀

## 系統需求
- Python 3.7+
- Chrome 瀏覽器（用於爬蟲）
- 足夠的系統記憶體（建議 4GB 以上）
- 支援 3D 加速的顯示卡（用於蝴蝶效應視覺化）

## 授權說明
本專案僅供教育和研究目的使用，請勿用於商業或非法用途。

## 貢獻指南
歡迎提交 Issue 和 Pull Request 來改進專案。在提交之前，請確保：
1. 代碼符合 PEP 8 規範
2. 添加適當的註釋和文檔
3. 通過所有現有的測試用例