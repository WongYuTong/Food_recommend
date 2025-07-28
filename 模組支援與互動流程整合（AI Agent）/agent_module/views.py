from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
import random


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

# 功能 1：反向推薦條件擷取（優化後最終版）
class ExtractNegativeConditionsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get('text', '')

       # ✅ 支援更多前綴詞（我、不過、可能…）
        prefix_variants = r'(?:我|不過|那就|可能)?'
        negative_verbs = r'(不想吃|不想要|不要|不吃|別推薦|不要推薦)'

        # 🔍 組合成彈性正則：抓出否定語句
        pattern = rf'{prefix_variants}{negative_verbs}(.+?)(?:[，。!！,\.]|$)'

        matches = re.findall(pattern, user_input)
        excluded_items = []

        for match in matches:
            # 若 match 是 tuple（前綴 + 動詞 + 內容），我們只取內容
            content = match[1] if isinstance(match, tuple) else match
            split_items = re.split(r'[,、，和跟以及或還有\s]+', content)
            excluded_items.extend([item.strip() for item in split_items if item.strip()])

        # 去除重複並排序（方便測試與展示）
        unique_excluded = sorted(set(excluded_items))

        # ✅ 可選功能：只保留已知分類（未來整合資料庫或tag列表時可開啟）
        # known_categories = {"火鍋", "甜點", "壽司", "牛排", "燒烤", "義大利麵", "拉麵", "飲料"}
        # unique_excluded = [item for item in unique_excluded if item in known_categories]

        return Response({'excluded': unique_excluded})

# 功能 2：推薦理由補強 + 結構化輸出（優化版）
class GenerateRecommendReasonView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        restaurants = request.data.get('restaurants', [])
        results = []

        for restaurant in restaurants:
            name = restaurant.get('name', '')
            rating = restaurant.get('rating', 0)
            address = restaurant.get('address', '')
            is_open_raw = restaurant.get('is_open', None)
            ai_reason = restaurant.get('ai_reason', '')
            comment_summary = restaurant.get('comment_summary', '')
            highlight = restaurant.get('highlight', '')
            matched_tags = restaurant.get('matched_tags', [])
            distance = restaurant.get('distance', '未知')
            reason_score = restaurant.get('reason_score', None)
            price_level = restaurant.get('price_level', '')

            # 1. 營業狀態文字化
            if isinstance(is_open_raw, bool):
                is_open = "營業中" if is_open_raw else "休息中"
            elif isinstance(is_open_raw, str):
                is_open = is_open_raw
            else:
                is_open = "無資料"

            # 2. 主推薦理由
            reason_source = "inference"
            core_reason = ""

            if ai_reason:
                core_reason = ai_reason
                reason_source = "ai"
            elif comment_summary:
                core_reason = comment_summary
                reason_source = "summary"
            else:
                core_reasons = []
                if rating >= 4.5:
                    core_reasons.append("評價很高")
                if "台北" in address:
                    core_reasons.append("地點方便")
                if not core_reasons:
                    core_reasons.append("整體評價不錯")
                core_reason = "、".join(core_reasons)

            # 3. 補強 extra 理由（標籤、highlight、價格、地點）
            extra_reasons = []

            if highlight:
                extra_reasons.append(highlight)
            if matched_tags:
                extra_reasons.extend(matched_tags)

            # 補強價格
            if price_level == "$":
                extra_reasons.append("價格實惠")
            elif price_level == "$$":
                extra_reasons.append("價格中等")
            elif price_level == "$$$":
                extra_reasons.append("偏高價位")

            # 補強地區名稱（簡易從地址擷取）
            district_match = re.search(r'(台北市|新北市)?(\w{2,3}區)', address)
            if district_match:
                district = district_match.group(2)
                extra_reasons.append(f"位於{district}")

            # 4. 結構化推薦理由
            reason_summary = {
                "source": reason_source,
                "core": core_reason,
                "extra": extra_reasons
            }

            # 5. 合併成一行文字（給前端顯示用）
            full_reason = "、".join([core_reason] + extra_reasons)

            results.append({
                "name": name,
                "address": address,
                "is_open": is_open,
                "rating": rating,
                "reason": full_reason,
                "reason_summary": reason_summary,
                "distance": distance,
                "reason_score": reason_score,
                "highlight": highlight,
                "matched_tags": matched_tags,
                "price_level": price_level
            })

        return Response({"results": results})


