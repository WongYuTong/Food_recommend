# === 📦 imports ===

# 標準庫
import json
import re
import random

# Django
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# DRF
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.test import APIRequestFactory  # ✅ 新增這行
from rest_framework.request import Request
from rest_framework.parsers import JSONParser

# 本地 utils（共用邏輯）
from .utils_card import (
    generate_map_url,
    format_open_status,
    extract_district,
    generate_price_description,
    generate_recommend_reason
)


# 功能 1：反向推薦條件擷取（強化版 v6 - 語意補強完全命中）
class ExtractNegativeConditionsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get('type')
        user_input = request.data.get('text', '').strip()

        if req_type != 'text' or not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='text' 且包含 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        # --- 基本設定 ---
        prefix = r'(?:我|不過|那就|可能)?'
        negative_verbs = r'(不想吃|不想要|不要|不吃|別推薦|不要推薦|不太想吃|沒有很喜歡|那種我不愛|不會選|不太喜歡|不喜歡|不愛|我不會選|不考慮|無法接受)'
        pattern = rf'{prefix}{negative_verbs}(.+?)(?:[，。!！,\.\s]|$)'
        matches = re.findall(pattern, user_input)

        FUNCTION_PREFIXES = ['推薦', '餐廳', '地方', '那家', '這家', '店家', '吃', '想吃', '提供']
        TAIL_PARTICLES = r'[的了呢啦啊嘛唷喔哦耶呀囉吧]*$'
        PRESERVE_TERMS = ['吃到飽', '早午餐', '宵夜', '套餐', '內用', '外帶']
        CLEAN_SUFFIXES = ['的料理', '料理', '店家', '餐廳', '類型', '類', '那家', '這家', '店']
        EXCLUSION_WHITELIST = ['辣妹', '辣個', '辣個女生', '火辣的音樂']
        BLACKLIST_SUFFIX = ['那種', '這種']

        SEMANTIC_NEGATIVE_MAP = {
            "太油": "油膩",
            "很油": "油膩",
            "油膩": "油膩",
            "太膩": "油膩",
            "吃完會膩": "油膩",
            "甜到膩": "甜膩",
            "太貴": "高價",
            "價格太高": "高價",
            "CP 值太低": "高價",
            "份量少又貴": "高價",
            "不夠飽": "份量少",
            "太吵": "吵雜",
            "很吵": "吵雜",
            "太擠": "擁擠",
            "不太乾淨": "不乾淨",
            "衛生不好": "不乾淨",
            "不乾淨": "不乾淨",
            "太鹹": "重口味",
            "太辣": "重口味",
            "太鹹太辣": "重口味",
            "太多醬": "醬多",
            "太多醬的": "醬多",
            "雷": "雷店",
            "有點雷": "雷店",
            "雷店": "雷店",
            "太文青": "文青風格",
            "這種太文青的": "文青風格",
            "網美店": "網美店",
            "打卡店": "網美店",
            "Instagram 打卡": "網美店"
        }

        excluded_items = []

        for match in matches:
            phrase = match[1] if isinstance(match, tuple) and len(match) > 1 else match[0] if isinstance(match, tuple) else match
            split_words = re.split(r'[,、，和跟以及或還有\s]+', phrase)

            for word in split_words:
                word = word.strip()
                if not word or word in EXCLUSION_WHITELIST or word in BLACKLIST_SUFFIX:
                    continue

                if word in PRESERVE_TERMS:
                    cleaned = word
                elif word.endswith("的") and word[:-1] in PRESERVE_TERMS:
                    cleaned = word[:-1]
                else:
                    for prefix_word in FUNCTION_PREFIXES:
                        if word.startswith(prefix_word):
                            word = word[len(prefix_word):]
                            break
                    word = re.sub(TAIL_PARTICLES, '', word)
                    for suffix in CLEAN_SUFFIXES:
                        if word.endswith(suffix) and len(word) > len(suffix):
                            word = word[:-len(suffix)]
                            break
                    cleaned = word

                if cleaned and len(cleaned) <= 6 and re.match(r'^[\u4e00-\u9fffA-Za-z0-9]+$', cleaned):
                    excluded_items.append(cleaned)

        for phrase, keyword in SEMANTIC_NEGATIVE_MAP.items():
            if phrase in user_input and keyword not in excluded_items:
                excluded_items.append(keyword)

        final_excluded = []
        for kw in excluded_items:
            normalized = SEMANTIC_NEGATIVE_MAP.get(kw, kw)
            if normalized not in final_excluded:
                final_excluded.append(normalized)

        return Response({
            "status": "success",
            "data": {
                "excluded": final_excluded
            },
            "message": "已擷取反向推薦條件"
        }, status=status.HTTP_200_OK)


