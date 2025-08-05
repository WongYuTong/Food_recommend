from django.urls import path
from . import views

urlpatterns = [
    path('recommend/', views.recommend_restaurant, name='recommend_restaurant'),
    path('save_preference/', views.save_user_preference, name='save_user_preference'),
    path('get_preference/', views.get_user_preference, name='get_user_preference'),
    path('delete_preference_item/', views.delete_user_preference_item),  # 移除 context/ 前綴
]