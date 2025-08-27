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


# 功能 2：推薦理由補強 + 結構化輸出（優化版）
class GenerateRecommendReasonView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        restaurants = request.data.get('restaurants', [])
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
            distance = restaurant.get('distance', '未知')
            reason_score = restaurant.get('reason_score', 0)
            price_level = restaurant.get('price_level', '')
            review_count = restaurant.get('review_count', None)

            # 建立地圖搜尋連結
            map_url = f"https://www.google.com/maps/search/{name}"

            # 1. 營業狀態轉文字
            if isinstance(is_open_raw, bool):
                is_open = "營業中" if is_open_raw else "休息中"
            elif isinstance(is_open_raw, str):
                is_open = is_open_raw
            else:
                is_open = "無資料"

            # 2. 主理由來源與內容
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
                if "台北" in address:
                    core_reasons.append("地點方便")
                if not core_reasons:
                    core_reasons.append("整體評價不錯")
                core_reason = "、".join(core_reasons)

            # 3. 補強 extra
            extra_reasons = []
            if highlight:
                extra_reasons.append(highlight)
            if matched_tags:
                extra_reasons.extend(matched_tags)

            # 價格補強
            price_desc = {
                "$": "價格實惠",
                "$$": "價格中等",
                "$$$": "偏高價位"
            }.get(price_level)
            if price_desc:
                extra_reasons.append(price_desc)

            # 區域補強（地址擷取）
            district_match = re.search(r'(台北市|新北市)?(\w{2,3}區)', address)
            if district_match:
                extra_reasons.append(f"位於{district_match.group(2)}")

            # 4. 結構化理由
            reason_summary = {
                "source": reason_source,
                "core": core_reason,
                "extra": extra_reasons
            }

            # 5. 合併成單行說明
            full_reason = "、".join([core_reason] + extra_reasons)

            results.append({
                "name": name,
                "address": address,
                "rating": rating,
                "price_level": price_level,
                "review_count": review_count,
                "highlight": highlight,
                "matched_tags": matched_tags,
                "is_open": is_open,
                "distance": distance,
                "reason_score": reason_score,
                "map_url": map_url,
                "reason_summary": reason_summary,
                "recommend_reason": full_reason
            })

        # 排序：先用 reason_score，其次 rating，再來 review_count
        sorted_results = sorted(results, key=lambda x: (
            x.get('reason_score') if x.get('reason_score') is not None else 0,
            x.get('rating') if x.get('rating') is not None else 0,
            x.get('review_count') if x.get('review_count') is not None else 0
        ), reverse=True)

        return Response({"results": sorted_results})


# 功能 3：模糊語句提示（進階優化版）
class GeneratePromptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get("input", "").strip()

        vague_keywords = {
            "輕微": [
                "沒想法", "還沒想好", "沒特別想吃", "還不知道吃什麼", "需要想一下", "再看看"
            ],
            "中等": [
                "都可以", "無所謂", "你看著辦", "你幫我選", "再說吧", "看心情", "看著辦"
            ],
            "明確": [
                "隨便", "你決定", "不知道", "沒意見", "不知道吃什麼", "不清楚", "沒想吃的"
            ]
        }

        # 預設提示語
        level = "無"
        prompt = "有特別想吃的嗎？也可以說說你不想吃的類型，我們來幫你挑～"

        # 判斷模糊程度
        for current_level, keywords in vague_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                level = current_level
                if current_level == "輕微":
                    prompt = "想一下今天是想吃簡單一點的，還是想來點特別的呢？"
                elif current_level == "中等":
                    prompt = "那你偏好什麼類型呢？或是有不喜歡吃的料理？我們可以先排除看看！"
                elif current_level == "明確":
                    prompt = "沒問題！先從排除不愛吃的類型開始吧～像是不吃辣、不吃炸物這些都可以說唷！"
                break

        return Response({
            "level": level,
            "prompt": prompt
        }, status=status.HTTP_200_OK)


# 功能 3-2：互動式語句引導建議（最終強化版2）

class SuggestInputGuidanceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get("text", "").lower().strip()

        default_guidance = "您可以輸入想吃的類型、場合、預算等資訊，我們會給您更好的建議！"
        guidance = default_guidance
        level = "其他"

        # 特殊處理：同時命中 排除語句 + 料理類型 才視為「排除語句」
        exclusion_phrases = ['不想吃', '不吃', '不要']
        cuisine_phrases = ['甜點', '拉麵', '日式', '韓式', '中式', '義式', '義大利麵', '美式', '漢堡', '燒烤', '火鍋']

        if any(p in user_input for p in exclusion_phrases) and any(c in user_input for c in cuisine_phrases):
            guidance = "已排除特定料理類型，可推薦其他選項"
            level = "排除語句"
        else:
            rules = [
                ("飲食偏好", ['不吃辣', '怕辣', '我不吃辣'], '已排除辣味選項，推薦清爽、湯品等溫和口味'),
                ("飲食偏好", ['不吃牛', '我不吃牛'], '已排除牛肉餐點，可推薦雞肉、海鮮或蔬食'),
                ("飲食偏好", ['不吃海鮮', '海鮮過敏'], '已排除海鮮餐廳，推薦其他類型'),
                ("飲食偏好", ['吃素', '素食', '我吃素'], '已識別為素食需求，可推薦素食或蔬食友善餐廳'),

                ("用餐場合", ['朋友聚餐', '同學聚餐', '聚會'], '適合朋友聚會，可推薦平價熱鬧或多人套餐餐廳'),
                ("用餐場合", ['家庭聚餐', '家人吃飯', '家族聚餐'], '適合多人用餐，可考慮寬敞空間與多樣菜色的選擇'),
                ("用餐場合", ['約會'], '氣氛佳的推薦適合約會，可考慮咖啡廳或裝潢溫馨的餐廳'),
                ("用餐場合", ['商務', '請客', '正式'], '推薦穩重氣氛與高評價的餐廳，適合正式或商務用途'),
                ("用餐場合", ['慶生', '生日', '慶祝'], '推薦氣氛佳、有蛋糕或包廂的餐廳，適合慶祝場合'),
                ("用餐場合", ['小孩', '小朋友', '帶孩子', '兒童'], '適合親子用餐，建議考慮有兒童餐或寬敞空間的店家'),
                ("用餐場合", ['長輩', '父母', '家人一起吃'], '建議選擇環境安靜、餐點清淡的家庭友善餐廳'),

                ("預算", ['不貴', '便宜', '平價'], '偏好不貴的餐廳，可以優先查看平價高評價選項'),
                ("預算", ['高級', '高價', '精緻', '高端'], '偏好精緻體驗，可推薦高評價或高端餐廳'),

                ("時段", ['宵夜', '深夜'], '深夜推薦營業中的輕食、炸物或拉麵等店家'),
                ("時段", ['早午餐'], '可推薦氣氛佳、評價高的早午餐店'),
                ("時段", ['早餐'], '推薦營業中的中西式早餐選項'),

                ("料理類型", ['甜點'], '推薦甜點評價高的餐廳或咖啡廳'),
                ("料理類型", ['拉麵', '日式'], '可推薦高分日式餐廳與拉麵名店'),
                ("料理類型", ['韓式'], '推薦高人氣韓式料理'),
                ("料理類型", ['中式'], '中式餐廳選擇豐富，推薦合菜或便當型店家'),
                ("料理類型", ['義式', '義大利麵'], '可推薦義式料理與義大利麵專門店'),
                ("料理類型", ['美式', '漢堡'], '推薦高評價美式漢堡或炸物餐廳'),

                ("飲食狀態", ['吃不多', '吃少一點', '簡單吃'], '推薦輕食類型如三明治、沙拉或早午餐'),
                ("飲食狀態", ['趕時間', '快速吃', '時間不多'], '推薦供餐快速或外帶方便的選項'),
                ("飲食狀態", ['天氣冷', '想吃熱的', '暖胃'], '推薦湯品、火鍋或熱炒等溫暖料理'),
                ("飲食狀態", ['想吃辣', '重口味', '辣的料理'], '推薦麻辣火鍋、川菜或韓式辣炒等餐廳'),
                ("飲食狀態", ['清淡', '不想太油', '吃清爽的'], '推薦清爽或湯品類型，適合口味較淡的需求'),
            ]

            for category, keywords, response_text in rules:
                if any(keyword in user_input for keyword in keywords):
                    guidance = response_text
                    level = category
                    break

        return Response({"guidance": guidance, "level": level}, status=200)



# 功能 4：推薦卡片欄位模擬輸出（進階版）
class GenerateCardDataView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        restaurants = request.data.get("restaurants", [])
        results = []

        for r in restaurants:
            name = r.get("name", "")
            rating = r.get("rating", 0)
            address = r.get("address", "")

            # --- 模擬欄位 ---
            review_count = random.randint(50, 500)
            price_level_num = random.choice([1, 2, 3])
            is_open = random.choice([True, False])
            distance_m = random.randint(300, 1200)
            opening_hours = f"{random.choice(['10:00', '11:00'])} - {random.choice(['20:00', '21:00', '22:00'])}"

            # --- 標籤 ---
            tags = []
            if "燒肉" in name or "燒肉" in address:
                tags.append("燒肉")
            if "甜" in name or "甜點" in name:
                tags.append("甜點")
            if "素" in name:
                tags.append("素食")
            if "漢堡" in name:
                tags.append("漢堡")
            if "拉麵" in name or "拉麵" in address:
                tags.append("拉麵")
            if "咖啡" in name or "咖啡廳" in name:
                tags.append("咖啡廳")
            if "牛肉" in name:
                tags.append("牛肉")

            # 地區標籤
            district_match = re.search(r"(台北市|新北市|台中市|桃園市)?([^\d\s區]+區)", address)
            if district_match:
                tags.append(district_match.group(2))

            if rating >= 4.5:
                tags.append("高評價")

            # --- 亮點 ---
            if "甜點" in tags:
                highlight = "甜點評價高"
            elif rating >= 4.5:
                highlight = "Google 評價 4.5 分以上"
            else:
                highlight = "地點便利"

            # --- 推薦理由 ---
            reason = "、".join(tags + [highlight])

            # --- 額外欄位 ---
            features = []
            if "素食" in tags:
                features.append("蔬食友善")
            if price_level_num == 1:
                features.append("平價實惠")
            elif price_level_num == 3:
                features.append("高端體驗")
            if review_count > 300:
                features.append("人氣店家")

            # --- 樣式分類（多重判斷）---
            style = []
            if "咖啡廳" in tags or "甜點" in tags:
                style.append("文青")
            if "燒肉" in tags or "漢堡" in tags:
                style.append("美式")
            if "拉麵" in tags:
                style.append("日式")
            if "牛肉" in tags or "傳統" in name:
                style.append("傳統")
            if "宵夜" in name or "晚上" in opening_hours:
                style.append("夜貓族")

            result = {
                "name": name,
                "rating": rating,
                "address": address,
                "tags": tags,
                "highlight": highlight,
                "distance": f"{distance_m} 公尺",
                "distance_m": distance_m,
                "reason": reason,
                "review_count": review_count,
                "price_level": "$" * price_level_num,
                "is_open": is_open,
                "opening_hours": opening_hours,
                "map_url": f"https://www.google.com/maps/search/{name}",
                "features": features,
                "style": style,
            }
            results.append(result)

        return Response({"results": results})


