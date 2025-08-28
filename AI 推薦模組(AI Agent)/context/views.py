# context/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
import re
from django.utils import timezone

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

DB_ALIAS = 'user_pref'  # 指定 PostgreSQL 資料庫

# ---------------- 推薦餐廳 ----------------
@csrf_exempt
@require_POST
def recommend_restaurant(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
        user_location = data.get("location", {})
        user_id = data.get("user_id")

        context_info = get_current_context_info()
        detected_emotions = parse_emotion_from_text(user_message)
        user_preferences = {"喜歡": [], "不喜歡": []}
        preference_msg = ""

        # 取得現有偏好
        if user_id and User.objects.filter(id=user_id).exists():
            user = User.objects.get(id=user_id)
            prefs_qs = UserPreference.objects.using(DB_ALIAS).filter(user=user)
            for pref in prefs_qs:
                mapped_type = type_mapping.get(pref.preference_type, pref.preference_type)
                user_preferences.setdefault(mapped_type, []).append(pref.keyword)

        # 分析新的偏好
        parsed_preferences = parse_preference_from_text(user_message)
        if parsed_preferences and parsed_preferences != ["無特別偏好"] and user_id and User.objects.filter(id=user_id).exists():
            user = User.objects.get(id=user_id)
            for category in ["喜歡", "不喜歡"]:
                for keyword in parsed_preferences.get(category, []):
                    pref_obj, created = UserPreference.objects.using(DB_ALIAS).get_or_create(
                        user=user,
                        keyword=keyword,
                        preference_type=reverse_mapping[category],
                        defaults={
                            "weight": 1.0,
                            "frequency": 1,
                            "source": "dialog",
                        }
                    )
                    if not created:
                        pref_obj.update_preference(boost=1.0, using_db=DB_ALIAS)

            # 更新 user_preferences
            user_preferences = {"喜歡": [], "不喜歡": []}
            prefs_qs = UserPreference.objects.using(DB_ALIAS).filter(user=user)
            for pref in prefs_qs:
                mapped_type = type_mapping.get(pref.preference_type, pref.preference_type)
                user_preferences[mapped_type].append(pref.keyword)

            # 建立偏好訊息
            like_list = parsed_preferences.get("喜歡", [])
            dislike_list = parsed_preferences.get("不喜歡", [])
            parts = []
            if like_list:
                parts.append(f"已為你新增『{'、'.join(like_list)}』偏好")
            if dislike_list:
                parts.append(f"已為你排除『{'、'.join(dislike_list)}』")
            preference_msg = "；".join(parts)

        # ------------------ 偵測刪除偏好 ------------------
        if user_id and User.objects.filter(id=user_id).exists():
            user = User.objects.get(id=user_id)
            deleted_items = []
            not_found_items = []

            for delete_kw in DELETE_KEYWORDS:
                matches = re.findall(f"{delete_kw}([^\s，；]+)", user_message)
                for item in matches:
                    pref_qs = UserPreference.objects.using(DB_ALIAS).filter(user=user, keyword=item)
                    if pref_qs.exists():
                        pref_qs.delete()
                        deleted_items.append(item)
                    else:
                        not_found_items.append(item)

            # 建立刪除提示訊息
            delete_msg_parts = []
            if deleted_items:
                delete_msg_parts.append(f"已成功刪除偏好：{'、'.join(deleted_items)}")
            if not_found_items:
                delete_msg_parts.append(f"未找到偏好：{'、'.join(not_found_items)}")
            if delete_msg_parts:
                preference_msg = preference_msg + ("\n" if preference_msg else "") + "；".join(delete_msg_parts)

        # 推薦餐廳
        controller = RestaurantRecommendationController()
        response = controller.process_query(
            query_text=user_message,
            user_location=user_location,
            user_id=user_id,
            context=context_info,
            emotions=detected_emotions,
            preferences=user_preferences
        )

        full_response_text = preference_msg + ("\n" if preference_msg else "") + response.get("response_text", "")

        return JsonResponse({
            "status": "success",
            "data": {
                "context_info": context_info,
                "detected_emotions": detected_emotions,
                "user_preferences": user_preferences,
                "recommendation": response,
                "preference_message": preference_msg,
                "full_response_text": full_response_text,
            }
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
        if not parsed_preferences:
            parsed_preferences = {"提示": "未偵測到明確偏好"}

        if parsed_preferences != ["無特別偏好"]:
            for category in ["喜歡", "不喜歡"]:
                for keyword in parsed_preferences.get(category, []):
                    pref_obj, created = UserPreference.objects.using(DB_ALIAS).get_or_create(
                        user=user,
                        keyword=keyword,
                        preference_type=reverse_mapping[category],
                        defaults={
                            "weight": 1.0,
                            "frequency": 1,
                            "source": "manual",
                        }
                    )
                    if not created:
                        pref_obj.update_preference(boost=1.0, using_db=DB_ALIAS)

        return JsonResponse({"status": "success", "message": "偏好已儲存", "parsed_preferences": parsed_preferences})

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
        prefs_qs = UserPreference.objects.using(DB_ALIAS).filter(user=user)
        preferences = {"喜歡": [], "不喜歡": []}
        for pref in prefs_qs:
            mapped_type = type_mapping.get(pref.preference_type, pref.preference_type)
            preferences[mapped_type].append(pref.keyword)

        return JsonResponse({"status": "success", "preferences": preferences})

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
                pref_qs = UserPreference.objects.using(DB_ALIAS).filter(user=user, keyword=item)
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