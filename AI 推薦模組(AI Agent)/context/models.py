from django.db import models
from django.contrib.auth.models import User

class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferences = models.JSONField(default=dict)  # 儲存使用者偏好，預設為空字典

    def __str__(self):
        return f"{self.user.username} 的偏好"