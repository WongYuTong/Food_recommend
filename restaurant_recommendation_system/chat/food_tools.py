import requests
import os
import json
from typing import List, Dict, Any, Optional

# API 密鑰設置
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
GOOGLE_SEARCH_API_KEY = os.environ.get("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_CX_ID = os.environ.get("GOOGLE_CX_ID", "")
GPT_API_KEY = os.environ.get("GPT_API_KEY", "")

class GooglePlacesAPI:
    """Google Places API 工具類"""
    
    def __init__(self, api_key: str = GOOGLE_PLACES_API_KEY):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def search_nearby(self, 
                      location: str, 
                      keyword: str = None, 
                      radius: int = 2000, 
                      type: str = "restaurant", 
                      price_level: Optional[int] = None,
                      latitude: float = None,
                      longitude: float = None) -> Dict[str, Any]:
        """
        搜尋指定位置附近的餐廳
        
        參數:
            location: 搜尋地點 (例如: "台中市一中街")，如果提供latitude和longitude則可為空
            keyword: 搜尋關鍵字 (例如: "日式料理")
            radius: 搜尋半徑 (單位: 米)
            type: 地點類型 (預設: "restaurant")
            price_level: 價格等級 (0-4，4最貴，None表示不限)
            latitude: 緯度座標 (如果直接提供座標則優先使用)
            longitude: 經度座標 (如果直接提供座標則優先使用)
        
        返回:
            包含餐廳資料的字典
        """
        try:
            # 檢查API密鑰是否設置
            if not self.api_key or self.api_key == "":
                print("Error: Google Places API key not set")
                return {"status": "ERROR", "error_message": "API key not configured", "results": []}
                
            # 如果提供了經緯度座標，直接使用
            if latitude is not None and longitude is not None:
                # 搜尋附近餐廳
                nearby_url = f"{self.base_url}/nearbysearch/json"
                nearby_params = {
                    "location": f"{latitude},{longitude}",
                    "radius": radius,
                    "type": type,
                    "key": self.api_key,
                    "language": "zh-TW"  # 設置返回結果為繁體中文
                }
                
                if keyword:
                    nearby_params["keyword"] = keyword
                
                # 處理價格等級 - 如果是"平價"（2或以下），則設置maxprice
                if price_level is not None:
                    if price_level <= 2:  # 平價範圍 ($$及以下)
                        nearby_params["maxprice"] = price_level
                        print(f"搜尋平價餐廳: 最高價格等級設為 {price_level} ($$及以下)")
                    else:  # 高級範圍
                        nearby_params["minprice"] = price_level - 1
                        nearby_params["maxprice"] = price_level
                        print(f"搜尋高級餐廳: 價格等級範圍設為 {price_level-1}-{price_level}")
                
                response = requests.get(nearby_url, params=nearby_params, timeout=10)
                return response.json()
                
            # 如果未提供經緯度，需要從location中獲取
            # 首先嘗試從靜態JSON文件中查找位置信息
            location_found = False
            lat, lng = None, None
            
            if location:
                # 標準化處理地點名稱 (統一處理「臺」和「台」)
                location_normalized = location.replace('台', '臺') if '台' in location else location
                
                # 嘗試從靜態文件讀取地理位置數據
                try:
                    import os
                    import json
                    
                    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                           'static', 'json', 'town.json')
                    
                    if os.path.exists(json_path):
                        with open(json_path, 'r', encoding='utf-8') as f:
                            towns_data = json.load(f)
                        
                        print(f"正在從位置數據庫中尋找位置: {location}")
                        
                        # 先嘗試精確匹配完整地名
                        for town in towns_data:
                            full_name = f"{town['CountyName']}{town['TownName']}"
                            
                            if location_normalized in full_name or full_name in location_normalized:
                                lat = town['latitude']
                                lng = town['longitude']
                                location_found = True
                                print(f"找到精確位置: {full_name}, 座標: {lat}, {lng}")
                                break
                        
                        # 如果精確匹配失敗，嘗試匹配縣市名稱
                        if not location_found:
                            for town in towns_data:
                                county_name = town['CountyName']
                                town_name = town['TownName']
                                
                                # 檢查縣市名稱是否在查詢中，或查詢是否在縣市名稱中
                                if county_name in location_normalized or location_normalized in county_name:
                                    # 對於縣市匹配，優先使用縣市中心（通常是XXX市或第一個行政區）
                                    if town_name in ['中正區', '中區', '中山區'] or '市' in town_name:
                                        lat = town['latitude']
                                        lng = town['longitude']
                                        location_found = True
                                        print(f"找到縣市中心位置: {county_name}{town_name}, 座標: {lat}, {lng}")
                                        break
                            
                            # 如果仍未找到，使用第一個匹配縣市名的資料
                            if not location_found:
                                for town in towns_data:
                                    county_name = town['CountyName']
                                    
                                    if county_name in location_normalized or location_normalized in county_name:
                                        lat = town['latitude']
                                        lng = town['longitude']
                                        location_found = True
                                        print(f"找到縣市位置: {county_name}, 座標: {lat}, {lng}")
                                        break
                    else:
                        print(f"位置數據文件不存在: {json_path}")
                except Exception as e:
                    print(f"從靜態文件讀取位置數據時出錯: {str(e)}")
            
            # 如果從靜態文件中未找到位置，使用Google地理編碼API
            if not location_found:
                print(f"嘗試使用Google地理編碼API查詢位置: {location}")
                geocode_url = f"{self.base_url}/findplacefromtext/json"
                geocode_params = {
                    "input": location,
                    "inputtype": "textquery",
                    "fields": "geometry",
                    "key": self.api_key,
                    "language": "zh-TW"  # 設置返回結果為繁體中文
                }
                
                response = requests.get(geocode_url, params=geocode_params, timeout=10)
                result = response.json()
                
                if result.get("status") != "OK" or not result.get("candidates"):
                    error_msg = f"無法找到位置: {location}"
                    print(error_msg)
                    return {"status": "ZERO_RESULTS", "error_message": error_msg, "results": []}
                
                # 獲取座標
                location_data = result["candidates"][0]["geometry"]["location"]
                lat = location_data["lat"]
                lng = location_data["lng"]
                print(f"使用Google API找到位置座標: {lat}, {lng}")
            
            # 搜尋附近餐廳
            nearby_url = f"{self.base_url}/nearbysearch/json"
            nearby_params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": type,
                "key": self.api_key,
                "language": "zh-TW"  # 設置返回結果為繁體中文
            }
            
            if keyword:
                nearby_params["keyword"] = keyword
            
            # 處理價格等級 - 如果是"平價"（2或以下），則設置maxprice
            if price_level is not None:
                if price_level <= 2:  # 平價範圍 ($$及以下)
                    nearby_params["maxprice"] = price_level
                    print(f"搜尋平價餐廳: 最高價格等級設為 {price_level} ($$及以下)")
                else:  # 高級範圍
                    nearby_params["minprice"] = price_level - 1
                    nearby_params["maxprice"] = price_level
                    print(f"搜尋高級餐廳: 價格等級範圍設為 {price_level-1}-{price_level}")
            
            print(f"搜索參數: {nearby_params}")
            response = requests.get(nearby_url, params=nearby_params, timeout=10)
            
            # 檢查響應
            result = response.json()
            print(f"搜索結果狀態: {result.get('status')}, 找到結果數量: {len(result.get('results', []))}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API請求錯誤: {str(e)}"
            print(error_msg)
            return {"status": "ERROR", "error_message": error_msg, "results": []}
        except Exception as e:
            error_msg = f"搜尋附近餐廳時發生未知錯誤: {str(e)}"
            print(error_msg)
            return {"status": "ERROR", "error_message": error_msg, "results": []}
    
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        獲取特定地點的詳細資訊
        
        參數:
            place_id: Google Places API 的地點ID
            
        返回:
            包含地點詳細資訊的字典
        """
        details_url = f"{self.base_url}/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,rating,formatted_address,formatted_phone_number,opening_hours,price_level,review,website,photos,user_ratings_total,business_status,url,types,geometry",
            "key": self.api_key,
            "language": "zh-TW"  # 設置返回結果為繁體中文
        }
        
        response = requests.get(details_url, params=params)
        result = response.json()
        
        # 保留照片信息，但不再直接生成照片URL
        # 这个工作将交给Controller层或代理视图来处理
        
        # 如果成功获取信息，增加一些辅助字段
        if result.get("status") == "OK" and result.get("result"):
            try:
                # 提取并格式化一些字段，方便后续使用
                place_result = result["result"]
                
                # 1. 格式化营业状态
                if place_result.get("business_status") == "OPERATIONAL":
                    place_result["business_status_text"] = "營業中"
                elif place_result.get("business_status") == "CLOSED_TEMPORARILY":
                    place_result["business_status_text"] = "暫時休業"
                elif place_result.get("business_status") == "CLOSED_PERMANENTLY":
                    place_result["business_status_text"] = "永久停業"
                else:
                    place_result["business_status_text"] = "狀態未知"
                
                # 2. 格式化价格级别
                if place_result.get("price_level") is not None:
                    place_result["price_level_text"] = "$" * (place_result["price_level"] + 1)
                
                # 3. 提取餐厅类型
                if place_result.get("types"):
                    place_result["cuisine_type"] = ", ".join(place_result["types"][:3])
                
                print(f"成功获取餐厅详情: {place_result.get('name')}")
            except Exception as e:
                print(f"处理餐厅详情时出错: {str(e)}")
        
        return result
    
    def get_photo_url(self, photo_reference: str, max_width: int = 800) -> str:
        """
        獲取照片URL
        
        參數:
            photo_reference: 照片參考ID
            max_width: 照片最大寬度
            
        返回:
            照片URL
        """
        # 直接返回Google Places API的照片URL
        # 這個URL可以直接在<img>標籤中使用
        return f"{self.base_url}/photo?maxwidth={max_width}&photoreference={photo_reference}&key={self.api_key}"
    
    def get_photo_data(self, photo_reference: str, max_width: int = 800) -> Optional[bytes]:
        """
        直接獲取照片二進制數據
        
        參數:
            photo_reference: 照片參考ID
            max_width: 照片最大寬度
            
        返回:
            照片二進制數據，失敗時返回None
        """
        try:
            # 檢查API密鑰是否設置
            if not self.api_key or self.api_key == "":
                print("错误：Google Places API密钥未设置")
                return None
                
            # 構建照片URL
            photo_url = self.get_photo_url(photo_reference, max_width)
            print(f"尝试获取照片: {photo_url[:70]}...")  # 仅打印URL的一部分，避免泄露完整API密钥
            
            # 設定請求頭和參數
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            
            # 發送請求獲取照片
            response = requests.get(photo_url, headers=headers, timeout=10)
            
            # 檢查請求是否成功
            if response.status_code == 200:
                print(f"成功获取照片，大小: {len(response.content)} 字节")
                return response.content
            else:
                print(f"獲取照片失敗，狀態碼: {response.status_code}, 响应: {response.text[:100]}")
                return None
        except requests.exceptions.Timeout:
            print(f"获取照片超时")
            return None
        except requests.exceptions.ConnectionError:
            print(f"获取照片连接错误")
            return None
        except Exception as e:
            print(f"獲取照片數據時出錯: {str(e)}")
            return None


class GoogleSearchAPI:
    """Google Search API 工具類"""
    
    def __init__(self, api_key: str = GOOGLE_SEARCH_API_KEY, cx_id: str = GOOGLE_CX_ID):
        self.api_key = api_key
        self.cx_id = cx_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query: str, num: int = 5) -> Dict[str, Any]:
        """
        執行 Google 搜尋
        
        參數:
            query: 搜尋查詢字串
            num: 返回結果數量
            
        返回:
            搜尋結果字典
        """
        params = {
            "q": query,
            "key": self.api_key,
            "cx": self.cx_id,
            "num": num,
            "lr": "lang_zh-TW",  # 限制搜尋繁體中文結果
            "hl": "zh-TW"        # 設置界面語言為繁體中文
        }
        
        response = requests.get(self.base_url, params=params)
        return response.json()


class GPTAPI:
    """OpenAI GPT API 工具類"""
    
    def __init__(self, api_key: str = GPT_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """
        獲取 GPT 回應
        
        參數:
            messages: 訊息列表，格式為 [{"role": "user", "content": "你好"}]
            model: 使用的模型名稱
            
        返回:
            GPT 回應字典
        """
        try:
            # 檢查 API 密鑰是否已設置
            if not self.api_key or self.api_key == "":
                print("API 密鑰未設置，使用模擬回應")
                return self._get_mock_response(messages)
            
            data = {
                "model": model,
                "messages": messages
            }
            
            # 嘗試發送請求到 OpenAI API
            try:
                response = requests.post(self.base_url, headers=self.headers, json=data, timeout=30)
                response.raise_for_status()  # 如果狀態碼不是 200，會拋出異常
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"API 請求失敗: {str(e)}")
                return self._get_mock_response(messages)
            
        except Exception as e:
            print(f"獲取 GPT 回應時發生異常: {str(e)}")
            return self._get_mock_response(messages)
        
    def _get_mock_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        當 API 調用失敗時生成模擬回應
        
        參數:
            messages: 訊息列表
            
        返回:
            模擬的 GPT 回應
        """
        # 檢查是否是用戶查詢
        user_message = ""
        system_message = ""
        for message in messages:
            if message.get("role") == "user":
                user_message = message.get("content", "")
            elif message.get("role") == "system":
                system_message = message.get("content", "")
        
        # 檢查是否是查詢分析請求
        if "分析用戶的查詢" in system_message and "JSON" in system_message:
            # 模擬分析查詢的回應
            location = ""
            food_type = ""
            price_level = None
            
            # 簡單提取地點
            locations = ["台北", "台中", "高雄", "信義區", "西門町", "東區", "北投", "士林"]
            for loc in locations:
                if loc in user_message:
                    location = loc
                    break
            
            # 簡單提取食物類型
            food_types = ["日本料理", "韓式", "火鍋", "燒烤", "日式", "義式", "泰式", "法式", "美式", "中式", "西式", "素食"]
            for food in food_types:
                if food in user_message:
                    food_type = food
                    break
            
            # 簡單提取價格等級
            if any(term in user_message for term in ["超便宜", "非常便宜", "便宜到爆", "銅板價"]):
                price_level = 0
            elif any(term in user_message for term in ["便宜", "實惠", "學生價"]):
                price_level = 1
            elif any(term in user_message for term in ["中等", "適中", "普通價位"]):
                price_level = 2
            elif any(term in user_message for term in ["高檔", "昂貴", "高級", "高價"]):
                price_level = 3
            elif any(term in user_message for term in ["頂級", "奢華", "非常高級", "豪華"]):
                price_level = 4
            
            # 特殊處理"平價"
            if "平價" in user_message or "經濟" in user_message:
                price_level = 2
            
            # 生成分析結果
            analysis_result = {
                "tools": ["places_api"],
                "location": location,
                "food_type": food_type,
                "price_level": price_level,
                "query_for_search": "",
                "radius": 2000,
                "keywords": ""
            }
            
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(analysis_result, ensure_ascii=False)
                        }
                    }
                ]
            }
        
        # 根據用戶訊息生成模擬回應
        mock_content = ""
        if "餐廳" in user_message or "推薦" in user_message:
            # 檢查特定類型
            if "燒烤" in user_message:
                if "平價" in user_message or "便宜" in user_message:
                    mock_content = """以下是我推薦的平價燒烤餐廳：

1. 燒肉王 - 平價燒烤店，提供新鮮食材和多種醬料選擇
   地址: 台北市中山區林森北路123號
   評分: 4.3
   價格: $
   狀態: 營業中

2. 烤肉天堂 - 自助式平價燒烤，多種肉品和蔬菜可選
   地址: 台北市信義區松高路45號
   評分: 4.1
   價格: $
   狀態: 營業中

3. 燒烤夜市 - 道地臺式燒烤，價格經濟實惠
   地址: 台北市大安區師大路32號
   評分: 4.2
   價格: $
   狀態: 營業中

這些店家的價格都很平實，食材新鮮，適合朋友聚餐。您有其他特別的需求嗎？"""
                else:
                    mock_content = """以下是我推薦的燒烤餐廳：

1. 炭火燒肉專門店 - 正宗日式燒肉，選用上等肉品
   地址: 台北市信義區松壽路12號
   評分: 4.7
   價格: $$$
   狀態: 營業中

2. 韓式烤肉屋 - 道地韓式烤肉，提供各式小菜
   地址: 台北市中山區林森北路88號
   評分: 4.4
   價格: $$
   狀態: 營業中

3. BBQ花園 - 戶外烤肉體驗，提供精緻食材和專業服務
   地址: 台北市內湖區成功路三段123號
   評分: 4.5
   價格: $$$
   狀態: 營業中

請問這些推薦符合您的需求嗎？或者您有其他特定的偏好？"""
            elif "火鍋" in user_message:
                mock_content = """以下是我推薦的火鍋餐廳：

1. 老四川麻辣鍋 - 正宗川味，麻辣鮮香，食材新鮮多樣。
   地址: 台北市信義區松高路123號
   評分: 4.5
   價格: $$
   狀態: 營業中

2. 涮涮鍋專門店 - 日式風格涮涮鍋，湯頭清淡鮮美。
   地址: 台北市大安區敦化南路245號
   評分: 4.3
   價格: $$
   狀態: 營業中

3. 養生藥膳鍋 - 溫補養生，食材講究，適合全家享用。
   地址: 台北市中山區南京東路56號
   評分: 4.6
   價格: $$$
   狀態: 營業中

請問這些推薦符合您的需求嗎？或者您有其他特定的偏好？"""
            else:
                mock_content = """以下是我推薦的餐廳：

1. 鼎泰豐 - 世界知名的小籠包，皮薄餡多汁。
   地址: 台北市信義區松高路194號
   評分: 4.8
   價格: $$$
   狀態: 營業中

2. 老四川麻辣鍋 - 正宗川味，麻辣鮮香，食材新鮮多樣。
   地址: 台北市信義區松高路123號
   評分: 4.5
   價格: $$
   狀態: 營業中

3. 金蓬萊遵古台菜 - 傳統台灣料理，古早味道，適合家庭聚餐。
   地址: 台北市中山區林森北路
   評分: 4.6
   價格: $$
   狀態: 營業中

請問這些推薦符合您的需求嗎？或者您有其他特定的偏好？"""
        elif "早餐" in user_message:
            mock_content = """早餐推薦：

1. 燒餅油條 - 經典的中式早餐組合
2. 豆漿與蛋餅 - 營養均衡的搭配
3. 飯糰 - 方便攜帶的早餐選擇
4. 蘿蔔糕 - 煎至金黃的外皮特別香脆

這些早餐都很適合忙碌的早晨！"""
        elif "午餐" in user_message or "晚餐" in user_message:
            mock_content = """以下是一些受歡迎的餐點推薦：

1. 紅燒牛肉麵 - 湯頭濃郁，牛肉軟嫩多汁
2. 三杯雞 - 香氣四溢，搭配白飯超下飯
3. 滷肉飯 - 台灣經典小吃，簡單卻美味
4. 清蒸魚 - 鮮美健康的選擇

您喜歡哪種口味的料理？"""
        else:
            mock_content = """感謝您的提問！我是美食推薦小幫手，可以為您推薦各種美食和餐廳。請告訴我您的口味偏好或是您想了解的美食類型，我會給您最適合的推薦。無論是中式、西式、日式料理，或是特定的料理方式，我都很樂意為您提供建議！"""
        
        # 模擬 OpenAI API 回應格式
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": mock_content
                    }
                }
            ]
        }

