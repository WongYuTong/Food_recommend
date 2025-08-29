from django.db import models 
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class UserPreference(models.Model):
    SOURCE_CHOICES = [
        ('dialog', '對話'),
        ('profile', '使用者設定'),
        ('history', '點餐紀錄'),
    ]

    PREFERENCE_TYPE_CHOICES = [
        ('like', '喜歡'),
        ('dislike', '不喜歡'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="preferences")
    keyword = models.CharField(max_length=50, default="")  # 偏好，例如 "甜"、"辣"、"不吃牛"
    preference_type = models.CharField(
        max_length=10,
        choices=PREFERENCE_TYPE_CHOICES,
        default='like'
    )
    weight = models.FloatField(default=1.0)  # 權重，越高代表越重要
    frequency = models.IntegerField(default=1)  # 出現次數
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='dialog')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_preferences"  # 指定使用你現有的 PostgreSQL 資料表
        unique_together = ('user', 'keyword', 'preference_type')  # 同一個使用者、同一個偏好、同一類型唯一

    def __str__(self):
        return f"{self.user.username} - {self.keyword} ({self.preference_type}, weight={self.weight:.2f})"

    def update_preference(self, boost: float = 0.2, using_db: str = 'default'):
        """
        當使用者再次提到相同偏好時，更新頻率、權重和最後時間
        boost: 每次增加的權重
        using_db: 指定使用的資料庫
        """
        self.frequency += 1
        self.weight = min(self.weight + boost, 5.0)  # 最大權重為 5
        self.last_updated = timezone.now()
        self.save(using=using_db)

    def decay_weight(self, days: int = 30, decay_rate: float = 0.9, using_db: str = 'default'):
        """
        如果偏好太久沒更新，自動降低權重
        days: 超過多少天沒更新就衰減
        decay_rate: 衰減比例
        using_db: 指定使用的資料庫
        """
        if self.last_updated < timezone.now() - timedelta(days=days):
            self.weight = max(self.weight * decay_rate, 0.1)  # 最低 0.1
            self.save(using=using_db)