# 功能 2：推薦理由補強 + 結構化輸出（強化版：去重與排序 + 保底排除閘門）
class GenerateRecommendReasonView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from collections import OrderedDict
        import re, json

        DEBUG = True  # 想關閉終端 debug 印出就設為 False

        # ✅ 接收 user_input（可選）與上游傳入的 excluded_items（可選）
        user_input = (request.data.get("user_input", "") if hasattr(request, "data") else "").lower().strip()
        req_excluded_items = (request.data.get("excluded_items", []) if hasattr(request, "data") else []) or []

        if hasattr(request, 'data'):
            req_type = request.data.get('type')
            restaurants = request.data.get('restaurants', [])
        else:
            req_type = request.POST.get('type')
            try:
                restaurants = json.loads(request.body.decode()).get("restaurants", [])
            except Exception:
                restaurants = []

        if req_type != 'restaurant_list' or not isinstance(restaurants, list):
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='restaurant_list' 且包含 restaurants 清單"
            }, status=status.HTTP_400_BAD_REQUEST)

        # ======================
        # 🛡️ 保底排除閘門（關鍵修正）
        def _normalize(s: str) -> str:
            if not isinstance(s, str):
                return ""
            s = s.strip().lower()
            s = re.sub(r"[，,。.!？?、/\\|()\[\]【】{}\-＿_~^'\"`：:；;@#*$＋+＝=．·･\s]+", "", s)
            return s

        def _extract_negatives(text: str) -> list:
            if not text:
                return []
            # 1) 把否定詞擷取式子改成：分隔符後面一定要跟詞
            neg_pat = re.compile(
                r"(?:不想吃|不想要|不要|不吃|別推薦|不要推薦)\s*"
                r"([^\n，,。！!？?\s]+(?:(?:[、,/和與及或]|或是|[,，/ ])+[^\n，,。！!？?\s]+)*)"
            )
            m = neg_pat.search(text)
            if not m:
                return []
            seg = m.group(1)
            # 2) 分詞器維持你新加的版本即可（OK）
            parts = re.split(r"(?:[、,/和與及或]|或是|[,，\s])+", seg)
            return [p.strip() for p in parts if p.strip()]

        def _expand_exclusions(items: list) -> list:
            mapping = {
                "甜點": ["甜點", "甜品", "甜食", "蛋糕", "烘焙", "下午茶", "甜點店", "甜點專門", "甜點評價高"],
                "拉麵": ["拉麵", "ramen"],
                "燒烤": ["燒烤", "烤肉", "炭火", "燒肉"],
                "漢堡": ["漢堡", "burger"],
                "美式": ["美式", "美式餐廳", "美式風格", "美式漢堡"],
                "火鍋": ["火鍋", "鍋物", "涮涮鍋", "麻辣鍋"],
            }
            expanded = set()
            for it in items or []:
                raw = (it or "").strip()
                norm = _normalize(raw)
                if not norm:
                    continue
                candidates = set([raw, norm])
                for key, syns in mapping.items():
                    if key == raw or key == norm:
                        candidates |= set(syns)
                for c in candidates:
                    expanded.add(_normalize(c))
            return list(expanded)

        def _collect_blob(r: dict) -> str:
            parts = []
            for k in ["name", "highlight", "ai_reason", "comment_summary", "style", "address"]:
                v = r.get(k, "")
                if v:
                    parts.append(str(v))
            for lk in ["matched_tags", "tags", "features"]:
                seq = r.get(lk) or []
                parts.extend([str(t) for t in seq])
            return _normalize("｜".join(parts))

        extracted_from_input = _extract_negatives(user_input)
        raw_excluded = []
        for x in req_excluded_items + extracted_from_input:
            if x and x not in raw_excluded:
                raw_excluded.append(x)

        expanded_ex = set(_expand_exclusions(raw_excluded))
        if DEBUG: print("🧩(功能二) 擴充後排除詞：", sorted(expanded_ex))

        filtered_restaurants = []
        debug_hits = []
        for r in restaurants:
            blob = _collect_blob(r)
            hit = None
            for ex in expanded_ex:
                if ex and ex in blob:
                    hit = ex
                    break
            if hit:
                debug_hits.append((r.get("name", ""), hit))
                continue
            filtered_restaurants.append(r)

        if len(filtered_restaurants) == len(restaurants) and raw_excluded:
            tmp = []
            for r in filtered_restaurants:
                name = r.get("name", "")
                if any(x in name for x in raw_excluded):
                    debug_hits.append((name, f"fallback:{'/'.join(raw_excluded)}"))
                else:
                    tmp.append(r)
            filtered_restaurants = tmp

        if DEBUG: print("🔎(功能二) 被排除清單/命中詞：", debug_hits)

        restaurants = filtered_restaurants
        # ======================

        # ✅ 語意補強規則（原樣保留）
        user_input_rules = {
            "吃素": "素食需求", "素食": "素食需求",
            "怕辣": "避免辛辣料理", "不吃辣": "避免辛辣料理",
            "不想太油": "清爽口味", "清爽": "清爽口味", "太油": "清爽口味", "油膩": "清爽口味",
            "朋友聚餐": "適合朋友聚會", "同學聚餐": "適合朋友聚會", "聚餐": "適合聚餐",
            "家庭聚餐": "適合家庭聚會", "帶爸媽": "適合家庭聚會", "爸媽": "適合家庭聚會", "家人吃飯": "適合家庭聚會",
            "約會": "氣氛佳，適合約會", "商務": "適合正式聚會", "請客": "適合正式聚會", "正式": "適合正式聚會",
            "慶生": "適合慶祝場合", "生日": "適合慶祝場合", "慶祝": "適合慶祝場合",
            "小孩": "親子友善", "兒童": "親子友善",
            "不貴": "價格實惠", "便宜": "價格實惠", "平價": "價格實惠", "價格實惠": "價格實惠",
            "高級": "精緻高價", "高價": "精緻高價", "高端": "精緻高價", "精緻": "精緻高價",
            "宵夜": "適合宵夜", "深夜": "適合宵夜", "早午餐": "適合早午餐", "早餐": "適合早餐",
            "時間不多": "快速方便", "趕時間": "快速方便", "快速吃": "快速方便",
            "想吃辣": "重口味料理", "重口味": "重口味料理", "辣的料理": "重口味料理", "麻辣": "重口味料理", "辣鍋": "重口味料理",
        }

        # ✅ 保序去重（用在 tags）
        def uniq_keep_order(items):
            seen = set()
            out = []
            for it in items:
                if it not in seen:
                    seen.add(it)
                    out.append(it)
            return out

        # ✅ 語意去重 + 排序（原樣保留）
        def deduplicate_semantic(phrases):
            cleaned = []
            seen = set()
            phrases_sorted = sorted(phrases, key=lambda x: -len(x))
            for p in phrases_sorted:
                if all(p not in s for s in seen):
                    cleaned.append(p)
                    seen.add(p)
            return list(OrderedDict.fromkeys(cleaned))

        def sort_reasons(reason_list):
            priority = [
                "素食", "辛辣", "清爽", "重口味",
                "評價", "熱門", "氣氛",
                "價格", "CP", "高價", "便宜",
                "地點", "位於",
                "聚餐", "約會", "家庭", "宵夜", "早餐", "慶祝", "親子",
                "風格", "營業", "夜貓"
            ]
            return sorted(reason_list, key=lambda r: next((i for i, p in enumerate(priority) if p in r), len(priority)))

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
            distance_m = restaurant.get('distance_m', None)
            distance = f"{distance_m} 公尺" if distance_m else "未知"
            reason_score = restaurant.get('reason_score', 0)
            price_level = restaurant.get('price_level', '')
            review_count = restaurant.get('review_count', None)

            map_url = generate_map_url(name)
            is_open = format_open_status(is_open_raw)
            price_desc = generate_price_description(price_level)
            district = extract_district(address)

            reason_source = "inference"
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
                if "台北" in address or "新北" in address:
                    core_reasons.append("地點方便")
                if not core_reasons:
                    core_reasons.append("整體評價不錯")
                core_reason = "、".join(core_reasons)

            extra_reasons = []
            if highlight:
                extra_reasons.append(highlight)
            if matched_tags:
                extra_reasons.extend(matched_tags)
            if price_desc:
                extra_reasons.append(price_desc)
            if district:
                extra_reasons.append(f"位於{district}")

            features = restaurant.get("features", [])
            style = restaurant.get("style", "")
            opening_hours = restaurant.get("opening_hours", "")

            feature_map = {
                "甜點專門": "甜點評價高",
                "氣氛佳": "氣氛佳",
                "聚餐推薦": "適合聚餐",
                "高 CP 值": "高 CP 值",
                "價格便宜": "價格實惠",
                "價格親民": "價格實惠",
                "人氣餐廳": "熱門店家",
                "宵夜好選擇": "適合宵夜",
                "異國料理": "異國風味"
            }
            for f in features:
                if f in feature_map:
                    extra_reasons.append(feature_map[f])

            style_map = {
                "文青": "文青風格",
                "美式": "美式風格",
                "日式": "日式風格",
                "夜貓族": "適合夜貓子",
                "東南亞風": "東南亞風格"
            }
            if style in style_map:
                extra_reasons.append(style_map[style])

            if opening_hours:
                if "00" in opening_hours or "02" in opening_hours:
                    extra_reasons.append("夜間營業")
                if "23" in opening_hours or "22" in opening_hours:
                    extra_reasons.append("適合宵夜")
                if "全天" in opening_hours:
                    extra_reasons.append("全天營業")

            if user_input:
                for keyword, reason in user_input_rules.items():
                    if keyword in user_input:
                        extra_reasons.append(reason)

            # ✅ 語意去重 + 分類排序
            extra_reasons_cleaned = deduplicate_semantic(extra_reasons)
            extra_reasons_sorted = sort_reasons(extra_reasons_cleaned)

            reason_summary = {
                "source": reason_source,
                "core": core_reason,
                "extra": extra_reasons_sorted
            }
            full_reason = "、".join([core_reason] + extra_reasons_sorted)

            # ✅ tags：保序去重（避免 set 打亂順序）
            combined_tags = uniq_keep_order(list(matched_tags) + list(extra_reasons_sorted))

            results.append({
                "name": name,
                "address": address,
                "rating": rating,
                "price_level": price_level,
                "review_count": review_count,
                "highlight": highlight,
                "tags": combined_tags,
                "matched_tags": matched_tags,
                "is_open": is_open,
                "distance": distance,
                "reason_score": reason_score,
                "map_url": map_url,
                "reason_summary": reason_summary,
                "recommend_reason": full_reason
            })

        sorted_results = sorted(results, key=lambda x: (
            x.get('reason_score') or 0,
            x.get('rating') or 0,
            x.get('review_count') or 0
        ), reverse=True)

        return Response({
            "status": "success",
            "data": {
                "results": sorted_results
            },
            "message": "推薦理由已產生"
        }, status=status.HTTP_200_OK)
    

