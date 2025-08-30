# context/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
import re

from utils.chat_view import get_current_context_info
from utils.emotion_parser import parse_emotion_from_text
from utils.preference_parser import parse_preference_from_text
from context.restaurant_controller import RestaurantRecommendationController
from context.models import UserPreference
from django.contrib.auth.models import User

# DB 欄位 (like/dislike) 與 API 回傳 (喜歡/不喜歡) 的對應
type_mapping = {"like": "喜歡", "dislike": "不喜歡"}
reverse_mapping = {"喜歡": "like", "不喜歡": "dislike"}

# 用於偵測刪除偏好的關鍵字
DELETE_KEYWORDS = ["不喜歡", "不要", "不想吃", "刪掉", "移除", "取消"]


# ---------------- 推薦餐廳 ----------------
@csrf_exempt
@require_POST
def recommend_restaurant(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
        user_location = data.get("location", {})
        user_id = data.get("user_id")

        # 取得時段與上下文
        context_info = get_current_context_info()
        meal_time = context_info.get("meal_time", "午餐")

        # 偵測情緒
        detected_emotions = parse_emotion_from_text(user_message)

        # 取得使用者長期偏好
        long_term_preferences = {"喜歡": [], "不喜歡": []}
        if user_id and User.objects.filter(id=user_id).exists():
            user = User.objects.get(id=user_id)
            prefs_qs = UserPreference.objects.filter(user=user)
            for pref in prefs_qs:
                mapped_type = type_mapping.get(pref.preference_type, pref.preference_type)
                long_term_preferences.setdefault(mapped_type, []).append(pref.keyword)

        # 分析新的偏好
        parsed_preferences = parse_preference_from_text(user_message)
        if not parsed_preferences or parsed_preferences == ["無特別偏好"]:
            parsed_preferences = {"long_term": {"喜歡": [], "不喜歡": []}, 
                                  "short_term": {"喜歡": [], "不喜歡": []}}

        short_term_preferences = parsed_preferences.get("short_term", {"喜歡": [], "不喜歡": []})

        # 更新長期偏好到 DB
        if parsed_preferences and parsed_preferences != ["無特別偏好"] and user_id and User.objects.filter(id=user_id).exists():
            user = User.objects.get(id=user_id)
            for category in ["喜歡", "不喜歡"]:
                for keyword in parsed_preferences.get("long_term", {}).get(category, []):
                    pref_obj, created = UserPreference.objects.get_or_create(
                        user=user,
                        keyword=keyword,
                        preference_type=reverse_mapping[category],
                        defaults={"weight": 1.0, "frequency": 1, "source": "dialog"}
                    )
                    if not created:
                        pref_obj.update_preference(boost=1.0)

            # 更新 long_term_preferences
            long_term_preferences = {"喜歡": [], "不喜歡": []}
            prefs_qs = UserPreference.objects.filter(user=user)
            for pref in prefs_qs:
                mapped_type = type_mapping.get(pref.preference_type, pref.preference_type)
                long_term_preferences[mapped_type].append(pref.keyword)

        # 偵測刪除偏好
        if user_id and User.objects.filter(id=user_id).exists():
            user = User.objects.get(id=user_id)
            for delete_kw in DELETE_KEYWORDS:
                matches = re.findall(f"{delete_kw}([^\s，；]+)", user_message)
                for item in matches:
                    pref_qs = UserPreference.objects.filter(user=user, keyword=item)
                    if pref_qs.exists():
                        pref_qs.delete()

        # 組成 response_text
        if not long_term_preferences['喜歡'] and not long_term_preferences['不喜歡']:
            response_text = f"這是你的推薦，我們先根據\"{meal_time}\"推薦熱門餐廳。你也可以輸入口味喜好，我們會記住喔！"
        else:
            response_text = "根據您的偏好，我們為您推薦以下餐廳。你也可以修改或新增偏好！"

        # 推薦餐廳
        controller = RestaurantRecommendationController()
        recommendation = controller.process_query(
            query_text=user_message,
            user_location=user_location,
            user_id=user_id,
            context=context_info,
            emotions=detected_emotions,
            preferences=long_term_preferences,
            short_term_preferences=short_term_preferences
        )

        # 回傳 JSON（長期與短期偏好）
        return JsonResponse({
            "status": "success",
            "response_text": response_text,
            "context_info": context_info,
            "detected_emotions": detected_emotions,
            "user_preferences": {
                "long_term": long_term_preferences,
                "short_term": short_term_preferences
            },
            "recommendation": recommendation
        })

    except Exception as e:
        print(f"推薦餐廳發生錯誤：{str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# ---------------- 儲存使用者偏好 ----------------
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

        user = User.objects.get(id=user_id)
        parsed_preferences = parse_preference_from_text(preferences_text)
        if not parsed_preferences or parsed_preferences == ["無特別偏好"]:
            parsed_preferences = {"long_term": {"喜歡": [], "不喜歡": []}, 
                                  "short_term": {"喜歡": [], "不喜歡": []}}
        else:
            # 儲存長期偏好
            for category in ["喜歡", "不喜歡"]:
                for keyword in parsed_preferences.get("long_term", {}).get(category, []):
                    pref_obj, created = UserPreference.objects.get_or_create(
                        user=user,
                        keyword=keyword,
                        preference_type=reverse_mapping[category],
                        defaults={"weight": 1.0, "frequency": 1, "source": "manual"}
                    )
                    if not created:
                        pref_obj.update_preference(boost=1.0)

        return JsonResponse({
            "status": "success",
            "message": "偏好已更新",
            "parsed_preferences": parsed_preferences
        })

    except Exception as e:
        print(f"儲存使用者偏好錯誤：{str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# ---------------- 查詢使用者偏好 ----------------
@csrf_exempt
@require_GET
def get_user_preference(request):
    try:
        user_id = request.GET.get("user_id")
        if not user_id:
            return JsonResponse({"status": "error", "message": "缺少 user_id"}, status=400)
        if not User.objects.filter(id=user_id).exists():
            return JsonResponse({"status": "error", "message": "使用者不存在"}, status=404)

        user = User.objects.get(id=user_id)
        prefs_qs = UserPreference.objects.filter(user=user)
        long_term_preferences = {"喜歡": [], "不喜歡": []}
        for pref in prefs_qs:
            mapped_type = type_mapping.get(pref.preference_type, pref.preference_type)
            long_term_preferences[mapped_type].append(pref.keyword)

        return JsonResponse({"status": "success", "preferences": {"long_term": long_term_preferences}})

    except Exception as e:
        print(f"讀取使用者偏好錯誤：{str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# ---------------- 刪除使用者偏好項目（自動解析使用者語句） ----------------
@csrf_exempt
@require_POST
def delete_user_preference_item(request):
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
        sentence = data.get("sentence")  # 前端傳整句話，例如 "我不要牛肉"

        if not user_id or not sentence:
            return JsonResponse({"status": "error", "message": "缺少 user_id 或 sentence"}, status=400)
        if not User.objects.filter(id=user_id).exists():
            return JsonResponse({"status": "error", "message": "使用者不存在"}, status=404)

        user = User.objects.get(id=user_id)
        deleted_items = []
        not_found_items = []

        # 自動解析使用者語句中的刪除偏好
        for delete_kw in DELETE_KEYWORDS:
            matches = re.findall(f"{delete_kw}([^\s，；]+)", sentence)
            for item in matches:
                pref_qs = UserPreference.objects.filter(user=user, keyword=item)
                if pref_qs.exists():
                    pref_qs.delete()
                    deleted_items.append(item)
                else:
                    not_found_items.append(item)

        # 回傳刪除結果訊息
        if deleted_items:
            message = f"已成功刪除偏好：{'、'.join(deleted_items)}"
            if not_found_items:
                message += f"；未找到偏好：{'、'.join(not_found_items)}"
            return JsonResponse({"status": "success", "message": message})

        return JsonResponse({"status": "error", "message": "未偵測到要刪除的偏好項目"}, status=404)

    except Exception as e:
        print(f"刪除使用者偏好錯誤：{str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)