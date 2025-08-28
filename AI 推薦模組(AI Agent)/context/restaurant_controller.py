class RestaurantRecommendationController:
    def __init__(self):
        # 模擬餐廳資料
        self.restaurants = [
            {
                "name": "小確幸早午餐",
                "address": "台北市大安區幸福路 123 號",
                "rating": 4.5,
                "price_level_text": "$$",
                "photo": "",
                "is_open": True,
                "website": "http://example.com",
                "phone": "02-1234-5678",
                "user_ratings_total": 150,
                "matched_dishes": ["鬆餅", "咖啡", "雞肉三明治"],
                "meal_types": ["早餐", "午餐","下午茶"],
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
                "meal_types": ["晚餐", "宵夜"],
            },
            {
                "name": "夏日涼麵屋",
                "address": "台北市中正區涼爽路 10 號",
                "rating": 4.4,
                "price_level_text": "$",
                "photo": "",
                "is_open": True,
                "website": "http://liangmian.com",
                "phone": "02-3344-5566",
                "user_ratings_total": 120,
                "matched_dishes": ["涼麵", "味噌湯"],
                "meal_types": ["午餐", "晚餐"],
            },
            {
                "name": "甜點女王",
                "address": "台北市信義區甜點路 20 號",
                "rating": 4.7,
                "price_level_text": "$$",
                "photo": "",
                "is_open": True,
                "website": "http://dessertqueen.com",
                "phone": "02-5566-7788",
                "user_ratings_total": 210,
                "matched_dishes": ["舒芙蕾", "提拉米蘇", "牛肉鹹派"],
                "meal_types": ["下午茶"],
            },
            {
                "name": "開心燒烤店",
                "address": "台北市松山區快樂街 20 號",
                "rating": 4.4,
                "price_level_text": "$$",
                "photo": "",
                "is_open": True,
                "website": "http://happybbq.com",
                "phone": "02-3344-5566",
                "user_ratings_total": 200,
                "matched_dishes": ["烤牛肉", "串燒", "火鍋"],
                "meal_types": ["晚餐", "宵夜"],
            },
            {
                "name": "放鬆咖啡館",
                "address": "台北市文山區悠閒路 5 號",
                "rating": 4.6,
                "price_level_text": "$$",
                "photo": "",
                "is_open": True,
                "website": "http://relaxcafe.com",
                "phone": "02-7788-9900",
                "user_ratings_total": 130,
                "matched_dishes": ["手沖咖啡", "司康", "沙拉"],
                "meal_types": ["下午茶", "早餐"],
            },
        ]

    def process_query(self, query_text, user_location=None, user_id=None, context=None, emotions=None, preferences=None):
        # 取得時段
        meal_time = context.get("meal_time", "午餐") if context else "午餐"

        # 過濾符合當前meal_time的餐廳
        filtered_restaurants = [
            r for r in self.restaurants if meal_time in r.get("meal_types", [])
        ]
        if not filtered_restaurants:
            filtered_restaurants = self.restaurants

        # 偏好
        liked = preferences.get("喜歡", []) if isinstance(preferences, dict) else []
        disliked = preferences.get("不喜歡", []) if isinstance(preferences, dict) else []

        # 組合查詢關鍵字
        query_keywords = liked.copy()
        if query_text:
            query_keywords += [word.strip() for word in query_text.replace("，", ",").split(",")]

        # 情緒對應食物
        emotion_food_map = {
            "開心": ["烤肉", "串燒", "火鍋", "牛肉"],
            "放鬆": ["咖啡", "茶", "司康", "輕食"],
            "解壓": ["茶", "輕食", "沙拉"],
            "慶祝": ["火鍋", "串燒", "牛排", "海鮮"],
            "溫暖": ["熱湯", "燉飯", "咖哩"],
            "難過": ["甜點", "舒芙蕾", "提拉米蘇", "蛋糕", "巧克力"],
            "生氣": ["辣", "辛辣食物", "麻辣鍋"],
            "焦慮": ["茶", "輕食", "沙拉"],
            "疲倦": ["咖啡", "能量飲品", "甜點"],
            "孤單": ["甜點", "舒芙蕾", "熱飲", "鬆餅"],
            "驚訝": ["特別料理", "創意料理"],
        }
        if emotions:
            for emo in emotions:
                if emo in emotion_food_map:
                    query_keywords.extend(emotion_food_map[emo])

        # 計分
        scored_restaurants = []
        for rest in filtered_restaurants:
            score = 0
            for kw in query_keywords:
                if any(kw in dish for dish in rest["matched_dishes"]):
                    score += 2
            for like in liked:
                if any(like in dish for dish in rest["matched_dishes"]):
                    score += 1
            for dislike in disliked:
                if any(dislike in dish for dish in rest["matched_dishes"]):
                    score -= 3
            scored_restaurants.append((score, rest))

        scored_restaurants.sort(key=lambda x: x[0], reverse=True)
        recommended_restaurants = [rest for score, rest in scored_restaurants[:3]]

        return {"recommended_restaurants": recommended_restaurants}