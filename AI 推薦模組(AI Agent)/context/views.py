from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from utils.chat_view import get_current_context_info
from utils.emotion_parser import parse_emotion_from_text
from context.restaurant_controller import RestaurantRecommendationController

@csrf_exempt
@require_POST
def recommend_restaurant(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
        user_location = data.get("location", {})

        # 取得當前情境（時段、平日/週末/節日）
        context_info = get_current_context_info()

        # 解析使用者輸入情緒
        detected_emotions = parse_emotion_from_text(user_message)

        # 初始化推薦控制器
        controller = RestaurantRecommendationController()

        # 執行推薦（請確保 controller 支援 context, emotions 參數）
        response = controller.process_query(
            query_text=user_message,
            user_location=user_location,
            context=context_info,
            emotions=detected_emotions
        )

        # 回傳結果
        return JsonResponse({
            "status": "success",
            "context_info": context_info,
            "detected_emotions": detected_emotions,
            "recommendation": response
        })

    except Exception as e:
        print(f"推薦餐廳發生錯誤：{str(e)}")
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)