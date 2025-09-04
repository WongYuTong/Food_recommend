# === 📦 imports ===

# 標準庫
import json
import re
import random

# Django
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# DRF
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.test import APIRequestFactory  # ✅ 新增這行
from rest_framework.request import Request
from rest_framework.parsers import JSONParser

# 本地 utils（共用邏輯）
from .utils_card import (
    generate_map_url,
    format_open_status,
    extract_district,
    generate_price_description,
    generate_recommend_reason
)


# 功能 1：反向推薦條件擷取（最終強化版 v3）
class ExtractNegativeConditionsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get('type')
        user_input = request.data.get('text', '').strip()

        if req_type != 'text' or not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='text' 且包含 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 否定語句樣式（✅ 已擴充）
        prefix = r'(?:我|不過|那就|可能)?'
        negative_verbs = r'(不想吃|不想要|不要|不吃|別推薦|不要推薦|不太想吃|沒有很喜歡|那種我不愛|不會選|不太喜歡|不喜歡|不愛|我不會選)'
        pattern = rf'{prefix}{negative_verbs}(.+?)(?:[，。!！,\.]|$)'

        matches = re.findall(pattern, user_input)

        # 功能詞前綴（剃除）
        FUNCTION_PREFIXES = ['推薦', '餐廳', '地方', '那家', '這家', '店家', '吃', '想吃', '提供']

        # 結尾語助詞（✅ 已擴充）
        TAIL_PARTICLES = r'[的了呢啦啊嘛唷喔哦耶呀囉吧]*$'

        # 保留詞（完整詞不能拆）
        PRESERVE_TERMS = ['吃到飽', '早午餐', '宵夜', '套餐', '內用', '外帶']

        # 結尾修飾詞（自動刪除）
        CLEAN_SUFFIXES = ['的料理', '料理', '店家', '餐廳', '類型', '類', '那家', '這家', '店']

        excluded_items = []

        for match in matches:
            phrase = match[1] if isinstance(match, tuple) and len(match) > 1 else match[0] if isinstance(match, tuple) else match
            split_words = re.split(r'[,、，和跟以及或還有\s]+', phrase)

            for word in split_words:
                word = word.strip()

                # ✅ 若為保留詞或「保留詞+的」，直接保留
                if word in PRESERVE_TERMS:
                    cleaned = word
                elif word.endswith("的") and word[:-1] in PRESERVE_TERMS:
                    cleaned = word[:-1]
                else:
                    # 去除功能詞前綴
                    for prefix_word in FUNCTION_PREFIXES:
                        if word.startswith(prefix_word):
                            word = word[len(prefix_word):]
                            break

                    # 去除語尾助詞
                    word = re.sub(TAIL_PARTICLES, '', word)

                    # 去除結尾修飾詞（像是「甜點店」→「甜點」）
                    for suffix in CLEAN_SUFFIXES:
                        if word.endswith(suffix) and len(word) > len(suffix):
                            word = word[:-len(suffix)]
                            break

                    cleaned = word

                if cleaned:
                    excluded_items.append(cleaned)

        unique_excluded = sorted(set(excluded_items))

        return Response({
            "status": "success",
            "data": {
                "excluded": unique_excluded
            },
            "message": "已擷取反向推薦條件"
        }, status=status.HTTP_200_OK)