# 功能 3：模糊語句提示（進階優化版）
class GeneratePromptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get("input", "").strip()

        vague_keywords = {
            "輕微": [
                "沒想法", "還沒想好", "沒特別想吃", "還不知道吃什麼", "需要想一下", "再看看"
            ],
            "中等": [
                "都可以", "無所謂", "你看著辦", "你幫我選", "再說吧", "看心情", "看著辦"
            ],
            "明確": [
                "隨便", "你決定", "不知道", "沒意見", "不知道吃什麼", "不清楚", "沒想吃的"
            ]
        }

        # 預設提示語
        level = "無"
        prompt = "有特別想吃的嗎？也可以說說你不想吃的類型，我們來幫你挑～"

        # 判斷模糊程度
        for current_level, keywords in vague_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                level = current_level
                if current_level == "輕微":
                    prompt = "想一下今天是想吃簡單一點的，還是想來點特別的呢？"
                elif current_level == "中等":
                    prompt = "那你偏好什麼類型呢？或是有不喜歡吃的料理？我們可以先排除看看！"
                elif current_level == "明確":
                    prompt = "沒問題！先從排除不愛吃的類型開始吧～像是不吃辣、不吃炸物這些都可以說唷！"
                break

        return Response({
            "level": level,
            "prompt": prompt
        }, status=status.HTTP_200_OK)


# 功能 3-2：互動式語句引導建議（優化版）
class SuggestInputGuidanceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get('text', '').lower()
        suggestion = '您可以輸入想吃的類型、場合、預算等資訊，我們會給您更好的建議！'

        rules = [
            # 飲食偏好／限制
            (['不吃辣', '怕辣'], '已排除辣味選項，推薦清爽、湯品等溫和口味'),
            (['不吃牛', '我不吃牛'], '已排除牛肉餐點，可推薦雞肉、海鮮或蔬食'),
            (['不吃海鮮', '海鮮過敏'], '已排除海鮮餐廳，推薦其他類型'),
            (['吃素', '素食', '我吃素'], '已識別為素食需求，可推薦素食或蔬食友善餐廳'),

            # 用餐場合
            (['朋友聚餐', '同學聚餐', '聚會'], '適合朋友聚會，可推薦平價熱鬧或多人套餐餐廳'),
            (['家庭聚餐', '家人吃飯', '家族聚餐'], '適合多人用餐，可考慮寬敞空間與多樣菜色的選擇'),
            (['約會'], '氣氛佳的推薦適合約會，可考慮咖啡廳或裝潢溫馨的餐廳'),
            (['商務', '請客', '正式'], '推薦穩重氣氛與高評價的餐廳，適合正式或商務用途'),
            (['慶生', '生日', '慶祝'], '推薦氣氛佳、有蛋糕或包廂的餐廳，適合慶祝場合'),
            (['小孩', '小朋友', '帶孩子', '兒童'], '適合親子用餐，建議考慮有兒童餐或寬敞空間的店家'),
            (['長輩', '父母', '家人一起吃'], '建議選擇環境安靜、餐點清淡的家庭友善餐廳'),

            # 價格／預算
            (['不貴', '便宜', '平價'], '偏好不貴的餐廳，可以優先查看平價高評價選項'),
            (['高級', '高價', '精緻', '高端'], '偏好精緻體驗，可推薦高評價或高端餐廳'),

            # 特定時段
            (['宵夜', '深夜'], '深夜推薦營業中的輕食、炸物或拉麵等店家'),
            (['早午餐'], '可推薦氣氛佳、評價高的早午餐店'),
            (['早餐'], '推薦營業中的中西式早餐選項'),

            # 類型偏好
            (['甜點'], '推薦甜點評價高的餐廳或咖啡廳'),
            (['拉麵', '日式'], '可推薦高分日式餐廳與拉麵名店'),
            (['韓式'], '推薦高人氣韓式料理'),
            (['中式'], '中式餐廳選擇豐富，推薦合菜或便當型店家'),
            (['義式', '義大利麵'], '可推薦義式料理與義大利麵專門店'),
            (['美式', '漢堡'], '推薦高評價美式漢堡或炸物餐廳'),

            # 飲食狀態／條件
            (['吃不多', '吃少一點', '簡單吃'], '推薦輕食類型如三明治、沙拉或早午餐'),
            (['趕時間', '快速吃', '時間不多'], '推薦供餐快速或外帶方便的選項'),
            (['天氣冷', '想吃熱的', '暖胃'], '推薦湯品、火鍋或熱炒等溫暖料理'),
            (['想吃辣', '重口味', '辣的料理'], '推薦麻辣火鍋、川菜或韓式辣炒等餐廳'),
            (['清淡', '不想太油', '吃清爽的'], '推薦清爽或湯品類型，適合口味較淡的需求'),

            # 泛用否定類（最後 fallback）
            (['不想吃', '不要', '不吃'], '已偵測到排除類型，可以幫您濾除不想吃的餐廳'),
        ]

        for keywords, response_text in rules:
            if any(k in user_input for k in keywords):
                suggestion = response_text
                break

        return Response({'guidance': suggestion}, status=status.HTTP_200_OK)



