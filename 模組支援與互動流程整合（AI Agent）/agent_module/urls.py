from django.urls import path
from . import views

urlpatterns = [
    path(
        'extract_negative_conditions/',
        views.ExtractNegativeConditionsView.as_view(),
        name='extract_negative_conditions'  # ✅ 功能一
    ),
    path(
        'generate_recommend_reasons/',
        views.GenerateRecommendReasonView.as_view(),
        name='generate_recommend_reasons'   # ✅ 功能二
    ),
]
