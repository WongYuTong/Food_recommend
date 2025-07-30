# context/restaurant_controller.py

class RestaurantRecommendationController:
    def __init__(self):
        # 模擬餐廳資料（可改為向量 DB）
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

    def process_query(self, query_text, user_location, context=None, emotions=None, preferences=None):
        meal_time = context.get("meal_time", "午餐") if context else "午餐"
        day_type = context.get("day_type", "平日") if context else "平日"
        holiday = context.get("holiday", None)
        emotion_str = ", ".join(emotions) if emotions else "無"

        # 先過濾符合當前meal_time的餐廳
        filtered_restaurants = [
            r for r in self.restaurants if meal_time in r.get("meal_types", [])
        ]
        # 如果過濾結果為空，避免沒推薦，退回全部餐廳
        if not filtered_restaurants:
            filtered_restaurants = self.restaurants

        # 新用戶 fallback 判斷：偏好為空 or 無特別偏好
        if not preferences or preferences == ["無特別偏好"] or preferences == {}:
            top_popular = sorted(
                filtered_restaurants,
                key=lambda r: (r["rating"], r["user_ratings_total"]),
                reverse=True
            )
            loc_str = f"你目前的位置（大約在 {user_location}）" if user_location else "你的位置未提供"
            time_str = f"{meal_time}時間，{day_type}狀態" + (f"，今天是{holiday}" if holiday else "")
            return {
                "response_text":
                    f"這是你的第一次推薦，我們先根據{meal_time}時間推薦熱門餐廳。你也可以輸入口味喜好，我們會記住喔！",
                "recommended_restaurants": top_popular[:3]
            }

        liked = preferences.get("喜歡", []) if isinstance(preferences, dict) else []
        disliked = preferences.get("不喜歡", []) if isinstance(preferences, dict) else []

        query_keywords = liked.copy()
        if query_text:
            query_keywords += [word.strip() for word in query_text.replace("，", ",").split(",")]

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

        response = {
            "response_text":
                f"根據您的輸入『{query_text}』，位置 {user_location}，"
                f"情境：{meal_time}、{day_type}"
                + (f"、今天是 {holiday}" if holiday else "")
                + f"，偵測情緒：{emotion_str}，考慮您的偏好與當下情緒後，以下是推薦結果。",
            "recommended_restaurants": recommended_restaurants
        }

        return response