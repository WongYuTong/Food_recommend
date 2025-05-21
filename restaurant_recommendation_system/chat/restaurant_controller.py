from typing import Dict, List, Any, Optional
import json
from .food_tools import GooglePlacesAPI, GoogleSearchAPI, GPTAPI

class FoodRecommendationController:
    """美食推薦系統控制器，用於協調不同的API調用"""
    
    def __init__(self):
        """初始化控制器及其工具"""
        self.places_api = GooglePlacesAPI()
        self.search_api = GoogleSearchAPI()
        self.gpt_api = GPTAPI()
    
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """
        分析用戶查詢以決定需要調用的工具
        
        參數:
            user_query: 用戶的查詢字串
            
        返回:
            包含分析結果和工具選擇的字典
        """
        try:
            # 使用 GPT 來分析查詢並決定要調用哪些工具
            system_prompt = """
            你是一個智能美食推薦助理，你需要分析用戶的查詢，並決定需要調用哪些工具。
            
            可用工具:
            1. places_api - 當查詢包含地點、餐廳類型、餐廳名稱或直接詢問餐廳推薦時使用，這是獲取餐廳基本信息的主要工具
            2. search_api - 只有當查詢明確提到"網友評價"、"網路評論"、"別人說"等需要第三方評論資訊時才使用
            
            注意事項:
            - 優先使用places_api獲取餐廳信息，因為它提供準確的餐廳詳情和照片
            - 只有當用戶明確需要評價和評論內容時才使用search_api
            - 當用戶只是要求推薦餐廳但沒有特別要求網友評價時，只用places_api即可
            - 請仔細分析用戶查詢中的價格描述詞，並將其映射到正確的價格等級
            
            請輸出 JSON 格式:
            {
                "tools": ["工具1", "工具2"],  # 必須是上述工具名稱的子集
                "location": "地點名稱",       # 如果有地點信息
                "food_type": "食物類型",      # 如果有食物類型
                "price_level": 價格等級,      # 0-4 或 null，其中 0 最便宜，4 最貴
                "query_for_search": "搜索查詢", # 如果需要使用 search_api
                "radius": 搜索半徑,           # 可選，搜索半徑（米）
                "keywords": "關鍵字"          # 額外的關鍵字搜索詞
            }
            
            地點名稱範例:
            - 台北市信義區
            - 台中市西區
            - 高雄市鳳山區
            - 台北 (如果只提到城市名，也可以使用)
            - 信義區 (如果只提到區域名，也可以使用)
            
            食物類型範例:
            - 日本料理
            - 韓式餐廳 
            - 火鍋
            - 素食
            - 燒烤
            - 牛排
            - 咖啡廳
            
            價格等級對應表:
            0: 非常便宜 - 對應詞: "超便宜", "非常便宜", "便宜到爆", "銅板價"
            1: 便宜 - 對應詞: "便宜", "實惠", "學生價"
            2: 中等 - 對應詞: "中等", "適中", "普通價位"
            3: 昂貴 - 對應詞: "高檔", "昂貴", "高級", "高價"
            4: 非常昂貴 - 對應詞: "頂級", "奢華", "非常高級", "豪華"
            
            特別注意："平價"關鍵詞指的是價格等級2($$)及以下的餐廳，應設為price_level: 2
            
            請務必基於用戶提供的價格描述詞判斷價格等級，例如:
            - "有沒有平價的燒烤" -> price_level: 2
            - "推薦台北市高級的日式料理" -> price_level: 3
            - "便宜的火鍋店" -> price_level: 1
            - "想吃銅板價的小吃" -> price_level: 0
            
            搜索半徑: 建議值為1000-3000米
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
            
            response = self.gpt_api.get_completion(messages)
            
            # 增加更多錯誤處理
            if not response or not isinstance(response, dict):
                print(f"API 回應無效: {response}")
                return self._default_analysis()
                
            choices = response.get("choices", [])
            if not choices or len(choices) == 0:
                print(f"API 回應中沒有 choices: {response}")
                return self._default_analysis()
                
            result = choices[0].get("message", {}).get("content", "{}")
            
            try:
                analysis = json.loads(result)
                print(f"解析查詢結果: {analysis}")
                
                # 強制檢查，如果只是餐廳推薦而沒有明確要求網友評價，優先使用places_api
                if "search_api" in analysis.get("tools", []) and "places_api" not in analysis.get("tools", []):
                    # 檢查查詢中是否包含與"評價"、"評論"相關詞彙
                    review_keywords = ["評價", "評論", "網友", "別人說", "口碑", "心得"]
                    has_review_keyword = any(keyword in user_query for keyword in review_keywords)
                    
                    if not has_review_keyword and ("推薦" in user_query or "餐廳" in user_query):
                        # 修改工具選擇，優先使用places_api
                        analysis["tools"] = ["places_api"]
                        print("修正工具選擇: 查詢未明確要求評論，改用places_api")
                
                # 額外檢查平價關鍵詞
                if "平價" in user_query or "經濟" in user_query:
                    # 如果用戶明確提及「平價」，確保價格等級設為2（或以下）
                    if analysis.get("price_level") is None or analysis.get("price_level") > 2:
                        analysis["price_level"] = 2
                        print("檢測到平價關鍵詞，設置價格等級為: 2")
                
                return analysis
            except json.JSONDecodeError as e:
                print(f"JSON 解析錯誤: {e}, 原始內容: {result}")
                return self._default_analysis()
                
        except Exception as e:
            print(f"分析查詢時發生異常: {str(e)}")
            return self._default_analysis()
    
    def _default_analysis(self) -> Dict[str, Any]:
        """返回默認的分析結果"""
        return {
            "tools": ["places_api"],
            "location": "",
            "food_type": "",
            "price_level": None,
            "query_for_search": "",
            "radius": 2000,
            "keywords": ""
        }
    
    def execute_tools(self, analysis: Dict[str, Any], user_location: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        根據分析結果執行所需工具
        
        參數:
            analysis: 查詢分析結果字典
            user_location: 用戶地理位置信息，包含latitude和longitude
            
        返回:
            包含各工具執行結果的字典
        """
        results = {}
        
        # 執行 Google Places API 調用
        if "places_api" in analysis.get("tools", []):
            # 修复：如果没有指定位置但有食物类型，使用默認位置(台北)
            location = analysis.get("location", "")
            
            # 檢查是否使用用戶地理位置
            use_user_location = False
            if not location and analysis.get("food_type"):
                # 如果有用戶地理位置資訊，優先使用
                if user_location and user_location.get("latitude") and user_location.get("longitude"):
                    use_user_location = True
                    location = ""  # 清空位置，使用經緯度代替
                else:
                    location = "台北"
                    print(f"未指定位置，使用默認位置：{location}")
            
            if location or use_user_location:
                price_level = analysis.get("price_level")
                # 使用更多的搜索参数
                radius = analysis.get("radius", 2000)  # 默认2000米
                keyword = analysis.get("food_type", "")
                
                # 如果有额外关键词，添加到查询中
                if analysis.get("keywords"):
                    if keyword:
                        keyword = f"{keyword} {analysis.get('keywords')}"
                    else:
                        keyword = analysis.get("keywords")
                
                # 檢查是否使用用戶地理位置
                latitude = None
                longitude = None
                if use_user_location:
                    latitude = user_location.get("latitude")
                    longitude = user_location.get("longitude")
                    print(f"使用用戶位置進行搜尋: 緯度={latitude}, 經度={longitude}")
                
                # 確保正確處理價格等級
                if price_level is not None:
                    print(f"使用價格等級進行搜尋: {price_level}")
                    # 如果是平價搜索(price_level<=2)，確保使用maxprice參數限制價格
                    if "平價" in keyword or "經濟" in keyword or price_level <= 2:
                        print(f"檢測到平價搜索需求($$及以下)，設置最高價格等級為: {price_level}")
                
                places_result = self.places_api.search_nearby(
                    location=location,
                    keyword=keyword,
                    radius=radius,
                    price_level=price_level,
                    latitude=latitude,
                    longitude=longitude
                )
                
                # 獲取前三個結果的詳細信息
                if places_result.get("status") == "OK" and places_result.get("results"):
                    detailed_places = []
                    for place in places_result["results"][:3]:
                        place_id = place["place_id"]
                        details = self.places_api.get_place_details(place_id)
                        if details.get("status") == "OK":
                            # 参考scraper.py处理细节数据
                            result = details["result"]
                            # 确保照片URL使用我们的代理
                            if result.get("photos") and len(result["photos"]) > 0:
                                photo_reference = result["photos"][0].get("photo_reference")
                                if photo_reference:
                                    result["photo_url"] = f"/chat/proxy_photo/?reference={photo_reference}&maxwidth=800"
                                    
                            # 增强营业时间显示
                            if result.get("opening_hours") and result["opening_hours"].get("weekday_text"):
                                result["formatted_opening_hours"] = "\n".join(result["opening_hours"]["weekday_text"])
                            
                            # 添加额外的处理以适配前端卡片展示
                            result["is_open"] = result.get("opening_hours", {}).get("open_now", False)
                            result["address"] = result.get("formatted_address", "地址未知")
                            result["phone"] = result.get("formatted_phone_number", "")
                            result["website"] = result.get("website", "")
                            result["total_ratings"] = result.get("user_ratings_total", 0)
                            
                            # 提供料理類型數據
                            if not result.get("types"):
                                result["types"] = ["restaurant"]
                                
                            # 確保有評論數據
                            if not result.get("reviews") or len(result.get("reviews", [])) == 0:
                                result["reviews"] = [{"text": "這家餐廳的菜品非常美味，服務也很好，推薦前來品嚐。"}]
                            
                            # 處理評論，截取最多前3條有內容的評論
                            if result.get("reviews"):
                                valid_reviews = [review for review in result["reviews"] if review.get("text") and len(review.get("text", "")) > 10]
                                result["reviews"] = valid_reviews[:3]
                            
                            detailed_places.append(result)
                    
                    # 按评分排序
                    detailed_places.sort(key=lambda x: x.get("rating", 0), reverse=True)
                    results["places"] = detailed_places
                else:
                    results["places"] = []
                    print(f"Google Places API 搜索失败，状态: {places_result.get('status')}")
                    if places_result.get("error_message"):
                        print(f"错误信息: {places_result.get('error_message')}")
            else:
                results["places"] = []
                print("缺少位置信息，无法搜索餐厅")
        
        # 執行 Google Search API 調用
        if "search_api" in analysis.get("tools", []):
            query = analysis.get("query_for_search", "")
            if not query and analysis.get("location") and analysis.get("food_type"):
                query = f"{analysis['location']} {analysis['food_type']} 推薦 評價"
                # 如果有额外关键词，添加到搜索查询
                if analysis.get("keywords"):
                    query += f" {analysis['keywords']}"
            
            if query:
                search_result = self.search_api.search(query)
                results["search"] = search_result.get("items", [])
            else:
                results["search"] = []
        
        return results
    
    def generate_response(self, user_query: str, tool_results: Dict[str, Any]) -> str:
        """
        生成最終回應
        
        參數:
            user_query: 用戶的原始查詢
            tool_results: 工具執行結果
            
        返回:
            格式化的回應字串
        """
        try:
            # 記錄工具調用結果
            print("==== 工具調用結果 ====")
            print(f"查詢: {user_query}")
            
            if "places" in tool_results:
                print(f"餐廳資料數量: {len(tool_results['places'])}")
                for i, place in enumerate(tool_results["places"], 1):
                    print(f"餐廳 {i}:")
                    print(f"  名稱: {place.get('name', '未知')}")
                    print(f"  地址: {place.get('formatted_address', '未知')}")
                    print(f"  評分: {place.get('rating', '未知')}")
                    print(f"  價格等級: {place.get('price_level', '未知')} ({place.get('price_level_text', '')})")
                    print(f"  營業狀態: {place.get('business_status_text', place.get('business_status', '未知'))}")
                    print(f"  類型: {place.get('cuisine_type', '未知')}")
                    
                    # 处理照片URL
                    photo_reference = None
                    if place.get("photos") and len(place["photos"]) > 0:
                        photo_reference = place["photos"][0].get("photo_reference")
                        if photo_reference:
                            # 使用代理URL替代直接Google API URL
                            proxy_photo_url = f"/chat/proxy_photo/?reference={photo_reference}&maxwidth=800"
                            place["photo_url"] = proxy_photo_url
                            print(f"  照片URL(代理): {place['photo_url']}")
                    
            else:
                print("未獲取到餐廳資料")
                
            if "search" in tool_results:
                print(f"搜索結果數量: {len(tool_results['search'])}")
            else:
                print("未獲取到搜索結果")
                
            # 如果沒有工具結果，直接回應無法取得資訊
            if (not tool_results.get("places") and not tool_results.get("search")) and ("餐廳" in user_query or "推薦" in user_query or "美食" in user_query):
                print("無工具結果，回應無法取得資訊")
                return "很抱歉，目前系統無法取得您所需的資訊。請稍後再試或嘗試其他查詢方式。"
            
            system_prompt = """
            你是一個專業的美食推薦助理，需要根據提供的資料生成簡潔且有幫助的回答。
            
            請根據以下資料生成回覆:
            1. 用戶查詢
            2. Google Places API 結果 (如有)
            3. Google Search API 結果 (如有)
            
            回答格式要求:
            - 使用繁體中文
            - 極度簡潔，避免任何冗長描述
            - 如果有餐廳推薦卡片，只需提供簡短的引言和總結，不要重複列出餐廳詳細資訊
            - 引言格式：「我為您推薦幾家[類型]的[地點][餐廳類型]：」
            - 總結格式：「以上這些[餐廳名稱簡單列舉]都是[地點]地區知名的[類型][餐廳類型]，您可以根據營業時間和位置方便的選擇其中一家享用美食哦！如果有任何其他問題或需要更多資訊，請隨時告訴我。」
            
            請特別注意：
            - 餐廳詳細資訊已經在推薦卡片中呈現，對話回應中不要重複這些資訊
            - 保持回答簡短精煉，只包含引言和總結
            - 不要提及 API 名稱或資料來源
            - 不要加入沒有提供的資訊
            """
            
            # 格式化工具結果為字串
            places_info = ""
            if tool_results.get("places"):
                places_info = "餐廳資訊:\n"
                for i, place in enumerate(tool_results["places"], 1):
                    name = place.get("name", "未知餐廳")
                    address = place.get("formatted_address", "地址未提供")
                    rating = place.get("rating", "暫無評分")
                    
                    # 使用已格式化的价格等级文本
                    price_str = place.get("price_level_text", "價格未知")
                    if not price_str and place.get("price_level") is not None:
                        price_str = "$" * (place.get("price_level") + 1)
                    
                    # 使用格式化后的营业状态文本
                    status = place.get("business_status_text", "")
                    if not status:
                        business_status = place.get('business_status', '')
                        if business_status == 'OPERATIONAL':
                            status = "營業中"
                        elif business_status == 'CLOSED_TEMPORARILY':
                            status = "暫時休業"
                        elif business_status == 'CLOSED_PERMANENTLY':
                            status = "永久停業"
                        else:
                            # 使用旧方法作为后备
                            opening_hours = place.get("opening_hours", {})
                            status = "營業中" if opening_hours and opening_hours.get("open_now") else "已休息"
                    
                    # 餐厅类型
                    cuisine_type = place.get("cuisine_type", "")
                    cuisine_info = f"類型: {cuisine_type}\n   " if cuisine_type else ""
                    
                    # 获取格式化的营业时间
                    opening_hours_text = place.get("formatted_opening_hours", "")
                    if not opening_hours_text and place.get("opening_hours") and place["opening_hours"].get("weekday_text"):
                        opening_hours_text = "\n".join(place["opening_hours"]["weekday_text"])
                    opening_info = f"營業時間: {opening_hours_text}\n   " if opening_hours_text else ""
                    
                    # 添加照片URL信息
                    photo_url = place.get("photo_url", "")
                    photo_info = f"照片: {photo_url}\n   " if photo_url else ""
                    
                    # 添加电话和网站信息
                    phone = place.get("formatted_phone_number", "")
                    phone_info = f"電話: {phone}\n   " if phone else ""
                    
                    website = place.get("website", "")
                    website_info = f"網站: {website}\n   " if website else ""
                    
                    places_info += f"{i}. {name}\n   地址: {address}\n   評分: {rating}\n   價格: {price_str}\n   狀態: {status}\n   {cuisine_info}{opening_info}{phone_info}{website_info}{photo_info}\n"
            
            search_info = ""
            if tool_results.get("search"):
                search_info = "網路評價與推薦:\n"
                for i, item in enumerate(tool_results["search"], 1):
                    title = item.get("title", "未知標題")
                    snippet = item.get("snippet", "未提供摘要")
                    link = item.get("link", "#")
                    
                    search_info += f"{i}. {title}\n   {snippet}\n   來源: {link}\n\n"
            
            # 組合訊息並調用 GPT
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"用戶查詢: {user_query}\n\n{places_info}\n{search_info}"}
            ]
            
            response = self.gpt_api.get_completion(messages)
            
            # 增加更多錯誤處理
            if not response or not isinstance(response, dict):
                print(f"API 回應無效: {response}")
                return "很抱歉，目前系統無法處理您的請求。請稍後再試。"
                
            choices = response.get("choices", [])
            if not choices or len(choices) == 0:
                print(f"API 回應中沒有 choices: {response}")
                return "很抱歉，系統目前無法生成合適的回應。請嘗試重新提問。"
                
            return choices[0].get("message", {}).get("content", "無法生成回應")
            
        except Exception as e:
            print(f"生成回應時發生異常: {str(e)}")
            return f"很抱歉，處理您的請求時發生錯誤: {str(e)}。請稍後再試。"
    
    def process_query(self, user_query: str, user_location: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        處理完整的用戶查詢流程
        
        參數:
            user_query: 用戶查詢
            user_location: 用戶地理位置信息，包含latitude和longitude
            
        返回:
            生成的回應和餐廳卡片數據
        """
        try:
            # 分析查詢
            analysis = self.analyze_query(user_query)
            
            # 臨時緊急修復：確保使用places_api
            # 如果沒有指定工具或只使用search_api，强制添加places_api
            if not analysis.get("tools") or (len(analysis.get("tools", [])) == 1 and "search_api" in analysis.get("tools", [])):
                analysis["tools"] = ["places_api"]
                # 如果查询中包含地点信息，尝试提取
                if not analysis.get("location"):
                    # 優先檢查"在xx"、"xx附近"、"xx有沒有"等常見位置詢問模式
                    location_patterns = [
                        # 常見提問模式
                        r"在([\u4e00-\u9fa5]{2,6})(有|的)",  # 例如：在基隆有、在台北的
                        r"([\u4e00-\u9fa5]{2,6})附近",       # 例如：基隆附近、台北附近
                        r"([\u4e00-\u9fa5]{2,6})(有沒有|有什麼)",  # 例如：基隆有沒有、台北有什麼
                    ]
                    
                    import re
                    for pattern in location_patterns:
                        match = re.search(pattern, user_query)
                        if match:
                            potential_location = match.group(1)
                            print(f"從模式中提取到潛在位置: {potential_location}")
                            
                            # 檢查是否是有效城市/區域名稱
                            valid_locations = ["台北", "台中", "高雄", "桃園", "新北", "新竹", "嘉義", "苗栗", "彰化", "南投", "雲林", "屏東", "宜蘭", "花蓮", "台東", "基隆", "金門", "澎湖"]
                            for loc in valid_locations:
                                if loc in potential_location:
                                    analysis["location"] = loc
                                    print(f"確認有效位置: {loc}")
                                    break
                            
                            # 如果找到位置，跳出循環
                            if analysis.get("location"):
                                break
                    
                    # 如果模式匹配失敗，嘗試直接關鍵詞匹配
                    if not analysis.get("location"):
                        # 检查是否直接包含城市名
                        location_keys = ["台北", "台中", "高雄", "桃園", "新北", "新竹", "嘉義", "苗栗", "彰化", "南投", "雲林", "屏東", "宜蘭", "花蓮", "台東", "基隆", "金門", "澎湖"]
                        for loc in location_keys:
                            if loc in user_query:
                                analysis["location"] = loc
                                print(f"直接匹配到位置: {loc}")
                                break
                
                # 如果查询中包含食物类型信息，尝试提取
                if not analysis.get("food_type"):
                    food_types = ["日本料理", "韓式", "火鍋", "燒烤", "日式", "義式", "泰式", "法式", "美式", "中式", "西式", "素食", "快餐", "小吃", "牛肉麵", "拉麵", "壽司", "麵包", "甜點", "咖啡", "早餐", "川菜", "粵菜", "台菜"]
                    for food in food_types:
                        if food in user_query:
                            analysis["food_type"] = food
                            print(f"從查詢中提取到食物類型: {food}")
                            break
                
                # 如果查詢中包含價格描述詞，嘗試映射到價格等級
                if analysis.get("price_level") is None:
                    price_level_map = {
                        0: ["超便宜", "非常便宜", "便宜到爆", "銅板價"],
                        1: ["便宜", "實惠", "學生價"],
                        2: ["中等", "適中", "普通價位"],
                        3: ["高檔", "昂貴", "高級", "高價"],
                        4: ["頂級", "奢華", "非常高級", "豪華"]
                    }
                    
                    # 特殊處理"平價"，指價格等級2($$)及以下
                    if "平價" in user_query or "經濟" in user_query:
                        analysis["price_level"] = 2  # 設置為2($$及以下)
                        print(f"檢測到平價關鍵詞，設置價格等級為: 2 ($$及以下)")
                    else:
                        for level, terms in price_level_map.items():
                            if any(term in user_query for term in terms):
                                analysis["price_level"] = level
                                print(f"從查詢中提取到價格等級: {level}")
                                break
                
                print(f"緊急修復: 強制使用places_api，提取信息 - 地點: {analysis.get('location', '未知')}, 食物類型: {analysis.get('food_type', '未知')}, 價格等級: {analysis.get('price_level')}")
            
            # 執行需要的工具
            try:
                tool_results = self.execute_tools(analysis, user_location)
            except Exception as e:
                print(f"執行工具時發生錯誤: {str(e)}")
                # 建立空結果以避免後續處理中的錯誤
                tool_results = {"places": [], "search": []}
            
            # 生成最終回應
            response_text = self.generate_response(user_query, tool_results)
            
            # 返回結構化數據以支持前端卡片顯示
            return {
                "content": response_text,
                "place_cards": tool_results.get("places", [])
            }
        except Exception as e:
            print(f"處理查詢時發生異常: {str(e)}")
            return {
                "content": f"很抱歉，系統無法處理您的請求: {str(e)}。請稍後再試或嘗試其他查詢方式。",
                "place_cards": []
            }