# 功能 3-1：模糊語句提示（最終優化版）
class GeneratePromptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get("type")
        user_input = request.data.get("text", "").strip()

        if req_type != "text" or not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='text' 且包含 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 模糊語句依照程度分類（可擴充）
        vague_patterns = {
            "vague": [
                "隨便", "你決定", "不知道", "不清楚", "沒意見", "沒想吃的", "不知道吃什麼", "不確定", "沒靈感", "隨你"
            ],
            "medium": [
                "都可以", "無所謂", "你看著辦", "你幫我選", "再說吧", "看心情", "看著辦", "可以啊都行", "沒關係"
            ],
            "slight": [
                "沒想法", "還沒想好", "沒特別想吃", "還不知道吃什麼", "需要想一下", "再看看", "再想想"
            ]
        }


        level = "clear"
        guidance = "歡迎告訴我們今天想吃什麼，或也可以提供不想吃的類型，我們會幫你挑選適合的餐廳！"

        # 遍歷所有模糊等級，依序比對
        for current_level, keywords in vague_patterns.items():
            if any(keyword in user_input for keyword in keywords):
                level = current_level
                if level == "slight":
                    guidance = "今天想吃點簡單的還是來點特別的呢？幾個方向幫你發想一下～"
                elif level == "medium":
                    guidance = "那你偏好什麼類型？或有不喜歡的料理嗎？我們可以幫你排除一部分喔！"
                elif level == "vague":
                    guidance = "可以先從『不想吃什麼』開始講起唷～像是不吃辣、不吃炸物之類的都可以說出來！"
                break

        return Response({
            "status": "success",
            "data": {
                "level": level,
                "guidance": guidance
            },
            "message": "模糊語句提示已產生"
        }, status=status.HTTP_200_OK)


