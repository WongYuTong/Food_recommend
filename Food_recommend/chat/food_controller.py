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
        # 使用 GPT 來分析查詢並決定要調用哪些工具
        system_prompt = """
        你是一個智能美食推薦助理，你需要分析用戶的查詢，並決定需要調用哪些工具。
        
        可用工具:
        1. places_api - 當查詢含有明確地點、餐廳類型或需要即時資訊（營業時間、距離等）時使用
        2. search_api - 當查詢提到評價、熱門、推薦、網友說等需要網路評論資訊時使用
        
        請輸出 JSON 格式:
        {
            "tools": ["工具1", "工具2"],  # 必須是上述工具名稱的子集
            "location": "地點名稱",       # 如果有地點信息
            "food_type": "食物類型",      # 如果有食物類型
            "price_level": 價格等級,      # 0-4 或 null，其中 0 最便宜，4 最貴
            "query_for_search": "搜索查詢" # 如果需要使用 search_api
        }
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        response = self.gpt_api.get_completion(messages)
        result = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        
        try:
            analysis = json.loads(result)
            return analysis
        except json.JSONDecodeError:
            # 如果 GPT 未返回有效 JSON，使用保守的默認值
            return {
                "tools": ["places_api"],
                "location": "",
                "food_type": "",
                "price_level": None,
                "query_for_search": ""
            }
    
    def execute_tools(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        根據分析結果執行所需工具
        
        參數:
            analysis: 查詢分析結果字典
            
        返回:
            包含各工具執行結果的字典
        """
        results = {}
        
        # 執行 Google Places API 調用
        if "places_api" in analysis.get("tools", []):
            if analysis.get("location"):
                price_level = analysis.get("price_level")
                places_result = self.places_api.search_nearby(
                    location=analysis["location"],
                    keyword=analysis.get("food_type", ""),
                    price_level=price_level
                )
                
                # 獲取前三個結果的詳細信息
                if places_result.get("status") == "OK" and places_result.get("results"):
                    detailed_places = []
                    for place in places_result["results"][:3]:
                        place_id = place["place_id"]
                        details = self.places_api.get_place_details(place_id)
                        if details.get("status") == "OK":
                            detailed_places.append(details["result"])
                    
                    results["places"] = detailed_places
                else:
                    results["places"] = []
            else:
                results["places"] = []
        
        # 執行 Google Search API 調用
        if "search_api" in analysis.get("tools", []):
            query = analysis.get("query_for_search", "")
            if not query and analysis.get("location") and analysis.get("food_type"):
                query = f"{analysis['location']} {analysis['food_type']} 推薦 評價"
            
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
        system_prompt = """
        你是一個專業的美食推薦助理，需要根據提供的資料生成詳細且有幫助的回答。
        
        請根據以下資料生成回覆:
        1. 用戶查詢
        2. Google Places API 結果 (如有)
        3. Google Search API 結果 (如有)
        
        回答應該:
        - 使用繁體中文
        - 整合所有資訊，提供連貫且自然的回覆
        - 包含實用的詳細資訊（地址、評分、營業時間等）
        - 針對用戶的具體需求提供建議
        - 語調親切且專業
        
        不要:
        - 提及 API 名稱或資料來源
        - 使用標準模板化回答
        - 加入沒有提供的資訊
        """
        
        # 格式化工具結果為字串
        places_info = ""
        if tool_results.get("places"):
            places_info = "餐廳資訊:\n"
            for i, place in enumerate(tool_results["places"], 1):
                name = place.get("name", "未知餐廳")
                address = place.get("formatted_address", "地址未提供")
                rating = place.get("rating", "暫無評分")
                
                price_level = place.get("price_level", None)
                price_str = "價格未知"
                if price_level is not None:
                    price_str = "¥" * (price_level + 1)
                
                opening_hours = place.get("opening_hours", {})
                is_open = "營業中" if opening_hours.get("open_now") else "已休息"
                
                places_info += f"{i}. {name}\n   地址: {address}\n   評分: {rating}\n   價格: {price_str}\n   狀態: {is_open}\n\n"
        
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
        return response.get("choices", [{}])[0].get("message", {}).get("content", "無法生成回應")
    
    def process_query(self, user_query: str) -> str:
        """
        處理完整的用戶查詢流程
        
        參數:
            user_query: 用戶查詢
            
        返回:
            生成的回應
        """
        # 分析查詢
        analysis = self.analyze_query(user_query)
        
        # 執行需要的工具
        tool_results = self.execute_tools(analysis)
        
        # 生成最終回應
        response = self.generate_response(user_query, tool_results)
        
        return response
