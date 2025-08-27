# sample_data.py
# 📦 模擬資料集中管理（功能一～四通用）

# --- 功能一：反向推薦條件擷取用句子（含預期排除項目） ---
NEGATIVE_INPUTS = [
    {"text": "我不想吃火鍋、燒烤和壽司", "expected": ["火鍋", "燒烤", "壽司"]},
    {"text": "不要牛排，不吃辣", "expected": ["牛排", "辣"]},
    {"text": "不過我可能不想要拉麵和韓式", "expected": ["拉麵", "韓式"]},
    {"text": "別推薦甜點或飲料了，我最近忌口", "expected": ["甜點", "飲料"]},
    {"text": "我不太喜歡炸雞和披薩", "expected": ["炸雞", "披薩"]},
    {"text": "不要推薦吃到飽，我怕吃不回本", "expected": ["吃到飽"]},
    {"text": "我最近牙痛，不想吃太硬的", "expected": ["太硬"]},
    {"text": "不想吃太油的料理", "expected": ["太油"]},
    {"text": "別推薦早午餐了", "expected": ["早午餐"]},
    {"text": "不想要餐廳火鍋或地方牛排", "expected": ["火鍋", "牛排"]},
    {"text": "不想吃吃到飽的", "expected": ["吃到飽"]},
    {"text": "不要推薦火鍋了", "expected": ["火鍋"]},
    {"text": "我不喜歡早午餐呢", "expected": ["早午餐"]},
    {"text": "不要那家甜點店啦", "expected": ["甜點"]},
]



# --- 功能二 & 四：餐廳清單（推薦理由補強 + 卡片欄位模擬） ---
RESTAURANTS_SAMPLE = [
    {
        "name": "小確幸甜點店",
        "rating": 4.6,
        "address": "台北市大安區忠孝東路100號",
        "is_open": True,
        "ai_reason": "甜點口感細緻，整體氣氛舒適",
        "comment_summary": "甜點評價很高，店員親切",
        "highlight": "甜點評價高",
        "matched_tags": ["甜點", "大安區", "高評價"],
        "price_level": "$",
        "review_count": 313,
        "reason_score": 9.2,
        "features": ["高評價", "價格便宜", "甜點專門"],
        "style": "文青",
        "opening_hours": "10:00–18:00",
        "distance_m": 365
    },
    {
        "name": "阿牛燒肉",
        "rating": 4.2,
        "address": "新北市板橋區文化路88號",
        "is_open": False,
        "ai_reason": "",
        "comment_summary": "份量充足，適合聚餐",
        "highlight": "份量大",
        "matched_tags": ["燒肉", "板橋區"],
        "price_level": "$$$",
        "review_count": 371,
        "reason_score": 8.5,
        "features": ["聚餐推薦", "肉量多"],
        "style": "美式",
        "opening_hours": "17:00–23:00",
        "distance_m": 1194
    },
    {
        "name": "拉麵一郎",
        "rating": 4.8,
        "address": "台北市中山區南京東路三段99號",
        "is_open": True,
        "ai_reason": "拉麵湯頭濃郁，肉質滑嫩",
        "comment_summary": "",
        "highlight": "人氣拉麵名店",
        "matched_tags": ["拉麵", "中山區"],
        "price_level": "$$",
        "review_count": 510,
        "reason_score": 9.7,
        "features": ["人氣餐廳", "日式風味"],
        "style": "日式",
        "opening_hours": "11:30–21:30",
        "distance_m": 781
    },
    {
        "name": "夜貓咖啡屋",
        "rating": 4.3,
        "address": "台北市信義區松壽路20號",
        "is_open": True,
        "ai_reason": "適合夜晚小酌，氛圍放鬆",
        "comment_summary": "氣氛不錯，適合聊天聚會",
        "highlight": "氣氛佳",
        "matched_tags": ["咖啡", "信義區", "夜貓族"],
        "price_level": "$$",
        "review_count": 198,
        "reason_score": 8.8,
        "features": ["宵夜好選擇", "氣氛佳"],
        "style": "夜貓族",
        "opening_hours": "18:00–02:00",
        "distance_m": 2140
    },
    {
        "name": "泰式小館",
        "rating": 4.0,
        "address": "台北市萬華區西園路一段50號",
        "is_open": False,
        "ai_reason": "",
        "comment_summary": "",
        "highlight": "",
        "matched_tags": [],
        "price_level": "$",
        "review_count": 89,
        "reason_score": 7.5,
        "features": ["異國料理", "價格親民"],
        "style": "東南亞風",
        "opening_hours": "11:00–15:00",
        "distance_m": 2980
    }
]


# --- 功能三-1 ：模糊語句  ---
PROMPT_TEST_INPUTS = [
    {"text": "都可以啦，你決定", "expected_level": "vague"},
    {"text": "不想吃辣的，我吃素", "expected_level": "clear"},
    {"text": "朋友聚餐，希望氣氛好一點", "expected_level": "clear"},
    {"text": "今天想吃點便宜的", "expected_level": "clear"},
    {"text": "還沒想好要吃什麼", "expected_level": "slight"},
    {"text": "我爸媽要一起吃，要安靜一點的地方", "expected_level": "clear"},
]




# --- 功能三-2：語意引導建議 測試資料（修正版） ---
GUIDANCE_TEST_INPUTS = [
    {
        "text": "我不吃辣，吃素，想找適合約會的",
        "expected_levels": ["飲食偏好", "用餐場合"],
        "expected_keywords": ["辣味", "素食", "約會"]
    },
    {
        "text": "朋友聚餐又要便宜",
        "expected_levels": ["用餐場合", "預算"],
        "expected_keywords": ["聚會", "平價"]
    },
    {
        "text": "我爸媽要一起吃，要安靜一點的地方",
        "expected_levels": ["用餐場合"],
        "expected_keywords": ["安靜", "家庭"]
    },
    {
        "text": "想吃熱的，時間不多",
        "expected_levels": ["飲食狀態"],
        "expected_keywords": ["供餐快速", "溫暖"]
    },
    {
        "text": "我想吃漢堡",
        "expected_levels": ["料理類型"],
        "expected_keywords": ["漢堡"]
    },
    {
        "text": "不吃海鮮，也不想要甜點",
        "expected_levels": ["飲食偏好", "排除語句"],
        "expected_keywords": ["海鮮", "甜點", "排除"]
    },
    {
        "text": "我吃素",
        "expected_levels": ["飲食偏好"],
        "expected_keywords": ["素食"]
    },
    {
        "text": "不知道欸",
        "expected_levels": ["其他"],
        "expected_keywords": []
    },
    {
        "text": "我想吃宵夜",
        "expected_levels": ["時段"],
        "expected_keywords": ["宵夜"]
    },
    {
        "text": "今天早餐想簡單吃",
        "expected_levels": ["時段", "飲食狀態"],
        "expected_keywords": ["早餐", "輕食"]
    },
    {
        "text": "想吃義大利麵",
        "expected_levels": ["料理類型"],
        "expected_keywords": ["義式", "義大利麵"]
    },
    {
        "text": "今天想吃韓式的",
        "expected_levels": ["料理類型"],
        "expected_keywords": ["韓式"]
    },
    {
        "text": "我想吃重口味的麻辣鍋",
        "expected_levels": ["飲食狀態"],
        "expected_keywords": ["重口味", "麻辣"]
    }
]