# 功能 3-2：互動式語句引導建議（最終強化版2）

class SuggestInputGuidanceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get("type")
        user_input = request.data.get("text", "").lower().strip()

        if req_type != "text" or not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='text' 且包含 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        summary = []
        default_guidance = "您可以輸入想吃的類型、場合、預算等資訊，我們會給您更好的建議！"

        # ✅ 特殊處理：排除語句 + 特定料理
        exclusion_phrases = ['不想吃', '不吃', '不要']
        cuisine_phrases = ['甜點', '拉麵', '日式', '韓式', '中式', '義式', '義大利麵', '美式', '漢堡', '燒烤', '火鍋']
        if any(p in user_input for p in exclusion_phrases) and any(c in user_input for c in cuisine_phrases):
            summary.append({"type": "排除語句", "message": "已排除特定料理類型，可推薦其他選項"})

        # ✅ 通用語意分類規則
        rules = [
            ("飲食偏好", ['不吃辣', '怕辣', '我不吃辣'], '已排除辣味選項，推薦清爽、湯品等溫和口味'),
            ("飲食偏好", ['不吃牛', '我不吃牛'], '已排除牛肉餐點，可推薦雞肉、海鮮或蔬食'),
            ("飲食偏好", ['不吃海鮮', '海鮮過敏'], '已排除海鮮餐廳，推薦其他類型'),
            ("飲食偏好", ['吃素', '素食', '我吃素'], '已識別為素食需求，可推薦素食或蔬食友善餐廳'),

            ("用餐場合", ['朋友聚餐', '同學聚餐', '聚會'], '適合朋友聚會，可推薦平價熱鬧或多人套餐餐廳'),
            ("用餐場合", ['家庭聚餐', '家人吃飯', '家族聚餐', '爸媽'], '適合家庭用餐，建議選擇環境安靜、多樣菜色的餐廳'),
            ("用餐場合", ['約會'], '氣氛佳的推薦適合約會，可考慮咖啡廳或裝潢溫馨的餐廳'),
            ("用餐場合", ['商務', '請客', '正式'], '推薦穩重氣氛與高評價的餐廳，適合正式或商務用途'),
            ("用餐場合", ['慶生', '生日', '慶祝'], '推薦氣氛佳、有蛋糕或包廂的餐廳，適合慶祝場合'),
            ("用餐場合", ['小孩', '小朋友', '帶孩子', '兒童'], '適合親子用餐，建議考慮有兒童餐或寬敞空間的店家'),
            ("用餐場合", ['長輩', '父母', '家人一起吃'], '建議選擇環境安靜、餐點清淡的家庭友善餐廳'),

            ("預算", ['不貴', '便宜', '平價', '價格實惠'], '偏好不貴的餐廳，可以優先查看平價高評價選項'),
            ("預算", ['高級', '高價', '精致', '高端'], '偏好精緻體驗，可推薦高評價或高端餐廳'),

            ("時段", ['宵夜', '深夜'], '推薦宵夜時段營業中的輕食、炸物或拉麵等店家'),
            ("時段", ['早午餐'], '可推薦氣氛佳、評價高的早午餐店'),
            ("時段", ['早餐'], '推薦營業中的中西式早餐選項'),

            ("料理類型", ['甜點'], '推薦甜點評價高的餐廳或咖啡廳'),
            ("料理類型", ['拉麵', '日式'], '可推薦高分日式餐廳與拉麵名店'),
            ("料理類型", ['韓式'], '推薦高人氣韓式料理'),
            ("料理類型", ['中式'], '中式餐廳選擇豐富，推薦合菜或便當型店家'),
            ("料理類型", ['義式', '義大利麵'], '可推薦義式料理與義大利麵專門店'),
            ("料理類型", ['美式', '漢堡'], '推薦高評價美式漢堡或炸物餐廳'),

            ("飲食狀態", ['吃不多', '吃少一點', '簡單吃', '輕食'], '推薦輕食類型如三明治、沙拉或早午餐'),
            ("飲食狀態", ['趕時間', '快速吃', '時間不多'], '推薦供餐快速或外帶方便的選項'),
            ("飲食狀態", ['天氣冷', '想吃熱的', '暖胃'], '推薦湯品、火鍋或熱炒等溫暖料理'),
            ("飲食狀態", ['想吃辣', '重口味', '辣的料理', '麻辣', '辣鍋'], '適合重口味愛好者，推薦麻辣火鍋、川菜或韓式辣炒等餐廳'),
            ("飲食狀態", ['清淡', '不想太油', '吃清爽的'], '推薦清爽或湯品類型，適合口味較淡的需求'),
        ]

        for category, keywords, response_text in rules:
            if any(keyword in user_input for keyword in keywords):
                summary.append({"type": category, "message": response_text})

        if not summary:
            summary.append({"type": "其他", "message": default_guidance})

        guidance_combined = "；".join([item["message"] for item in summary])
        levels = list({item["type"] for item in summary})  # 去重類別

        return Response({
            "status": "success",
            "data": {
                "summary": summary,
                "guidance": guidance_combined,
                "level": levels
            },
            "message": "已產生語意引導建議"
        }, status=status.HTTP_200_OK)



