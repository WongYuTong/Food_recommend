from django.urls import path
from . import views

urlpatterns = [
    path(
        'extract_negative_conditions/',
        views.ExtractNegativeConditionsView.as_view(),
        name='extract_negative_conditions'),# ✅ 功能一

    path(
        'generate_recommend_reasons/',
        views.GenerateRecommendReasonView.as_view(),
        name='generate_recommend_reasons'),# ✅ 功能二

    path('generate_prompt/', 
         views.GeneratePromptView.as_view(), 
         name='generate_prompt'), # ✅ 功能三

    path('suggest_input_guidance/', 
         views.SuggestInputGuidanceView.as_view(), 
         name='suggest_input_guidance'), # ✅ 功能3-2

    path('generate_card_data/', 
         views.GenerateCardDataView.as_view(), 
         name='generate_card_data'), # ✅ 功能四
]
