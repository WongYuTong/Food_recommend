from django.urls import path
from . import views
from .views import (
    ExtractNegativeConditionsView,
    GenerateRecommendReasonView,
    GeneratePromptView,
    SuggestInputGuidanceView,
    GenerateCardDataView,
    IntegrationTestView
)

urlpatterns = [
    path('extract_negative_conditions/', ExtractNegativeConditionsView.as_view(), name='extract_negative_conditions'),  # 功能一
    path('generate_recommend_reasons/', GenerateRecommendReasonView.as_view(), name='generate_recommend_reasons'),    # 功能二
    path('generate_prompt/', GeneratePromptView.as_view(), name='generate_prompt'),                                   # 功能三
    path('suggest_input_guidance/', SuggestInputGuidanceView.as_view(), name='suggest_input_guidance'),              # 功能3-2
    path('generate_card_data/', GenerateCardDataView.as_view(), name='generate_card_data'),                          # 功能四
    path('integration_test/', IntegrationTestView.as_view(), name='integration_test'),                               # ✅ 整合測試
]
