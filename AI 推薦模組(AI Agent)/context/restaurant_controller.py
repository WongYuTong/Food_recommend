# context/restaurant_controller.py

class RestaurantRecommendationController:
    def __init__(self):
        # 可在此初始化向量資料庫、地圖 API、菜單分析模型等
        pass

    def process_query(self, query_text, user_location, context=None, emotions=None):
        """
        根據使用者輸入、位置、情境 (時段、節日)、情緒進行推薦餐廳。
        回傳示範格式供前端顯示。
        """

        # 模擬依情境與情緒進行推薦邏輯
        meal_time = context.get("meal_time", "午餐") if context else "午餐"
        day_type = context.get("day_type", "平日") if context else "平日"
        holiday = context.get("holiday", None)

        emotion_str = ", ".join(emotions) if emotions else "無"

        # 模擬餐廳推薦結果
        recommended_restaurants = [
            {
                "name": "小確幸早午餐",
                "address": "台北市大安區幸福路 123 號",
                "rating": 4.5,
                "price_level_text": "$$",
                "photo": "",  # 可接 Google Place API 取得實際圖
                "is_open": True,
                "website": "http://example.com",
                "phone": "02-1234-5678",
                "user_ratings_total": 150,
                "matched_dishes": ["鬆餅", "咖啡"],
            },
            {
                "name": "深夜療癒拉麵",
                "address": "台北市中山區美食街 456 號",
                "rating": 4.3,
                "price_level_text": "$",
                "photo": "",
                "is_open": True,
                "website": "http://example-ramen.com",
                "phone": "02-8765-4321",
                "user_ratings_total": 98,
                "matched_dishes": ["豚骨拉麵", "煎餃"],
            },
        ]

        response = {
            "response_text": f"根據您的輸入『{query_text}』，位置 {user_location}，情境：{meal_time}、{day_type}" + \
                             (f"、今天是 {holiday}" if holiday else "") + \
                             f"，偵測情緒：{emotion_str}，以下是推薦結果。",
            "recommended_restaurants": recommended_restaurants
        }

        return response