from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .api import CustomAuthToken, LogoutView

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('post/new/', views.create_post, name='create_post'),
    path('post/history/', views.post_history, name='post_history'),
    path('favorite/<int:post_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('favorites/', views.favorites, name='favorites'),
    path('followers/', views.followers, name='followers'),
    path('following/', views.following, name='following'),
    path('following/<int:user_id>/', views.following, name='user_following'),
    
    # 新增 - 帖文置頂功能
    path('post/<int:post_id>/pin/', views.toggle_post_pin, name='toggle_post_pin'),
    
    # 新增 - 商家認證相關
    path('verification/apply/', views.apply_for_verification, name='apply_for_verification'),
    path('verification/review/<int:verification_id>/', views.review_verification, name='review_verification'),
    path('admin/verifications/', views.admin_verification_list, name='admin_verification_list'),
    
    # 新增 - 管理員功能
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/feature/', views.toggle_post_feature, name='toggle_post_feature'),
    
    # 新增 - 系統公告相關
    path('announcements/', views.view_announcements, name='view_announcements'),
    path('announcement/<int:announcement_id>/', views.view_announcement, name='view_announcement'),
    path('admin/announcements/', views.announcement_list, name='announcement_list'),
    path('admin/announcement/new/', views.create_announcement, name='create_announcement'),
    path('admin/announcement/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('admin/announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('admin/announcement/<int:announcement_id>/toggle/', views.toggle_announcement, name='toggle_announcement'),
    
    # 新增 - 動態牆與探索頁面功能
    path('feed/', views.feed, name='feed'),
    path('explore/', views.explore, name='explore'),
    
    # 新增 - 單一貼文頁面與編輯功能
    path('post/<int:post_id>/', views.view_post, name='view_post'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('post/<int:post_id>/reaction/add/', views.add_reaction, name='add_reaction'),
    path('post/<int:post_id>/reaction/remove/', views.remove_reaction, name='remove_reaction'),
    
    # 新增 - 通知系統
    path('notifications/', views.notifications, name='notifications'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notification/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/delete-all/', views.delete_all_notifications, name='delete_all_notifications'),
    
    # 新增 - 回報系統
    path('report/post/<int:post_id>/', views.report_post, name='report_post'),
    path('report/comment/<int:comment_id>/', views.report_comment, name='report_comment'),
    path('report/user/<int:user_id>/', views.report_user, name='report_user'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/report/<int:report_id>/handle/', views.handle_report, name='handle_report'),
    
    # 新增 - 公開用戶主頁
    path('user/<str:username>/', views.public_profile, name='public_profile'),
    
    # API端点 - Token认证
    path('api/token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),
    
    # 餐廳收藏相關
    path('restaurant/favorite/', views.toggle_favorite_restaurant, name='toggle_favorite_restaurant'),
    path('restaurant/favorites/', views.favorite_restaurants, name='favorite_restaurants'),
    path('restaurant/favorite/delete/<int:favorite_id>/', views.delete_favorite_restaurant, name='delete_favorite_restaurant'),
    path('restaurant/check_favorite/', views.check_favorite_restaurant, name='check_favorite_restaurant'),
] 