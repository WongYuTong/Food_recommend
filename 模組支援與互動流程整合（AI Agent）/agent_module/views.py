from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
import random


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

# 功能 1：反向推薦條件擷取（強化版）
class ExtractNegativeConditionsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get('text', '')

        negative_patterns = [
            r'不想吃(.+?)(?:[，。!！,\.]|$)',
            r'不想要(.+?)(?:[，。!！,\.]|$)',
            r'不要(.+?)(?:[，。!！,\.]|$)',
            r'不吃(.+?)(?:[，。!！,\.]|$)',
            r'別推薦(.+?)(?:[，。!！,\.]|$)',
        ]

        excluded_items = []
        for pattern in negative_patterns:
            matches = re.findall(pattern, user_input)
            for match in matches:
                # 這裡是加強版：能抓「甜點、義大利麵」中兩個詞
                split_items = re.split(r'[,、，和跟以及或還有\s]+', match)
                excluded_items.extend([item.strip() for item in split_items if item.strip()])

        # 去除重複與空白
        unique_excluded = list(set(excluded_items))

        # ✅ 可選：只保留已知分類（未來接資料庫可開啟）
        # known_categories = {"火鍋", "甜點", "壽司", "牛排", "燒烤", "義大利麵", "拉麵", "飲料"}
        # unique_excluded = [item for item in unique_excluded if item in known_categories]

        return Response({'excluded': unique_excluded})

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
            reason_score = restaurant.get('reason_score', None)
            price_level = restaurant.get('price_level', '')

            # 1. 營業狀態文字化
            if isinstance(is_open_raw, bool):
                is_open = "營業中" if is_open_raw else "休息中"
            elif isinstance(is_open_raw, str):
                is_open = is_open_raw
            else:
                is_open = "無資料"

            # 2. 主推薦理由
            reason_source = "inference"
            core_reason = ""

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

            # 3. 補強 extra 理由（標籤、highlight、價格、地點）
            extra_reasons = []

            if highlight:
                extra_reasons.append(highlight)
            if matched_tags:
                extra_reasons.extend(matched_tags)

            # 補強價格
            if price_level == "$":
                extra_reasons.append("價格實惠")
            elif price_level == "$$":
                extra_reasons.append("價格中等")
            elif price_level == "$$$":
                extra_reasons.append("偏高價位")

            # 補強地區名稱（簡易從地址擷取）
            district_match = re.search(r'(台北市|新北市)?(\w{2,3}區)', address)
            if district_match:
                district = district_match.group(2)
                extra_reasons.append(f"位於{district}")

            # 4. 結構化推薦理由
            reason_summary = {
                "source": reason_source,
                "core": core_reason,
                "extra": extra_reasons
            }

            # 5. 合併成一行文字（給前端顯示用）
            full_reason = "、".join([core_reason] + extra_reasons)

            results.append({
                "name": name,
                "address": address,
                "is_open": is_open,
                "rating": rating,
                "reason": full_reason,
                "reason_summary": reason_summary,
                "distance": distance,
                "reason_score": reason_score,
                "highlight": highlight,
                "matched_tags": matched_tags,
                "price_level": price_level
            })

        return Response({"results": results})


# 功能 3（優化版）：模糊語句提示
class GeneratePromptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get("input", "").strip()

        # 常見模糊語句組
        vague_keywords = {
            "輕微": ["沒想法", "還沒想好", "沒特別想吃"],
            "中等": ["無所謂", "都可以", "都行", "看著辦", "再說吧"],
            "明確": ["隨便", "你決定", "你幫我選", "看你", "不知道", "沒意見"],
        }

        prompt = "你有想吃的類型嗎？或是有不想吃的？"

        for level, phrases in vague_keywords.items():
            if any(p in user_input for p in phrases):
                if level == "輕微":
                    prompt = "可以想一下今天有沒有想吃的方向，像是簡單吃或想吃特別的？"
                elif level == "中等":
                    prompt = "那你偏好什麼類型呢？或是有不想吃的東西嗎？"
                else:  # 明確模糊
                    prompt = "你有不喜歡吃的嗎？像是不吃辣、不吃牛？我們可以幫你排除～"
                break

        return Response({"prompt": prompt}, status=status.HTTP_200_OK)


# 功能 3-2：互動式語句引導建議（優化版）
class SuggestInputGuidanceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get('text', '')
        suggestion = '您可以輸入想吃的類型、場合、預算等資訊，我們會給您更好的建議！'

        rules = [
            (['不想吃', '不要', '不吃'], '已偵測到排除類型，可以幫您濾除不想吃的餐廳'),
            (['不想吃火鍋', '不要火鍋'], '已排除火鍋類型，可考慮中式或日式餐廳'),
            (['不吃辣', '怕辣'], '已排除辣味餐廳，推薦清爽或湯品類型'),
            (['不吃牛'], '會幫您排除牛肉相關選項'),
            (['吃素'], '已識別為素食需求，可推薦素食或蔬食友善餐廳'),

            (['約會'], '氣氛佳的推薦適合約會，可考慮咖啡廳或裝潢溫馨的餐廳'),
            (['家庭聚餐'], '適合多人用餐，可考慮寬敞空間與多樣菜色的選擇'),
            (['朋友聚餐'], '適合朋友聚會，可推薦平價熱鬧或多人套餐餐廳'),

            (['不貴', '便宜', '小資'], '偏好不貴的餐廳，可以優先查看平價高評價選項'),
            (['高級', '精緻', '高價'], '偏好精緻體驗，可推薦高評價或高端餐廳'),

            (['宵夜'], '深夜推薦營業中的輕食、炸物或拉麵等店家'),
            (['早午餐'], '可推薦氣氛佳、評價高的早午餐店'),
            (['下午茶'], '可考慮甜點或咖啡廳，有悠閒空間與高評價餐點'),
        ]

        for keywords, response in rules:
            if any(k in user_input for k in keywords):
                suggestion = response
                break

        return Response({'guidance': suggestion}, status=status.HTTP_200_OK)



# 功能 4：推薦卡片欄位模擬輸出
class GenerateCardDataView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        restaurants = request.data.get('restaurants', [])
        results = []

        for r in restaurants:
            name = r.get('name', '')
            rating = r.get('rating', 0)
            address = r.get('address', '')

            tags = []
            if "燒肉" in name or "燒肉" in address:
                tags.append("燒肉")
            if rating >= 4.5:
                tags.append("高評價")
            if "台北" in address:
                tags.append("地點佳")

            highlight = "甜點評價高" if "甜" in name else "交通方便"
            distance = "800 公尺"  # 假資料，之後可由爬蟲或地圖服務提供

            results.append({
                "name": name,
                "rating": rating,
                "address": address,
                "tags": tags,
                "highlight": highlight,
                "distance": distance,
                "reason": "、".join(tags + [highlight])
            })

        return Response({"results": results})