# 功能 2：推薦理由補強 + 結構化輸出（強化版）
class GenerateRecommendReasonView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # ✅ 接收 user_input（可選）
        user_input = request.data.get("user_input", "").lower().strip()

        if hasattr(request, 'data'):
            req_type = request.data.get('type')
            restaurants = request.data.get('restaurants', [])
        else:
            req_type = request.POST.get('type')
            try:
                restaurants = json.loads(request.body.decode()).get("restaurants", [])
            except Exception:
                restaurants = []

        if req_type != 'restaurant_list' or not isinstance(restaurants, list):
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='restaurant_list' 且包含 restaurants 清單"
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 預先定義語意補強規則
        user_input_rules = {
            # 🍃 飲食偏好
            "吃素": "素食需求",
            "素食": "素食需求",
            "怕辣": "避免辛辣料理",
            "不吃辣": "避免辛辣料理",
            "不想太油": "清爽口味",
            "清爽": "清爽口味",
            "太油": "清爽口味",
            "油膩": "清爽口味",

            # 👪 用餐場合
            "朋友聚餐": "適合朋友聚會",
            "同學聚餐": "適合朋友聚會",
            "聚餐": "適合聚餐",
            "家庭聚餐": "適合家庭聚會",
            "帶爸媽": "適合家庭聚會",
            "爸媽": "適合家庭聚會",
            "家人吃飯": "適合家庭聚會",
            "約會": "氣氛佳，適合約會",
            "商務": "適合正式聚會",
            "請客": "適合正式聚會",
            "正式": "適合正式聚會",
            "慶生": "適合慶祝場合",
            "生日": "適合慶祝場合",
            "慶祝": "適合慶祝場合",
            "小孩": "親子友善",
            "兒童": "親子友善",

            # 💰 預算
            "不貴": "價格實惠",
            "便宜": "價格實惠",
            "平價": "價格實惠",
            "價格實惠": "價格實惠",
            "高級": "精緻高價",
            "高價": "精緻高價",
            "高端": "精緻高價",
            "精緻": "精緻高價",

            # ⏰ 時段
            "宵夜": "適合宵夜",
            "深夜": "適合宵夜",
            "早午餐": "適合早午餐",
            "早餐": "適合早餐",

            # ⏱️ 狀態/時間
            "時間不多": "快速方便",
            "趕時間": "快速方便",
            "快速吃": "快速方便",

            # 🌶️ 重口味
            "想吃辣": "重口味料理",
            "重口味": "重口味料理",
            "辣的料理": "重口味料理",
            "麻辣": "重口味料理",
            "辣鍋": "重口味料理",
        }


        results = []

        for restaurant in restaurants:
            name = restaurant.get('name', '')
            rating = restaurant.get('rating', 0)
            address = restaurant.get('address', '')
            is_open_raw = restaurant.get('is_open', None)
            ai_reason = restaurant.get('ai_reason', '')
            comment_summary = restaurant.get('comment_summary', '')
            highlight = restaurant.get('highlight', '')
            matched_tags = restaurant.get('matched_tags', [])
            distance_m = restaurant.get('distance_m', None)
            distance = f"{distance_m} 公尺" if distance_m else "未知"
            reason_score = restaurant.get('reason_score', 0)
            price_level = restaurant.get('price_level', '')
            review_count = restaurant.get('review_count', None)

            # 共用欄位處理
            map_url = generate_map_url(name)
            is_open = format_open_status(is_open_raw)
            price_desc = generate_price_description(price_level)
            district = extract_district(address)

            # 主推薦理由來源
            reason_source = "inference"
            if ai_reason:
                core_reason = ai_reason
                reason_source = "ai"
            elif comment_summary:
                core_reason = comment_summary
                reason_source = "summary"
            else:
                core_reasons = []
                if rating >= 4.5:
                    core_reasons.append("評價很高")
                if "台北" in address or "新北" in address:
                    core_reasons.append("地點方便")
                if not core_reasons:
                    core_reasons.append("整體評價不錯")
                core_reason = "、".join(core_reasons)

            # 補強理由：基本
            extra_reasons = []
            if highlight:
                extra_reasons.append(highlight)
            if matched_tags:
                extra_reasons.extend(matched_tags)
            if price_desc:
                extra_reasons.append(price_desc)
            if district:
                extra_reasons.append(f"位於{district}")

            # features / style / hours
            features = restaurant.get("features", [])
            style = restaurant.get("style", "")
            opening_hours = restaurant.get("opening_hours", "")

            feature_map = {
                "甜點專門": "甜點評價高",
                "氣氛佳": "氣氛佳",
                "聚餐推薦": "適合聚餐",
                "高 CP 值": "高 CP 值",
                "價格便宜": "價格實惠",
                "價格親民": "價格實惠",
                "人氣餐廳": "熱門店家",
                "宵夜好選擇": "適合宵夜",
                "異國料理": "異國風味"
            }
            for f in features:
                if f in feature_map:
                    extra_reasons.append(feature_map[f])

            style_map = {
                "文青": "文青風格",
                "美式": "美式風格",
                "日式": "日式風格",
                "夜貓族": "適合夜貓子",
                "東南亞風": "東南亞風格"
            }
            if style in style_map:
                extra_reasons.append(style_map[style])

            if opening_hours:
                if "00" in opening_hours or "02" in opening_hours:
                    extra_reasons.append("夜間營業")
                if "23" in opening_hours or "22" in opening_hours:
                    extra_reasons.append("適合宵夜")
                if "全天" in opening_hours:
                    extra_reasons.append("全天營業")

            # ✅ ➕ user_input 語意補強
            if user_input:
                for keyword, reason in user_input_rules.items():
                    if keyword in user_input:
                        extra_reasons.append(reason)

            # 結構化推薦理由
            reason_summary = {
                "source": reason_source,
                "core": core_reason,
                "extra": extra_reasons
            }
            full_reason = "、".join([core_reason] + extra_reasons)

            results.append({
                "name": name,
                "address": address,
                "rating": rating,
                "price_level": price_level,
                "review_count": review_count,
                "highlight": highlight,
                "tags": list(set(matched_tags + extra_reasons)),
                "matched_tags": matched_tags,
                "is_open": is_open,
                "distance": distance,
                "reason_score": reason_score,
                "map_url": map_url,
                "reason_summary": reason_summary,
                "recommend_reason": full_reason
            })

        sorted_results = sorted(results, key=lambda x: (
            x.get('reason_score') or 0,
            x.get('rating') or 0,
            x.get('review_count') or 0
        ), reverse=True)

        return Response({
            "status": "success",
            "data": {
                "results": sorted_results
            },
            "message": "推薦理由已產生"
        }, status=status.HTTP_200_OK)
    