# 添加用於測試的示例函數
def test_photo_retrieval_process():
    """
    測試整個照片獲取流程並顯示結果
    """
    print("===== 開始測試Google Places API照片獲取功能 =====")
    
    api = GooglePlacesAPI()
    
    # 步驟1: 搜索附近餐廳
    print("\n1. 搜索餐廳:")
    search_result = api.search_nearby("台北市信義區", keyword="日式料理")
    
    if search_result.get("status") != "OK" or not search_result.get("results"):
        print("  找不到餐廳或API密鑰無效")
        return
    
    # 顯示找到的餐廳
    restaurants = search_result.get("results", [])
    print(f"  找到 {len(restaurants)} 家餐廳")
    
    if not restaurants:
        print("  沒有找到餐廳，測試結束")
        return
    
    # 步驟2: 獲取第一家餐廳的詳細資訊
    first_restaurant = restaurants[0]
    restaurant_name = first_restaurant.get("name", "未知餐廳")
    place_id = first_restaurant.get("place_id")
    
    print(f"\n2. 獲取餐廳 '{restaurant_name}' 的詳細資訊:")
    details = api.get_place_details(place_id)
    
    if details.get("status") != "OK":
        print(f"  獲取餐廳詳細資訊失敗: {details.get('status')}")
        return
    
    # 步驟3: 獲取照片URL
    print("\n3. 獲取照片URL:")
    restaurant_details = details.get("result", {})
    photo_url = restaurant_details.get("photo_url", "")
    
    if photo_url:
        print(f"  成功獲取照片URL: {photo_url}")
    else:
        print("  未獲取到照片URL")
        
        # 檢查是否有照片參考但未正確處理
        if restaurant_details.get("photos"):
            print("  檢測到餐廳有照片，但URL處理失敗")
            
            # 嘗試手動獲取照片URL
            try:
                photo_reference = restaurant_details["photos"][0]["photo_reference"]
                manual_photo_url = api.get_photo_url(photo_reference, 800)
                print(f"  手動獲取的照片URL: {manual_photo_url}")
            except Exception as e:
                print(f"  手動獲取照片URL時出錯: {str(e)}")
    
    # 步驟4: 透過LLM整理的資料
    print("\n4. 整理後的餐廳推薦格式:")
    formatted_restaurant = f"""1. {restaurant_name} - 日式料理
   地址: {restaurant_details.get('formatted_address', '地址未知')}
   評分: {restaurant_details.get('rating', '評分未知')}
   價格: {"$" * (restaurant_details.get('price_level', 0) + 1) if restaurant_details.get('price_level') is not None else '價格未知'}
   狀態: {"營業中" if restaurant_details.get('opening_hours', {}).get('open_now') else "已休息"}
   照片: {photo_url}
    """
    print(formatted_restaurant)
    
    print("===== 測試完成 =====")
    return {
        "raw_result": restaurant_details,
        "formatted_result": formatted_restaurant,
        "photo_url": photo_url
    }

# 如果直接運行此文件，則執行測試函數
if __name__ == "__main__":
    test_photo_retrieval_process()
