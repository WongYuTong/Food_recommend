class RestaurantRecommendationController:
    def __init__(self):
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
                "matched_dishes": ["豚骨拉麵", "煎餃", "雞肉拉麵"],
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
                "matched_dishes": ["涼麵", "味噌湯", "海鮮涼麵", "素食涼麵"],
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
                "matched_dishes": ["舒芙蕾", "提拉米蘇", "牛肉鹹派", "蛋糕", "巧克力"],
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
                "matched_dishes": ["烤牛肉", "串燒", "火鍋", "豬肉串", "海鮮烤盤"],
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
                "matched_dishes": ["手沖咖啡", "司康", "沙拉", "輕食三明治"],
                "meal_types": ["下午茶", "早餐"],
            },
            {
                "name": "海鮮饗宴",
                "address": "台北市信義區海鮮路 50 號",
                "rating": 4.5,
                "price_level_text": "$$$",
                "photo": "",
                "is_open": True,
                "website": "http://seafoodfeast.com",
                "phone": "02-1122-3344",
                "user_ratings_total": 180,
                "matched_dishes": ["烤鮭魚", "海鮮鍋", "生蠔", "蝦仁炒飯", "龍蝦"],
                "meal_types": ["午餐", "晚餐"],
            },
            {
                "name": "牛排之家",
                "address": "台北市中山區牛排街 88 號",
                "rating": 4.6,
                "price_level_text": "$$$",
                "photo": "",
                "is_open": True,
                "website": "http://steakhouse.com",
                "phone": "02-2233-4455",
                "user_ratings_total": 160,
                "matched_dishes": ["肋眼牛排", "菲力牛排", "牛肉漢堡", "沙拉", "燉牛肉"],
                "meal_types": ["晚餐"],
            },
            {
                "name": "雞肉專賣店",
                "address": "台北市大同區雞街 12 號",
                "rating": 4.3,
                "price_level_text": "$$",
                "photo": "",
                "is_open": True,
                "website": "http://chickenhouse.com",
                "phone": "02-5566-8899",
                "user_ratings_total": 140,
                "matched_dishes": ["烤雞腿", "雞肉沙拉", "雞肉捲", "雞肉湯", "咖哩雞"],
                "meal_types": ["午餐", "晚餐"],
            },
            {
                "name": "豬肉坊",
                "address": "台北市南港區豬肉路 33 號",
                "rating": 4.2,
                "price_level_text": "$$",
                "photo": "",
                "is_open": True,
                "website": "http://porkcorner.com",
                "phone": "02-6677-8899",
                "user_ratings_total": 110,
                "matched_dishes": ["烤豬排", "豬肉鍋", "五花肉", "豬肉漢堡", "滷豬腳"],
                "meal_types": ["午餐", "晚餐", "宵夜"],
            },
        ]

    def process_query(
        self,
        query_text,
        user_location=None,
        user_id=None,
        context=None,
        emotions=None,
        preferences=None,
        short_term_preferences=None
    ):
        # 取得時段
        meal_time = context.get("meal_time", "午餐") if context else "午餐"

        # 過濾符合當前meal_time的餐廳
        filtered_restaurants = [
            r for r in self.restaurants if meal_time in r.get("meal_types", [])
        ]
        if not filtered_restaurants:
            filtered_restaurants = self.restaurants

        # 長期偏好
        long_liked = preferences.get("喜歡", []) if isinstance(preferences, dict) else []
        long_disliked = preferences.get("不喜歡", []) if isinstance(preferences, dict) else []

        # 短期偏好
        short_liked = []
        if isinstance(short_term_preferences, dict):
            short_liked = short_term_preferences.get("喜歡", [])

        # 情緒對應食物加到短期偏好
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
                    short_liked.extend(emotion_food_map[emo])

        # 計分
        scored_restaurants = []
        for rest in filtered_restaurants:
            score = 0
            # 短期偏好加分固定3
            for kw in short_liked:
                if any(kw in dish for dish in rest["matched_dishes"]):
                    score += 3
            # 長期喜歡依權重加分
            for kw in long_liked:
                weight = 1
                if user_id:
                    from context.models import UserPreference  # 替換為你的實際 models 模組
                    pref_obj = UserPreference.objects.filter(
                        user_id=user_id, keyword=kw, preference_type="like"
                    ).first()
                    if pref_obj:
                        weight = pref_obj.weight
                if any(kw in dish for dish in rest["matched_dishes"]):
                    score += weight
            # 長期不喜歡依權重扣分
            for kw in long_disliked:
                weight = 1
                if user_id:
                    from context.models import UserPreference
                    pref_obj = UserPreference.objects.filter(
                        user_id=user_id, keyword=kw, preference_type="dislike"
                    ).first()
                    if pref_obj:
                        weight = pref_obj.weight
                if any(kw in dish for dish in rest["matched_dishes"]):
                    score -= weight
            scored_restaurants.append((score, rest))

        # 分數排序
        scored_restaurants.sort(key=lambda x: x[0], reverse=True)

        # 取前三名推薦
        recommended_restaurants = [rest for score, rest in scored_restaurants[:3]]

        return {"recommended_restaurants": recommended_restaurants}