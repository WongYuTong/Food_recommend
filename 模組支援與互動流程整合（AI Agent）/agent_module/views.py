from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status


# 功能 1：反向推薦條件擷取
class ExtractNegativeConditionsView(APIView):
    permission_classes = [AllowAny]  # ✅ 測試期間開放所有人使用

    def post(self, request):
        user_input = request.data.get('text', '')

        # 正規表達式來找出負向條件
        negative_patterns = [
            r'不想吃(\w+)',
            r'不想要(\w+)',
            r'不要(\w+)',
            r'不吃(\w+)',
            r'別推薦(\w+)',
        ]

        excluded_items = []
        for pattern in negative_patterns:
            matches = re.findall(pattern, user_input)
            excluded_items.extend(matches)

        return Response({'excluded': excluded_items})



# 功能 2：推薦理由補強
class GenerateRecommendReasonView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        restaurants = request.data.get('restaurants', [])
        results = []

        for restaurant in restaurants:
            name = restaurant.get('name', '')
            rating = restaurant.get('rating', 0)
            address = restaurant.get('address', '')

            reasons = []
            if rating >= 4.5:
                reasons.append("評價很高")
            if "台北" in address:
                reasons.append("地點方便")
            if not reasons:
                reasons.append("整體評價不錯")

            results.append({
                "name": name,
                "reason": "、".join(reasons)
            })

        return Response({"results": results})