# 功能 3-1：模糊語句提示（最終優化版）
class GeneratePromptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get("type")
        user_input = request.data.get("text", "").strip()

        if req_type != "text" or not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='text' 且包含 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 模糊語句依照程度分類（可擴充）
        vague_patterns = {
            "vague": [
                "隨便", "你決定", "不知道", "不清楚", "沒意見", "沒想吃的", "不知道吃什麼", "不確定", "沒靈感", "隨你"
            ],
            "medium": [
                "都可以", "無所謂", "你看著辦", "你幫我選", "再說吧", "看心情", "看著辦", "可以啊都行", "沒關係"
            ],
            "slight": [
                "沒想法", "還沒想好", "沒特別想吃", "還不知道吃什麼", "需要想一下", "再看看", "再想想"
            ]
        }


        level = "clear"
        guidance = "歡迎告訴我們今天想吃什麼，或也可以提供不想吃的類型，我們會幫你挑選適合的餐廳！"

        # 遍歷所有模糊等級，依序比對
        for current_level, keywords in vague_patterns.items():
            if any(keyword in user_input for keyword in keywords):
                level = current_level
                if level == "slight":
                    guidance = "今天想吃點簡單的還是來點特別的呢？幾個方向幫你發想一下～"
                elif level == "medium":
                    guidance = "那你偏好什麼類型？或有不喜歡的料理嗎？我們可以幫你排除一部分喔！"
                elif level == "vague":
                    guidance = "可以先從『不想吃什麼』開始講起唷～像是不吃辣、不吃炸物之類的都可以說出來！"
                break

        return Response({
            "status": "success",
            "data": {
                "level": level,
                "guidance": guidance
            },
            "message": "模糊語句提示已產生"
        }, status=status.HTTP_200_OK)


# 功能 3-2：互動式語句引導建議（最終強化版2）

class SuggestInputGuidanceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get("type")
        user_input = request.data.get("text", "").lower().strip()

        if req_type != "text" or not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='text' 且包含 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        summary = []
        default_guidance = "您可以輸入想吃的類型、場合、預算等資訊，我們會給您更好的建議！"

        # ✅ 特殊處理：排除語句 + 特定料理
        exclusion_phrases = ['不想吃', '不吃', '不要']
        cuisine_phrases = ['甜點', '拉麵', '日式', '韓式', '中式', '義式', '義大利麵', '美式', '漢堡', '燒烤', '火鍋']
        if any(p in user_input for p in exclusion_phrases) and any(c in user_input for c in cuisine_phrases):
            summary.append({"type": "排除語句", "message": "已排除特定料理類型，可推薦其他選項"})

        # ✅ 通用語意分類規則
        rules = [
            ("飲食偏好", ['不吃辣', '怕辣', '我不吃辣'], '已排除辣味選項，推薦清爽、湯品等溫和口味'),
            ("飲食偏好", ['不吃牛', '我不吃牛'], '已排除牛肉餐點，可推薦雞肉、海鮮或蔬食'),
            ("飲食偏好", ['不吃海鮮', '海鮮過敏'], '已排除海鮮餐廳，推薦其他類型'),
            ("飲食偏好", ['吃素', '素食', '我吃素'], '已識別為素食需求，可推薦素食或蔬食友善餐廳'),

            ("用餐場合", ['朋友聚餐', '同學聚餐', '聚會'], '適合朋友聚會，可推薦平價熱鬧或多人套餐餐廳'),
            ("用餐場合", ['家庭聚餐', '家人吃飯', '家族聚餐', '爸媽'], '適合家庭用餐，建議選擇環境安靜、多樣菜色的餐廳'),
            ("用餐場合", ['約會'], '氣氛佳的推薦適合約會，可考慮咖啡廳或裝潢溫馨的餐廳'),
            ("用餐場合", ['商務', '請客', '正式'], '推薦穩重氣氛與高評價的餐廳，適合正式或商務用途'),
            ("用餐場合", ['慶生', '生日', '慶祝'], '推薦氣氛佳、有蛋糕或包廂的餐廳，適合慶祝場合'),
            ("用餐場合", ['小孩', '小朋友', '帶孩子', '兒童'], '適合親子用餐，建議考慮有兒童餐或寬敞空間的店家'),
            ("用餐場合", ['長輩', '父母', '家人一起吃'], '建議選擇環境安靜、餐點清淡的家庭友善餐廳'),

            ("預算", ['不貴', '便宜', '平價', '價格實惠'], '偏好不貴的餐廳，可以優先查看平價高評價選項'),
            ("預算", ['高級', '高價', '精致', '高端'], '偏好精緻體驗，可推薦高評價或高端餐廳'),

            ("時段", ['宵夜', '深夜'], '推薦宵夜時段營業中的輕食、炸物或拉麵等店家'),
            ("時段", ['早午餐'], '可推薦氣氛佳、評價高的早午餐店'),
            ("時段", ['早餐'], '推薦營業中的中西式早餐選項'),

            ("料理類型", ['甜點'], '推薦甜點評價高的餐廳或咖啡廳'),
            ("料理類型", ['拉麵', '日式'], '可推薦高分日式餐廳與拉麵名店'),
            ("料理類型", ['韓式'], '推薦高人氣韓式料理'),
            ("料理類型", ['中式'], '中式餐廳選擇豐富，推薦合菜或便當型店家'),
            ("料理類型", ['義式', '義大利麵'], '可推薦義式料理與義大利麵專門店'),
            ("料理類型", ['美式', '漢堡'], '推薦高評價美式漢堡或炸物餐廳'),

            ("飲食狀態", ['吃不多', '吃少一點', '簡單吃', '輕食'], '推薦輕食類型如三明治、沙拉或早午餐'),
            ("飲食狀態", ['趕時間', '快速吃', '時間不多'], '推薦供餐快速或外帶方便的選項'),
            ("飲食狀態", ['天氣冷', '想吃熱的', '暖胃'], '推薦湯品、火鍋或熱炒等溫暖料理'),
            ("飲食狀態", ['想吃辣', '重口味', '辣的料理', '麻辣', '辣鍋'], '適合重口味愛好者，推薦麻辣火鍋、川菜或韓式辣炒等餐廳'),
            ("飲食狀態", ['清淡', '不想太油', '吃清爽的'], '推薦清爽或湯品類型，適合口味較淡的需求'),
        ]

        for category, keywords, response_text in rules:
            if any(keyword in user_input for keyword in keywords):
                summary.append({"type": category, "message": response_text})

        if not summary:
            summary.append({"type": "其他", "message": default_guidance})

        guidance_combined = "；".join([item["message"] for item in summary])
        levels = list({item["type"] for item in summary})  # 去重類別

        return Response({
            "status": "success",
            "data": {
                "summary": summary,
                "guidance": guidance_combined,
                "level": levels
            },
            "message": "已產生語意引導建議"
        }, status=status.HTTP_200_OK)



