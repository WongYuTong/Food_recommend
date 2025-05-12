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
                      radius: int = 1500, 
                      type: str = "restaurant", 
                      price_level: Optional[int] = None) -> Dict[str, Any]:
        """
        搜尋指定位置附近的餐廳
        
        參數:
            location: 搜尋地點 (例如: "台中市一中街")
            keyword: 搜尋關鍵字 (例如: "日式料理")
            radius: 搜尋半徑 (單位: 米)
            type: 地點類型 (預設: "restaurant")
            price_level: 價格等級 (0-4，4最貴，None表示不限)
        
        返回:
            包含餐廳資料的字典
        """
        # 先進行地理編碼獲取座標
        geocode_url = f"{self.base_url}/findplacefromtext/json"
        geocode_params = {
            "input": location,
            "inputtype": "textquery",
            "fields": "geometry",
            "key": self.api_key
        }
        
        response = requests.get(geocode_url, params=geocode_params)
        result = response.json()
        
        if result.get("status") != "OK" or not result.get("candidates"):
            return {"error": f"無法找到位置: {location}"}
        
        # 獲取座標
        location_data = result["candidates"][0]["geometry"]["location"]
        lat = location_data["lat"]
        lng = location_data["lng"]
        
        # 搜尋附近餐廳
        nearby_url = f"{self.base_url}/nearbysearch/json"
        nearby_params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": type,
            "key": self.api_key
        }
        
        if keyword:
            nearby_params["keyword"] = keyword
        
        if price_level is not None:
            nearby_params["maxprice"] = price_level
        
        response = requests.get(nearby_url, params=nearby_params)
        return response.json()
    
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
            "fields": "name,rating,formatted_address,formatted_phone_number,opening_hours,price_level,review,website,photo,user_ratings_total",
            "key": self.api_key
        }
        
        response = requests.get(details_url, params=params)
        return response.json()


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
            "num": num
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
        data = {
            "model": model,
            "messages": messages
        }
        
        response = requests.post(self.base_url, headers=self.headers, json=data)
        return response.json()