# 功能 4：推薦卡片欄位模擬輸出
class GenerateCardDataView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        restaurants = request.data.get('restaurants', [])
        results = []

        for r in restaurants:
            name = r.get('name', '')
            rating = r.get('rating', 0)
            address = r.get('address', '')
            is_open = r.get('is_open', None)  # 可選欄位

            # 區域標籤擷取（信義區、中山區等）
            district_match = re.search(r'(台北市|新北市)?(\w{2,3}區)', address)
            district = district_match.group(2) if district_match else ''
            
            # 標籤產生
            tags = []
            keyword_map = {
                '燒肉': ['燒肉'],
                '甜點': ['甜點', '蛋糕'],
                '拉麵': ['拉麵'],
                '火鍋': ['火鍋', '麻辣'],
                '早午餐': ['早午餐', 'Brunch'],
                '漢堡': ['漢堡', '美式'],
                '日式': ['壽司', '日式'],
                '中式': ['中餐', '中式'],
                '韓式': ['韓式', '泡菜']
            }
            for tag, keywords in keyword_map.items():
                if any(k in name or k in address for k in keywords):
                    tags.append(tag)

            if rating >= 4.5:
                tags.append("高評價")
            if district:
                tags.append(district)
            if is_open is not None:
                tags.append("目前營業中" if is_open else "尚未營業")

            # highlight（亮點）
            if '甜' in name or '甜點' in name:
                highlight = "甜點評價高"
            elif rating >= 4.5:
                highlight = "Google 評價 4.5 分以上"
            elif '交通' in name or '捷運' in address:
                highlight = "交通方便"
            else:
                highlight = "地點便利"

            # 模擬距離（之後可改為真實資料）
            distance = "850 公尺"  # 假資料

            # 推薦理由組合（避免重複）
            combined = list(dict.fromkeys(tags + [highlight]))
            reason = "、".join(combined)

            # 輸出結果
            results.append({
                "name": name,
                "rating": rating,
                "address": address,
                "tags": tags,
                "highlight": highlight,
                "distance": distance,
                "reason": reason
            })

        return Response({"results": results})