# 功能 4：推薦卡片欄位模擬輸出(強化版)
class GenerateCardDataView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # ✅ 保險處理：兼容 DRF Request 和 WSGIRequest（整合測試用）
        if hasattr(request, 'data'):
            req_type = request.data.get('type')
            restaurants = request.data.get('restaurants', [])
        else:
            req_type = request.POST.get('type')
            try:
                restaurants = json.loads(request.body.decode()).get("restaurants", [])
            except Exception:
                restaurants = []

        if req_type != 'restaurant_list' or not isinstance(restaurants, list):
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='restaurant_list' 且包含 restaurants 清單"
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []

        for restaurant in restaurants:
            name = restaurant.get('name', '')
            rating = restaurant.get('rating', 0)
            address = restaurant.get('address', '')
            price_level = restaurant.get('price_level', '')
            review_count = restaurant.get('review_count', 0)
            is_open_raw = restaurant.get('is_open', None)
            matched_tags = restaurant.get('matched_tags', [])
            ai_reason = restaurant.get('ai_reason', '')
            highlight = restaurant.get('highlight', '')
            distance_m = restaurant.get('distance_m', random.randint(100, 2000))
            distance = f"{distance_m} 公尺"

            # 共用處理邏輯
            map_url = generate_map_url(name)
            is_open = format_open_status(is_open_raw)
            district = extract_district(address)
            price_desc = generate_price_description(price_level)

            # 組合 tags
            tags = list(set(matched_tags + ([district] if district else []) + ([price_desc] if price_desc else [])))

            # highlight 補強
            if not highlight:
                if "甜點" in tags or "蛋糕" in name:
                    highlight = "甜點評價高"
                elif rating >= 4.5:
                    highlight = "評價優良"
                elif district and name not in ["泰式小館"]:
                    highlight = "地點便利"
                else:
                    highlight = ""

            # 推薦理由
            recommend_reason = generate_recommend_reason(matched_tags, highlight, district, price_desc)

            # 模擬 features（邏輯擴充）
            features = []
            if "素食" in tags:
                features.append("提供素食")
            if price_desc == "價格實惠":
                features.append("高 CP 值")
            if "甜點" in tags or "蛋糕" in name:
                features.append("甜點專門")
            if rating >= 4.5 and review_count >= 300:
                features.append("人氣餐廳")
            if price_level == "$":
                features.append("價格便宜")
            if "異國料理" in tags or "泰式" in name:
                features.append("異國料理")

            # 模擬 style（先處理夜貓，再看其他）
            style = ""
            if "泰式" in name or "東南亞" in tags:
                style = "東南亞風"
            elif "夜貓族" in tags or "夜貓" in name or "宵夜" in tags or distance_m > 1500:
                style = "夜貓族"
            elif "文青" in name or "咖啡" in name or "甜點" in tags:
                style = "文青"
            elif "燒肉" in name or "烤肉" in tags:
                style = "美式"
            elif "壽司" in name or "日式" in tags or "拉麵" in name:
                style = "日式"

            # 模擬營業時間與預留欄位
            opening_hours = "11:00 - 21:00"
            has_coupon = False
            image_url = ""

            results.append({
                "name": name,
                "rating": rating,
                "address": address,
                "tags": tags,
                "highlight": highlight,
                "distance": distance,
                "distance_m": distance_m,
                "review_count": review_count,
                "price_level": price_level,
                "is_open": is_open,
                "map_url": map_url,
                "features": features,
                "style": style,
                "opening_hours": opening_hours,
                "recommend_reason": recommend_reason,
                "has_coupon": has_coupon,
                "image_url": image_url
            })

        return Response({
            "status": "success",
            "data": {
                "results": results
            },
            "message": "卡片欄位資料已產生"
        }, status=status.HTTP_200_OK)


