# 美食推薦小幫手

一個基於Django的智能美食推薦系統，結合AI和地理位置服務，提供個性化餐廳推薦。

## 核心功能

- **智能聊天推薦**：基於自然語言處理，理解用戶需求並推薦餐廳
- **地理位置感知**：支援定位和基於城市、區域的搜索功能
- **價格篩選**：可根據"平價"($$及以下)、"高級"等價格描述準確推薦餐廳
- **餐廳卡片展示**：顯示餐廳評分、價格、照片、營業時間等完整信息
- **顧客評價摘要**：展示用戶評論，幫助快速了解餐廳特色
- **一鍵導航**：內建地圖查看和導航功能，方便用戶前往餐廳

## 技術架構

- **後端**：Python Django框架
- **前端**：HTML, CSS, JavaScript, Bootstrap 5
- **數據庫**：SQLite (開發環境)
- **API集成**：
  - Google Places API：餐廳搜索和詳細信息獲取
  - Google Search API：網頁信息檢索
  - OpenAI GPT API：自然語言理解和回應生成

## 特色亮點

- **台灣地區精確定位**：內建台灣縣市鄉鎮區經緯度數據，精確處理台灣各地區搜索請求
- **價格智能映射**：準確理解"平價"、"高級"等描述詞並對應至適當價格級別
- **響應式設計**：適配桌面和移動設備的現代化UI
- **豐富的餐廳資訊**：包含評分、評論、照片、營業時間和聯絡方式等全方位信息
- **簡潔回應格式**：AI回應精準簡潔，突出重要信息

## 系統需求

- Python 3.8+
- Django 4.0+
- 必要的API金鑰：
  - Google Places API
  - Google Search API (選用)
  - OpenAI API (選用)

## 安裝與設置

1. 克隆存儲庫：

```bash
git clone https://github.com/yourusername/food_recommend.git
cd food_recommend
```

2. 創建虛擬環境並激活：

```bash
python -m venv venv
source venv/bin/activate  # 在Linux/Mac上
venv\Scripts\activate  # 在Windows上
```

3. 安裝依賴：

```bash
pip install -r requirements.txt
```

4. 設置環境變數（API金鑰）：

```bash
# Linux/Mac
export GOOGLE_PLACES_API_KEY="your_key_here"
export GOOGLE_SEARCH_API_KEY="your_key_here"
export GOOGLE_CX_ID="your_cx_id_here"
export GPT_API_KEY="your_openai_key_here"

# Windows
set GOOGLE_PLACES_API_KEY=your_key_here
set GOOGLE_SEARCH_API_KEY=your_key_here
set GOOGLE_CX_ID=your_cx_id_here
set GPT_API_KEY=your_openai_key_here
```

5. 運行數據庫遷移：

```bash
python manage.py makemigrations
python manage.py migrate
```

6. 創建超級用戶（可選）：

```bash
python manage.py createsuperuser
```

7. 啟動開發服務器：

```bash
python manage.py runserver
```

應用將在 http://127.0.0.1:8000/ 上運行。

## 項目結構

- `food_recommend/`: 主要Django項目設置
- `chat/`: 聊天和美食推薦功能核心應用
  - `food_tools.py`: API工具類，處理與外部服務的交互
  - `food_controller.py`: 控制層，協調用戶查詢處理和回應生成
- `user/`: 用戶管理和個人資料功能
- `templates/`: HTML模板文件
  - `chat/chat_room.html`: 聊天界面模板
- `static/`: 靜態文件
  - `json/town.json`: 台灣縣市鄉鎮區地理數據
  - `images/`: 圖片資源

## 使用指南

1. 註冊/登入系統
2. 進入聊天室與美食推薦助手互動
3. 詢問特定地區、類型或價格的餐廳推薦
   - 示例：「推薦基隆的平價燒烤店」
   - 示例：「台北市有什麼好吃的日本料理？」
4. 查看餐廳推薦卡片，獲取詳細信息
5. 點擊「查看地圖」或「導航前往」前往餐廳

## 目前支援的查詢類型

- 地區餐廳查詢：「高雄有什麼好吃的？」
- 特定料理類型：「推薦台中的義式餐廳」
- 價格範圍篩選：「平價的台南小吃」、「台北高級日料」
- 混合查詢：「台中西區有沒有平價的韓式烤肉？」

## 未來計劃

- 擴展餐廳標籤系統，支援更多特色標籤
- 增加餐廳收藏和歷史記錄功能
- 添加用戶自定義偏好設置
- 實現社交分享功能
- 增加餐廳預訂功能

## 貢獻

歡迎貢獻！請隨時提交問題或拉取請求。 