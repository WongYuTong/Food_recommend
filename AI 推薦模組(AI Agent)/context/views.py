from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
from utils.chat_view import get_current_context_info  # 情境
from utils.emotion_parser import parse_emotion_from_text  # 情緒
from utils.preference_parser import parse_preference_from_text  # 個人偏好
from context.restaurant_controller import RestaurantRecommendationController
from context.models import UserPreference
from django.contrib.auth.models import User

@csrf_exempt
@require_POST
def recommend_restaurant(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
        user_location = data.get("location", {})
        user_id = data.get("user_id", None)

        context_info = get_current_context_info()
        detected_emotions = parse_emotion_from_text(user_message)
        user_preferences = {}

        if user_id and User.objects.filter(id=user_id).exists():
            user_pref_obj = UserPreference.objects.filter(user_id=user_id).first()
            if user_pref_obj:
                try:
                    user_preferences = json.loads(user_pref_obj.preferences)
                except Exception:
                    user_preferences = {}

        parsed_preferences = parse_preference_from_text(user_message)
        if parsed_preferences and parsed_preferences != ["無特別偏好"] and user_id and User.objects.filter(id=user_id).exists():
            UserPreference.objects.update_or_create(
                user_id=user_id,
                defaults={"preferences": json.dumps(parsed_preferences, ensure_ascii=False)}
            )
            user_preferences = parsed_preferences

        controller = RestaurantRecommendationController()
        response = controller.process_query(
            query_text=user_message,
            user_location=user_location,
            context=context_info,
            emotions=detected_emotions,
            preferences=user_preferences
        )

        return JsonResponse({
            "status": "success",
            "data": {
                "context_info": context_info,
                "detected_emotions": detected_emotions,
                "user_preferences": user_preferences,
                "recommendation": response
            }
        })

    except Exception as e:
        print(f"推薦餐廳發生錯誤：{str(e)}")
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

@csrf_exempt
@require_POST
def save_user_preference(request):
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
        preferences_text = data.get("preferences")

        if not user_id or preferences_text is None:
            return JsonResponse({"status": "error", "message": "缺少 user_id 或 preferences"}, status=400)

        if not User.objects.filter(id=user_id).exists():
            return JsonResponse({"status": "error", "message": "使用者不存在"}, status=404)

        parsed_preferences = parse_preference_from_text(preferences_text)
        if not parsed_preferences:
            parsed_preferences = {"提示": "未偵測到明確偏好"}

        UserPreference.objects.update_or_create(
            user_id=user_id,
            defaults={"preferences": json.dumps(parsed_preferences, ensure_ascii=False)}
        )

        return JsonResponse({"status": "success", "message": "偏好已儲存", "parsed_preferences": parsed_preferences})
    except Exception as e:
        print(f"儲存使用者偏好錯誤：{str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_GET
def get_user_preference(request):
    try:
        user_id = request.GET.get("user_id")
        if not user_id:
            return JsonResponse({"status": "error", "message": "缺少 user_id"}, status=400)

        if not User.objects.filter(id=user_id).exists():
            return JsonResponse({"status": "error", "message": "使用者不存在"}, status=404)

        user_pref_obj = UserPreference.objects.filter(user_id=user_id).first()
        preferences = {}

        if user_pref_obj:
            try:
                preferences = json.loads(user_pref_obj.preferences)
            except Exception:
                preferences = {}

        return JsonResponse({"status": "success", "preferences": preferences})

    except Exception as e:
        print(f"讀取使用者偏好錯誤：{str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_POST
def delete_user_preference_item(request):
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
        item_to_delete = data.get("item")

        if not user_id or not item_to_delete:
            return JsonResponse({"status": "error", "message": "缺少 user_id 或 item"}, status=400)

        if not User.objects.filter(id=user_id).exists():
            return JsonResponse({"status": "error", "message": "使用者不存在"}, status=404)

        user_pref_obj = UserPreference.objects.filter(user_id=user_id).first()
        if not user_pref_obj:
            return JsonResponse({"status": "error", "message": "找不到偏好資料"}, status=404)

        try:
            preferences = json.loads(user_pref_obj.preferences)
        except Exception:
            preferences = {}

        if not isinstance(preferences, dict):
            return JsonResponse({"status": "error", "message": "偏好格式錯誤"}, status=500)

        found = False
        for category in ["喜歡", "不喜歡"]:
            if category in preferences and item_to_delete in preferences[category]:
                preferences[category].remove(item_to_delete)
                found = True
                break

        if not found:
            return JsonResponse({"status": "error", "message": f"{item_to_delete} 不存在於偏好資料中"}, status=404)

        UserPreference.objects.update_or_create(
            user_id=user_id,
            defaults={"preferences": json.dumps(preferences, ensure_ascii=False)}
        )

        return JsonResponse({
            "status": "success",
            "message": f"已成功刪除偏好項目：{item_to_delete}",
            "updated_preferences": preferences
        })

    except Exception as e:
        print(f"刪除使用者偏好錯誤：{str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)