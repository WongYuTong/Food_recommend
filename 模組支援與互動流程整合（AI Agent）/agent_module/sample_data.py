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
        "reason_score": 9.2
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
        "reason_score": 8.5
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
        "reason_score": 9.7
    }
]

# --- 功能三 & 三-2：模糊語句 / 語意提示句 ---
PROMPT_TEST_INPUTS = [
    "都可以啦，你決定",
    "不想吃辣的，我吃素",
    "朋友聚餐，希望氣氛好一點",
    "今天想吃點便宜的",
    "還沒想好要吃什麼",
    "我爸媽要一起吃，要安靜一點的地方"
]