# ✅ 整合測試：功能一 → 四 → 二（修正版）

class IntegrationTestView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]  # ✅ 支援 application/json

    def post(self, request):
        from .sample_data import RESTAURANTS_SAMPLE
        from .views import ExtractNegativeConditionsView, GenerateCardDataView, GenerateRecommendReasonView

        factory = APIRequestFactory()
        input_text = request.data.get("text", "").strip()

        if not input_text:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        print("\n🎯 整合測試開始 >>>")
        print(f"📝 使用者輸入：{input_text}")

        # ✅ Step 1：功能一（排除條件擷取）
        request_exclusion = factory.post("/fake_path/", {
            "text": input_text
        }, format='json')
        wrapped_request = Request(request_exclusion, parsers=[JSONParser()])  # ✅ 加上 parsers
        exclusion_response = ExtractNegativeConditionsView().post(wrapped_request)

        if hasattr(exclusion_response, "data") and isinstance(exclusion_response.data, dict):
            exclusion_data_raw = exclusion_response.data
        elif hasattr(exclusion_response, "_data") and isinstance(exclusion_response._data, dict):
            exclusion_data_raw = exclusion_response._data
        else:
            exclusion_data_raw = {}

        excluded_items = []
        if isinstance(exclusion_data_raw, dict):
            data_field = exclusion_data_raw.get("data", {})
            if isinstance(data_field, dict):
                excluded_items = data_field.get("excluded", [])

        print(f"🚫 排除項目：{excluded_items}")

        # ✅ Step 2：過濾掉排除的餐廳
        filtered = []
        for r in RESTAURANTS_SAMPLE:
            name = r.get("name", "")
            tags = r.get("matched_tags", [])
            if any(ex in name for ex in excluded_items):
                continue
            if any(ex in tag for ex in excluded_items for tag in tags):
                continue
            filtered.append(r)

        print(f"✅ 通過排除篩選的餐廳數：{len(filtered)}")

        # ✅ Step 3：功能四（欄位補強）
        request_card_data = factory.post("/fake_path/", {
            "type": "restaurant_list",
            "restaurants": filtered
        }, format='json')
        wrapped_card_request = Request(request_card_data, parsers=[JSONParser()])  # ✅ 加上 parsers
        card_data_response = GenerateCardDataView().post(wrapped_card_request)

        if hasattr(card_data_response, "data") and isinstance(card_data_response.data, dict):
            card_data_raw = card_data_response.data
        elif hasattr(card_data_response, "_data") and isinstance(card_data_response._data, dict):
            card_data_raw = card_data_response._data
        else:
            card_data_raw = {}

        card_restaurants = card_data_raw.get("data", {}).get("results", [])
        print(f"📦 補完欄位的餐廳數：{len(card_restaurants)}")

        # ✅ Step 4：功能二（推薦理由補強）
        request_reason = factory.post("/fake_path/", {
            "type": "restaurant_list",
            "restaurants": card_restaurants,
            "user_input": input_text  # ✅ 傳入使用者輸入文字
        }, format='json')
        wrapped_reason_request = Request(request_reason, parsers=[JSONParser()])  # ✅ 加上 parsers
        final_response = GenerateRecommendReasonView().post(wrapped_reason_request)

        if hasattr(final_response, "data") and isinstance(final_response.data, dict):
            final_data_raw = final_response.data
        elif hasattr(final_response, "_data") and isinstance(final_response._data, dict):
            final_data_raw = final_response._data
        else:
            final_data_raw = {}

        final_results = final_data_raw.get("data", {})
        print(f"🌟 最終推薦結果筆數：{len(final_results) if isinstance(final_results, list) else '未知'}")

        return Response({
            "status": "success",
            "data": final_results,
            "message": "整合流程已執行完成"
        }, status=status.HTTP_200_OK)



