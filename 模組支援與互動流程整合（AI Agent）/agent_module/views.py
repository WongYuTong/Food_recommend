from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
import random


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status


# 功能 1：反向推薦條件擷取（優化版）
class ExtractNegativeConditionsView(APIView):
    permission_classes = [AllowAny]  # ✅ 測試期間開放所有人使用

    def post(self, request):
        user_input = request.data.get('text', '')

        # 支援多個句尾標點
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
                # 將 "和"、"跟"、"或"、"以及"、"、" 等連接詞切開
                split_items = re.split(r'[、和跟以及或]', match)
                excluded_items.extend([item.strip() for item in split_items if item.strip()])

        return Response({'excluded': excluded_items})

# 功能 2：推薦理由補強 + 結構化輸出
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

            # 將布林值 is_open 轉為顯示用文字
            if isinstance(is_open_raw, bool):
                is_open = "營業中" if is_open_raw else "休息中"
            elif isinstance(is_open_raw, str):
                is_open = is_open_raw  # 若已是字串則保留
            else:
                is_open = "無資料"

            # 推薦理由主句
            if ai_reason:
                reason = ai_reason
            elif comment_summary:
                reason = comment_summary
            else:
                reasons = []
                if rating >= 4.5:
                    reasons.append("評價很高")
                if "台北" in address:
                    reasons.append("地點方便")
                if not reasons:
                    reasons.append("整體評價不錯")
                reason = "、".join(reasons)

            # 補強內容
            extra = []
            if highlight:
                extra.append(highlight)
            if matched_tags:
                extra.extend(matched_tags)

            full_reason = "、".join([reason] + extra)

            results.append({
                "name": name,
                "address": address,
                "is_open": is_open,
                "rating": rating,
                "reason": full_reason,
                "distance": distance,
                "reason_score": reason_score,
                "highlight": highlight,
                "matched_tags": matched_tags,
            })

        return Response({"results": results})

# 功能 3：模糊語句提示
class GeneratePromptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get("input", "").strip()
        vague_keywords = {"隨便", "都可以", "沒意見", "看你", "不知道", "你決定"}
        prompt = "你有想吃的類型嗎？或是有不想吃的？"

        if any(keyword in user_input for keyword in vague_keywords):
            prompt = "你有不喜歡吃的東西嗎？像是不吃辣、不吃牛？"

        return Response({"prompt": prompt}, status=status.HTTP_200_OK)


# 功能 3-2：互動式語句引導建議
class SuggestInputGuidanceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get('text', '')
        suggestion = '您可以輸入想吃的類型、場合、預算等資訊，我們會給您更好的建議！'

        rules = [
            (['不想吃火鍋', '不要火鍋'], '已排除火鍋類型，可考慮中式或日式餐廳'),
            (['約會'], '氣氛佳的推薦適合約會，可考慮咖啡廳或裝潢溫馨的餐廳'),
            (['不貴', '便宜'], '偏好不貴的餐廳，可以優先查看平價高評價選項'),
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
