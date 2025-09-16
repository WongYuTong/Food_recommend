import requests
from django.db import models
from restaurants.models import RestaurantIndicatorDetail, RestaurantIndicatorSummary
from user.models import UserPreferenceDetail, UserPreferenceSummary

def call_fastapi_analyze_restaurant(post_id, content, place_id=None):
    url = "http://localhost:8001/analyze/restaurant/"
    data = {
        "post_id": post_id,
        "content": content,
    }
    if place_id:
        data["place_id"] = place_id
    print(f"[送出] call_fastapi_analyze_restaurant: {data}")
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        print(f"[回傳] call_fastapi_analyze_restaurant: {resp.json()}")
        return resp.json()
    except Exception as e:
        print(f"[錯誤] call_fastapi_analyze_restaurant: {e}")
        return {"status": "error", "msg": str(e)}

def call_fastapi_analyze_user(post_id, content, user_id=None):
    url = "http://localhost:8001/analyze/user/"
    data = {
        "post_id": post_id,
        "content": content,
    }
    if user_id:
        data["user_id"] = user_id
    print(f"[送出] call_fastapi_analyze_user: {data}")
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        print(f"[回傳] call_fastapi_analyze_user: {resp.json()}")
        return resp.json()
    except Exception as e:
        print(f"[錯誤] call_fastapi_analyze_user: {e}")
        return {"status": "error", "msg": str(e)}

def analyze_and_save_restaurant_indicator(post, logger=None):
    result = call_fastapi_analyze_restaurant(post.id, post.content, post.location_place_id)
    if logger:
        logger.info(f"已呼叫 FastAPI 分析餐廳指標 ID:{post.id}，結果：{result}")
    if result.get("status") == "success" and "data" in result:
        for indicator in result["data"]:
            detail, created = RestaurantIndicatorDetail.objects.update_or_create(
                source="post",
                source_id=post.id,
                place_id=indicator.get("place_id"),
                indicator_type=indicator.get("indicator_type"),
                defaults={
                    "score": indicator.get("score")
                }
            )
            # 每次細項更新後，同步更新 summary
            update_restaurant_indicator_summary(
                place_id=indicator.get("place_id"),
                indicator_type=indicator.get("indicator_type")
            )
    return result

def analyze_and_save_user_preference(post, logger=None):
    result = call_fastapi_analyze_user(post.id, post.content, post.user.id)
    if logger:
        logger.info(f"已呼叫 FastAPI 分析使用者偏好 ID:{post.id}，結果：{result}")
    if result.get("status") == "success" and "data" in result:
        foods = result["data"].get("foods", [])
        for food in foods:
            UserPreferenceDetail.objects.update_or_create(
                user=post.user,
                keyword=food,
                preference_type="mention",  # 或 "mention"
                source="post",
                source_id=post.id,
                defaults={
                    "weight": 1.0,
                    "frequency": 1,
                }
            )
    return result

def update_user_preference_summary(user):
    # 統計每個 keyword 出現次數
    details = UserPreferenceDetail.objects.filter(user=user)
    keyword_counts = {}
    for d in details:
        keyword_counts[d.keyword] = keyword_counts.get(d.keyword, 0) + 1

    for keyword, count in keyword_counts.items():
        preference_type = "like" if count >= 5 else "mention"
        UserPreferenceSummary.objects.update_or_create(
            user=user,
            keyword=keyword,
            defaults={
                "preference_type": preference_type,
                "frequency": count,
            }
        )

def update_restaurant_indicator_summary(place_id, indicator_type):
    # 彙總所有細項
    details = RestaurantIndicatorDetail.objects.filter(
        place_id=place_id,
        indicator_type=indicator_type
    )
    count = details.count()
    total_score = details.aggregate(total=models.Avg('score'))['total'] or 0
    RestaurantIndicatorSummary.objects.update_or_create(
        place_id=place_id,
        indicator_type=indicator_type,
        defaults={
            "total_score": total_score,
            "count": count,
        }
    )