from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_bot_response = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'
    
    class Meta:
        ordering = ['timestamp']

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='recommendation_images', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.food_name

# 新增模型 - 支持即時美食推薦系統
class UserPreference(models.Model):
    """用戶美食偏好"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='food_preferences')
    favorite_foods = models.TextField(blank=True, help_text="用户偏好的食物，以逗號分隔")
    food_restrictions = models.TextField(blank=True, help_text="飲食限制（如過敏、素食等）")
    preferred_price_level = models.IntegerField(null=True, blank=True, help_text="偏好的價格等級(0-4)")
    cuisine_preferences = models.TextField(blank=True, help_text="偏好的菜系，以逗號分隔")
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}的飲食偏好"

class SavedPlace(models.Model):
    """用戶保存的地點"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_places')
    place_id = models.CharField(max_length=255, help_text="Google Places API 地點ID")
    place_name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    rating = models.FloatField(null=True, blank=True)
    price_level = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="用戶對此地點的筆記")
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'place_id']
    
    def __str__(self):
        return f"{self.user.username} - {self.place_name}"

class QueryHistory(models.Model):
    """用戶查詢歷史"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='query_history')
    query_text = models.TextField()
    response_text = models.TextField()
    tools_used = models.CharField(max_length=255, blank=True, help_text="使用的工具，以逗號分隔")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Query histories"
    
    def __str__(self):
        return f"{self.user.username}: {self.query_text[:50]}"
