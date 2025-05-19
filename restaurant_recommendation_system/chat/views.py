from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
import time
from .models import Message
from .food_controller import FoodRecommendationController

# 首頁視圖
def home(request):
    return render(request, 'chat/home.html')

# 聊天室視圖
@login_required
def chat_room(request):
    return render(request, 'chat/chat_room.html')

# 聊天助手視圖
def chat_assistant(request):
    return render(request, 'chat/assistant.html')

# 探索頁面視圖
def explore(request):
    return render(request, 'chat/explore.html')

# 關於頁面視圖
def about(request):
    return render(request, 'chat/about.html')

# 附近餐廳視圖
def nearby_restaurants(request):
    return render(request, 'chat/nearby_restaurants.html')

# 處理照片代理請求
def proxy_photo(request):
    from django.http import HttpResponse
    from .food_tools import GooglePlacesAPI
    
    photo_reference = request.GET.get('reference')
    max_width = request.GET.get('maxwidth', 800)
    
    if not photo_reference:
        return HttpResponse('Missing photo reference', status=400)
    
    api = GooglePlacesAPI()
    photo_data = api.get_photo_data(photo_reference, max_width)
    
    if photo_data:
        return HttpResponse(photo_data, content_type='image/jpeg')
    else:
        return HttpResponse('Failed to fetch photo', status=500)

# 處理發送訊息的視圖函數
@login_required
@require_POST
def send_message(request):
    try:
        # 解析JSON數據
        data = json.loads(request.body)
        user_message = data.get('message', '')
        user_preferences = data.get('preferences', {})
        user_location = data.get('location', {})
        
        # 儲存用戶訊息到數據庫
        Message.objects.create(
            user=request.user,
            content=user_message,
            is_bot_response=False
        )
        
        # 初始化控制器
        controller = FoodRecommendationController()
        
        # 處理查詢
        start_time = time.time()
        response = controller.process_query(user_message, user_location)
        processing_time = time.time() - start_time
        
        # 儲存機器人回應到數據庫
        Message.objects.create(
            user=request.user,
            content=response["content"],
            is_bot_response=True
        )
        
        # 記錄處理時間
        print(f"查詢處理耗時: {processing_time:.2f} 秒")
        
        # 返回響應
        return JsonResponse({
            'status': 'success',
            'bot_response': response
        })
        
    except Exception as e:
        print(f"處理訊息時發生錯誤: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500) 