# 功能 4：推薦卡片欄位模擬輸出(強化版)
class GenerateCardDataView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # ✅ 保險處理：兼容 DRF Request 和 WSGIRequest（整合測試用）
        if hasattr(request, 'data'):
            req_type = request.data.get('type')
            restaurants = request.data.get('restaurants', [])
        else:
            req_type = request.POST.get('type')
            try:
                restaurants = json.loads(request.body.decode()).get("restaurants", [])
            except Exception:
                restaurants = []

        if req_type != 'restaurant_list' or not isinstance(restaurants, list):
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='restaurant_list' 且包含 restaurants 清單"
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []

        for restaurant in restaurants:
            name = restaurant.get('name', '')
            rating = restaurant.get('rating', 0)
            address = restaurant.get('address', '')
            price_level = restaurant.get('price_level', '')
            review_count = restaurant.get('review_count', 0)
            is_open_raw = restaurant.get('is_open', None)
            matched_tags = restaurant.get('matched_tags', [])
            ai_reason = restaurant.get('ai_reason', '')
            highlight = restaurant.get('highlight', '')
            distance_m = restaurant.get('distance_m', random.randint(100, 2000))
            distance = f"{distance_m} 公尺"

            # 共用處理邏輯
            map_url = generate_map_url(name)
            is_open = format_open_status(is_open_raw)
            district = extract_district(address)
            price_desc = generate_price_description(price_level)

            # 組合 tags
            tags = list(set(matched_tags + ([district] if district else []) + ([price_desc] if price_desc else [])))

            # highlight 補強
            if not highlight:
                if "甜點" in tags or "蛋糕" in name:
                    highlight = "甜點評價高"
                elif rating >= 4.5:
                    highlight = "評價優良"
                elif district and name not in ["泰式小館"]:
                    highlight = "地點便利"
                else:
                    highlight = ""

            # 推薦理由
            recommend_reason = generate_recommend_reason(matched_tags, highlight, district, price_desc)

            # 模擬 features（邏輯擴充）
            features = []
            if "素食" in tags:
                features.append("提供素食")
            if price_desc == "價格實惠":
                features.append("高 CP 值")
            if "甜點" in tags or "蛋糕" in name:
                features.append("甜點專門")
            if rating >= 4.5 and review_count >= 300:
                features.append("人氣餐廳")
            if price_level == "$":
                features.append("價格便宜")
            if "異國料理" in tags or "泰式" in name:
                features.append("異國料理")

            # 模擬 style（先處理夜貓，再看其他）
            style = ""
            if "泰式" in name or "東南亞" in tags:
                style = "東南亞風"
            elif "夜貓族" in tags or "夜貓" in name or "宵夜" in tags or distance_m > 1500:
                style = "夜貓族"
            elif "文青" in name or "咖啡" in name or "甜點" in tags:
                style = "文青"
            elif "燒肉" in name or "烤肉" in tags:
                style = "美式"
            elif "壽司" in name or "日式" in tags or "拉麵" in name:
                style = "日式"

            # 模擬營業時間與預留欄位
            opening_hours = "11:00 - 21:00"
            has_coupon = False
            image_url = ""

            results.append({
                "name": name,
                "rating": rating,
                "address": address,
                "tags": tags,
                "highlight": highlight,
                "distance": distance,
                "distance_m": distance_m,
                "review_count": review_count,
                "price_level": price_level,
                "is_open": is_open,
                "map_url": map_url,
                "features": features,
                "style": style,
                "opening_hours": opening_hours,
                "recommend_reason": recommend_reason,
                "has_coupon": has_coupon,
                "image_url": image_url
            })

        return Response({
            "status": "success",
            "data": {
                "results": results
            },
            "message": "卡片欄位資料已產生"
        }, status=status.HTTP_200_OK)


# ✅ 整合測試：功能一 → 四 → 二（最終強化版，一次到位）
class IntegrationTestView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]  # ✅ 支援 application/json

    def post(self, request):
        from .sample_data import RESTAURANTS_SAMPLE
        from .views import ExtractNegativeConditionsView, GenerateCardDataView, GenerateRecommendReasonView

        factory = APIRequestFactory()

        input_text = request.data.get("text", "").strip()

        # ✅ 安全布林解析：避免 "false" 仍被當成 True
        raw_allow = request.data.get("allow_backfill", True)
        if isinstance(raw_allow, str):
            allow_backfill = raw_allow.strip().lower() in ("1", "true", "t", "yes", "y", "on")
        else:
            allow_backfill = bool(raw_allow)

        if not input_text:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        print("\n🎯 整合測試開始 >>>")
        print(f"📝 使用者輸入：{input_text}")
        print(f"🧩 allow_backfill = {allow_backfill}")

        # =========================
        # ✅ Step 1：功能一（排除條件擷取）
        request_exclusion = factory.post("/fake_path/", {"text": input_text}, format='json')
        wrapped_request = Request(request_exclusion, parsers=[JSONParser()])
        exclusion_response = ExtractNegativeConditionsView().post(wrapped_request)

        if hasattr(exclusion_response, "data") and isinstance(exclusion_response.data, dict):
            exclusion_data_raw = exclusion_response.data
        elif hasattr(exclusion_response, "_data") and isinstance(exclusion_response._data, dict):
            exclusion_data_raw = exclusion_response._data
        else:
            exclusion_data_raw = {}

        excluded_items = []
        if isinstance(exclusion_data_raw, dict):
            data_field = exclusion_data_raw.get("data", {})
            if isinstance(data_field, dict):
                excluded_items = data_field.get("excluded", [])
        print(f"🚫 上游排除項目：{excluded_items}")

        # =========================
        # ✅ Step 2：進階比對排除（清理標點/全形空白 + 同義詞 + 合併欄位字串 + 二次保底 + 可控補位）
        import re

        def _normalize(s: str) -> str:
            if not isinstance(s, str):
                return ""
            s = s.strip().lower()
            # 移除常見中英標點、全形空白與符號
            s = re.sub(r"[，,。.!？?、/\\|()\[\]【】{}\-＿_~^'\"`：:；;@#*$＋+＝=．·･\s]+", "", s)
            return s

        def _expand_exclusions(items: list) -> list:
            mapping = {
                "甜點": ["甜點", "甜品", "甜食", "蛋糕", "烘焙", "下午茶", "甜點店", "甜點專門", "甜點評價高"],
                "拉麵": ["拉麵", "ramen"],
                "燒烤": ["燒烤", "烤肉", "炭火", "燒肉"],
                "漢堡": ["漢堡", "burger"],
                "美式": ["美式", "美式餐廳", "美式風格", "美式漢堡"],
                "火鍋": ["火鍋", "鍋物", "涮涮鍋", "麻辣鍋"],
            }
            expanded = set()
            for it in items or []:
                raw = (it or "").strip()
                norm = _normalize(raw)
                if not norm:
                    continue
                # 原字與正規化字都拿去 mapping 找同義詞
                candidates = set([raw, norm])
                for key, syns in mapping.items():
                    if key == raw or key == norm:
                        candidates |= set(syns)
                # 所有候選詞正規化後加入
                for c in candidates:
                    expanded.add(_normalize(c))
            return list(expanded)

        def _collect_blob(r: dict) -> str:
            # 把可能包含品類訊息的欄位合併，提升命中率
            parts = []
            for k in ["name", "highlight", "ai_reason", "comment_summary", "style", "address"]:
                v = r.get(k, "")
                if v:
                    parts.append(str(v))
            for lk in ["matched_tags", "tags", "features"]:
                seq = r.get(lk) or []
                parts.extend([str(t) for t in seq])
            return _normalize("｜".join(parts))

        expanded_ex = set(_expand_exclusions(excluded_items))
        print(f"🧩 擴充後排除詞（norm）：{sorted(expanded_ex)}")

        # 統一先生成每間餐廳的「正規化合併字串」
        normalized_blobs = [(_collect_blob(r), r) for r in RESTAURANTS_SAMPLE]

        filtered = []
        debug_hits = []
        for blob, r in normalized_blobs:
            hit = None
            for ex in expanded_ex:
                if ex and ex in blob:
                    hit = ex
                    break
            if hit:
                debug_hits.append((r.get("name", ""), hit))
            else:
                filtered.append(r)

        # 🛡️ 二次保底：若完全沒剔除，用「名稱包含原始排除詞」再過一輪
        if len(filtered) == len(RESTAURANTS_SAMPLE):
            _raw_ex = [(it or "").strip() for it in (excluded_items or []) if (it or "").strip()]
            if _raw_ex:
                tmp = []
                for r in filtered:
                    name = r.get("name", "")
                    if any(x in name for x in _raw_ex):
                        debug_hits.append((name, f"fallback:{'/'.join(_raw_ex)}"))
                    else:
                        tmp.append(r)
                filtered = tmp

        print(f"✅ 通過排除篩選的餐廳數：{len(filtered)}")
        print("🔎 被排除清單/命中詞：", debug_hits)

        # —— 補位機制（可控）——
        TARGET_N = 5
        before_fill = len(filtered)
        used_backfill_pool = False

        if allow_backfill and len(filtered) < TARGET_N:
            picked_names = set(r.get("name", "") for r in filtered)
            candidate_pool = []
            for r in RESTAURANTS_SAMPLE:
                nm = r.get("name", "")
                if nm in picked_names:
                    continue
                blob = _collect_blob(r)
                if any(ex in blob for ex in expanded_ex):
                    continue
                candidate_pool.append(r)

            # 用 rating、review_count 做排序補位
            candidate_pool.sort(
                key=lambda x: (float(x.get("rating") or 0), int(x.get("review_count") or 0)),
                reverse=True
            )
            for r in candidate_pool:
                if len(filtered) >= TARGET_N:
                    break
                nm = r.get("name", "")
                if nm not in picked_names:
                    filtered.append(r)
                    picked_names.add(nm)

        # 可選：後備名單（若仍不足 5）
        if allow_backfill and len(filtered) < TARGET_N:
            BACKFILL_POOL = [
                {
                    "name": "青蔬便當舖",
                    "address": "台北市中正區",
                    "rating": 4.3, "review_count": 210,
                    "price_level": "$", "style": "家常",
                    "features": ["價格實惠", "快速方便"],
                    "matched_tags": ["素食需求", "清爽口味"],
                    "highlight": "平價清爽",
                    "ai_reason": "平價清爽、便當選擇多，適合快速用餐",
                },
                {
                    "name": "小巷清粥店",
                    "address": "台北市大同區",
                    "rating": 4.2, "review_count": 180,
                    "price_level": "$", "style": "傳統",
                    "features": ["清爽口味", "親子友善"],
                    "matched_tags": ["清爽口味"],
                    "highlight": "清粥小菜",
                    "ai_reason": "口味清爽、適合帶長輩，餐點選擇多",
                },
                {
                    "name": "南洋米線館",
                    "address": "台北市萬華區",
                    "rating": 4.4, "review_count": 260,
                    "price_level": "$$", "style": "東南亞風",
                    "features": ["價格實惠", "高 CP 值"],
                    "matched_tags": ["東南亞風格", "價格實惠"],
                    "highlight": "異國風味",
                    "ai_reason": "東南亞風味、份量充足、價格實惠",
                },
            ]
            picked_names = set(r.get("name", "") for r in filtered)
            safe_backfills = []
            for r in BACKFILL_POOL:
                if r["name"] in picked_names:
                    continue
                blob = _collect_blob(r)
                if any(ex in blob for ex in expanded_ex):
                    continue
                safe_backfills.append(r)

            safe_backfills.sort(
                key=lambda x: (float(x.get("rating") or 0), int(x.get("review_count") or 0)),
                reverse=True
            )
            for r in safe_backfills:
                if len(filtered) >= TARGET_N:
                    break
                filtered.append(r)
                picked_names.add(r.get("name", ""))
                used_backfill_pool = True

        if allow_backfill:
            print(
                f"📌 補位後的餐廳數：{len(filtered)}（目標 {TARGET_N}）；"
                f"來源：{'BACKFILL_POOL' if used_backfill_pool else ('RESTAURANTS_SAMPLE' if len(filtered) > before_fill else '無')}"
            )

        # =========================
        # ✅ Step 3：功能四（欄位補強）
        request_card_data = factory.post("/fake_path/", {
            "type": "restaurant_list",
            "restaurants": filtered
        }, format='json')
        wrapped_card_request = Request(request_card_data, parsers=[JSONParser()])
        card_data_response = GenerateCardDataView().post(wrapped_card_request)

        if hasattr(card_data_response, "data") and isinstance(card_data_response.data, dict):
            card_data_raw = card_data_response.data
        elif hasattr(card_data_response, "_data") and isinstance(card_data_response._data, dict):
            card_data_raw = card_data_response._data
        else:
            card_data_raw = {}

        card_restaurants = card_data_raw.get("data", {}).get("results", [])
        print(f"📦 補完欄位的餐廳數：{len(card_restaurants)}")

        # =========================
        # ✅ Step 4：功能二（推薦理由補強 + 保底排除）
        request_reason = factory.post("/fake_path/", {
            "type": "restaurant_list",
            "restaurants": card_restaurants,
            "user_input": input_text,
            "excluded_items": excluded_items,   # ⭐ 關鍵：把上游排除詞傳下去
        }, format='json')
        wrapped_reason_request = Request(request_reason, parsers=[JSONParser()])
        final_response = GenerateRecommendReasonView().post(wrapped_reason_request)

        if hasattr(final_response, "data") and isinstance(final_response.data, dict):
            final_data_raw = final_response.data
        elif hasattr(final_response, "_data") and isinstance(final_response._data, dict):
            final_data_raw = final_response._data
        else:
            final_data_raw = {}

        # 正確計算最終筆數（results 是 list）
        results_list = final_data_raw.get("data", {}).get("results", [])
        print(f"🌟 最終推薦結果筆數：{len(results_list) if isinstance(results_list, list) else 0}")

        # ✅ 回傳結構：維持你原本風格，外加把 excluded_items 一起回傳，方便測試印出或驗證
        return Response({
            "status": "success",
            "data": final_data_raw.get("data", {}),
            "excluded_items": excluded_items,
            "message": "整合流程已執行完成"
        }, status=status.HTTP_200_OK)




