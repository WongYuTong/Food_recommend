from ml_models import ws_driver, pos_driver, zero_shot, ner
from tqdm import tqdm
from collections import Counter
import re
import time

class CKIPTransformersTests:
    @classmethod
    def setUpClass(cls):
        print("模型已由 ml_models.py 初始化，直接 import 使用")
        cls.ws_driver = ws_driver
        cls.pos_driver = pos_driver
        cls.zero_shot = zero_shot
        cls.ner = ner

    # 判斷詞組是否與食物相關
    def is_food_related(self, phrase, core_food_terms, ws=None):
        """評估一個詞組是否與食物相關"""
        # 0. 排除帶有「湯頭」、「口味」等描述性詞的組合
        description_terms = ["湯頭", "口味", "味道", "外皮", "感覺", "香氣", "姊姊", "人員", "態度", "外帶"]
        if any(term in phrase for term in description_terms):
            return False
            
        # 1. 直接包含核心食物詞
        if any(food_term in phrase for food_term in core_food_terms):
            return True
            
        # 2. 如果有斷詞結果，檢查每個分詞是否為食物相關
        if ws:
            for word in ws:
                if any(food_term in word for food_term in core_food_terms):
                    return True
                    
        # 3. 檢查是否包含特定食物種類字
        food_categories = [
            "餐", "飯", "麵", "湯", "醬", "甜點", "冰", "炸", "烤", "煮", "蒸", "燉", "捲",
            "堡", "餅", "塔", "泥", "奶", "茶", "酪", "羅", "拋", "粥", "糕", "排", "肉",
            "菜", "豆", "鮮", "豬", "牛", "雞", "魚", "蝦", "貝", "米", "酥", "蛋", "泰式", 
            "義式", "日式", "韓式", "美式", "中式", "料理"
        ]
        
        # 注意：特定組合詞需要額外檢查
        if "口味" in phrase or "湯頭" in phrase:
            return False
            
        if any(category in phrase for category in food_categories):
            # 排除特定詞組
            if any(word in phrase for word in ["姊姊", "感覺", "這次", "下次", "這家", "服務"]):
                return False
            return True
            
        # 4. 排除明顯非食物的詞組
        non_food_indicators = [
            "服務", "這家", "下次", "朋友", "超", "很", "店", "感覺", "價格", "風景", "老闆",
            "環境", "這次", "桌子", "座位", "時間", "等待", "人員", "態度", "客人", "服務生", 
            "裝潢", "外觀", "打卡", "聚餐", "親友", "用餐", "地點", "位置", "停車", "交通",
            "點餐", "菜單", "介紹", "推薦", "建議", "評價", "評論", "心得", "感想", "網路",
            "網友", "朋友", "同事", "家人", "價錢", "便宜", "貴", "錢"
        ]
        if any(indicator in phrase for indicator in non_food_indicators):
            return False
            
        # 5. 檢查是否為服務人員等特殊詞組
        if "服務" in phrase and "人員" in phrase:
            return False
            
        # 6. 檢查是否以特定詞結尾，這些通常不是完整的食物實體
        if phrase.endswith("的") or phrase.endswith("了") or phrase.endswith("很") or phrase.endswith("也") or phrase.endswith("都"):
            return False
            
        # 7. 檢查是否為食物+設施的組合詞（例如：拉麵店、咖啡廳）
        facility_terms = ["店", "館", "餐廳", "廳", "攤", "屋", "小吃"]
        if any(term in phrase for term in facility_terms):
            return False
            
        # 預設不相關，由零射分類模型進一步確認
        return False
            
    def test_fake_post_analysis(self):
        # 開始計時
        total_start_time = time.time()
        
        # 模型參數設定
        zero_shot_threshold = 0.75  # 零射模型信心閾值
        max_phrase_length = 6      # 食物詞組最大長度限制
        
        # 特殊處理食物詞列表 (無需經過模型判斷的核心食物詞)
        core_food_terms = [
            "火鍋", "壽司", "牛排", "冰淇淋", "拉麵", "小菜", "燒肉", "霜淇淋", 
            "蛋糕", "豆腐", "雞肉", "豬排", "蝦仁", "飯", "麵", "奶茶", "咖哩", 
            "鴨", "牛肉", "魚", "紅豆", "抹茶", "巧克力", "芒果", "檸檬", "馬鈴薯", 
            "蒜", "雞", "炸雞", "炸豬排", "海鮮", "燉飯", "鹽酥雞", "椒麻雞"
        ]
        
        # 排除詞庫設定
        exclude_nouns = set(["東西", "餐點", "料理", "食物", "東西們", "感覺", "服務", "這家", "下次", "這次"])
        exclude_foods = set([
            # 描述性、泛指、雜訊詞
            "這家", "這個", "口", "有機", "份", "公共", "一", "一份", "本家", "家", "價格", 
            "湯頭", "質感", "份量", "口味", "部分", "一些", "這家", "新品", "主廚手藝", "香氣", 
            "甜點部分", "肉質", "肉品", "味噌湯鹹度", "紅豆餡", "紅豆餅外皮", "冰塊", "茶香", 
            "抹茶布丁口感", "九層塔香氣", "巧克力慕斯蛋", "糕", "白飯", "餅皮", "餡", "肉", 
            "甜麵醬", "青菜", "菜", "飲料", "醬料", "蔥段", "布丁口感", "慕斯蛋糕", "蛋糕味道",
            # 增加更多排除詞
            "冰淇淋口味", "拉麵湯頭", "牛肉麵湯頭", "義大利麵蒜味", "烏龍麵Q彈", "姊姊烤"
        ])
        # 直接指定測試資料
        fake_posts = [
            "樓上風景很好看，點了昆布火鍋和味噌火鍋，飲料還有可以加到火鍋的菜跟醬料很多元，霜淇淋可以自己做，還有很多小料可以加，超讚👍👍，下次還要來吃😊",  
        ]
        # 詞庫設定
        flavor_keywords = set(["鹹", "甜", "辣", "苦", "酸", "香", "口味", "酥脆", "濃郁", "綿密", 
                             "清爽", "香濃", "鮮嫩", "爽口", "Q彈", "多汁", "彈牙", "入味",
                             "香脆", "嫩滑", "香甜", "鬆軟", "滑順", "酸甜", "香辣", "軟嫩", "微酸"])
        
        # 零射分類的標籤
        candidate_labels = ["食物", "食物種類", "食物口味"]
        
        # 初始化各種計數器
        food_counter = Counter()      # 食物出現次數
        flavor_counter = Counter()    # 口味詞出現次數
        nn_counter = Counter()        # 名詞+名詞組合
        nnn_counter = Counter()       # 三連詞名詞組合
        nnnn_counter = Counter()      # 四連詞名詞組合
        na_counter = Counter()        # 名詞+形容詞組合
        an_counter = Counter()        # 形容詞+名詞組合

        for idx, content in enumerate(tqdm(fake_posts, desc="分析貼文")):
            start_time = time.time()
            print(f"\n=== 貼文{idx+1} ===")
            print("原文：", content)
            
            # 1. 斷詞 → 詞性標註
            ws = self.ws_driver([content])[0]
            pos = self.pos_driver([ws])[0]
            
            # 2. 收集所有可能候選詞
            ner_candidates = set()  # NER 抓出的候選詞
            ckip_candidates = set() # CKIP 斷詞抓出的候選詞
            phrase_candidates = set() # 各種組合詞
            ckip_flavors = set()  # CKIP 抓出的口味詞
            
            # 2.1 NER 抓產品實體
            ner_results = self.ner(content)
            for ent in ner_results:
                if ent['entity_group'] == 'PRODUCT':
                    phrase = ent['word']
                    if phrase not in exclude_foods and len(phrase) <= max_phrase_length:
                        ner_candidates.add(phrase)
            
            # 2.2 CKIP 斷詞抓食物詞和組合詞
            cur_phrase = []
            
            # 預處理: 尋找特定組合詞
            special_food_phrases = ["鹽酥雞", "椒麻雞", "炸豬排", "霜淇淋", "冰淇淋", "宮保雞丁鐵板麵"]
            for phrase in special_food_phrases:
                if phrase in content:
                    ckip_candidates.add(phrase)
                    print(f"添加特殊食物詞: {phrase}")
            
            for i in range(len(ws)):
                w, p = ws[i], pos[i]
                
                # 收集連續名詞短語
                if p.startswith("N"):
                    cur_phrase.append(w)
                else:
                    if cur_phrase:
                        phrase = ''.join(cur_phrase)
                        if (phrase not in exclude_nouns and 
                            phrase not in exclude_foods and 
                            len(phrase) <= max_phrase_length):
                            ckip_candidates.add(phrase)
                        cur_phrase = []
                
                # 抓取口味詞
                if w in flavor_keywords:
                    ckip_flavors.add(w)
                
                # 各種詞性組合抓取
                # 1. 名詞+名詞組合
                if p.startswith("N") and i+1 < len(ws) and pos[i+1].startswith("N"):
                    nn_phrase = ws[i] + ws[i+1]
                    if (nn_phrase not in exclude_foods and 
                        ws[i] not in exclude_foods and 
                        ws[i+1] not in exclude_foods and
                        len(nn_phrase) <= max_phrase_length):
                        # 檢查該組合詞是否與食物相關
                        component_ws = [ws[i], ws[i+1]]  # 組合詞的原始斷詞結果
                        if self.is_food_related(nn_phrase, core_food_terms, component_ws):
                            phrase_candidates.add(nn_phrase)
                            nn_counter[nn_phrase] += 1
                            print(f"添加名詞+名詞組合詞: {nn_phrase}")
                        else:
                            print(f"排除名詞+名詞組合詞: {nn_phrase}（非食物相關）")
                
                # 2. 形容詞+名詞組合
                if p.startswith("A") and i+1 < len(ws) and pos[i+1].startswith("N"):
                    an_phrase = ws[i] + ws[i+1]
                    if (an_phrase not in exclude_foods and 
                        ws[i] not in exclude_foods and 
                        ws[i+1] not in exclude_foods and
                        len(an_phrase) <= max_phrase_length):
                        # 檢查該組合詞是否與食物相關
                        component_ws = [ws[i], ws[i+1]]  # 組合詞的原始斷詞結果
                        # 特別考慮形容詞可能是口味詞
                        if self.is_food_related(an_phrase, core_food_terms, component_ws) or ws[i] in flavor_keywords:
                            phrase_candidates.add(an_phrase)
                            an_counter[an_phrase] += 1
                
                # 3. 名詞+形容詞組合
                if p.startswith("N") and i+1 < len(ws) and pos[i+1].startswith("A"):
                    na_phrase = ws[i] + ws[i+1]
                    if (na_phrase not in exclude_foods and 
                        ws[i] not in exclude_foods and 
                        ws[i+1] not in exclude_foods and
                        len(na_phrase) <= max_phrase_length):
                        # 檢查該組合詞是否與食物相關
                        component_ws = [ws[i], ws[i+1]]  # 組合詞的原始斷詞結果
                        # 特別考慮形容詞可能是口味詞
                        if self.is_food_related(na_phrase, core_food_terms, component_ws) or ws[i+1] in flavor_keywords:
                            phrase_candidates.add(na_phrase)
                            na_counter[na_phrase] += 1
                
                # 4. 三連詞組合 (N+N+N)
                if (p.startswith("N") and i+2 < len(ws) and 
                    pos[i+1].startswith("N") and pos[i+2].startswith("N")):
                    nnn_phrase = ws[i] + ws[i+1] + ws[i+2]
                    if (nnn_phrase not in exclude_foods and 
                        ws[i] not in exclude_foods and 
                        ws[i+1] not in exclude_foods and 
                        ws[i+2] not in exclude_foods and
                        len(nnn_phrase) <= max_phrase_length):
                        # 檢查該組合詞是否與食物相關
                        component_ws = [ws[i], ws[i+1], ws[i+2]]  # 組合詞的原始斷詞結果
                        if self.is_food_related(nnn_phrase, core_food_terms, component_ws):
                            phrase_candidates.add(nnn_phrase)
                            nnn_counter[nnn_phrase] += 1
                
                # 5. 四連詞組合 (N+N+N+N)
                if (p.startswith("N") and i+3 < len(ws) and 
                    pos[i+1].startswith("N") and 
                    pos[i+2].startswith("N") and 
                    pos[i+3].startswith("N")):
                    nnnn_phrase = ws[i] + ws[i+1] + ws[i+2] + ws[i+3]
                    if (nnnn_phrase not in exclude_foods and 
                        ws[i] not in exclude_foods and 
                        ws[i+1] not in exclude_foods and 
                        ws[i+2] not in exclude_foods and 
                        ws[i+3] not in exclude_foods and
                        len(nnnn_phrase) <= max_phrase_length):
                        # 檢查該組合詞是否與食物相關
                        component_ws = [ws[i], ws[i+1], ws[i+2], ws[i+3]]  # 組合詞的原始斷詞結果
                        if self.is_food_related(nnnn_phrase, core_food_terms, component_ws):
                            phrase_candidates.add(nnnn_phrase)
                            nnnn_counter[nnnn_phrase] += 1
            
            # 處理最後可能剩下的名詞片語
            if cur_phrase:
                phrase = ''.join(cur_phrase)
                if (phrase not in exclude_nouns and 
                    phrase not in exclude_foods and 
                    len(phrase) <= max_phrase_length):
                    ckip_candidates.add(phrase)
            
            # 3. 合併所有來源的候選詞，準備進行 zero-shot 過濾
            # 檢查是否含有特定食物詞組
            special_foods = ["鹽酥雞", "椒麻雞", "炸豬排", "炸雞"]
            for food in special_foods:
                if food in content and food not in ner_candidates and food not in ckip_candidates:
                    # 直接添加特定食物詞，不經過其他判斷
                    phrase_candidates.add(food)
                    
            all_candidates = ner_candidates | ckip_candidates | phrase_candidates
            
            # 額外過濾包含「湯頭」、「口味」等的組合詞
            filtered_candidates = set()
            for candidate in all_candidates:
                if not any(term in candidate for term in ["湯頭", "口味", "味道", "姊姊", "服務", "店", "餐廳", "館"]):
                    filtered_candidates.add(candidate)
                    
            all_candidates = filtered_candidates
            
            # 4. 僅對合併後的候選詞集一次性執行 zero-shot 過濾
            # 此處不重複過濾已存在的組合詞，提高效率
            filtered_foods = set()
            if all_candidates:
                all_candidates_list = list(all_candidates)
                z_results = self.zero_shot(
                    all_candidates_list, 
                    candidate_labels=candidate_labels,
                    multi_label=False
                )
                
                # 如果只有單個詞，確保結果以列表形式處理
                if isinstance(z_results, dict):
                    z_results = [z_results]
                
                # 特定食物關鍵詞列表 - 這些詞即使分數較低也會被視為食物
                core_food_keywords = ["火鍋", "壽司", "牛排", "冰淇淋", "拉麵", "燒肉", "豬排", "麵", "飯", 
                                     "奶茶", "炸雞", "鹽酥雞", "椒麻雞", "蛋糕", "豆腐"] 
                
                # 過濾出信心分數高於閾值的食物詞
                for i, phrase in enumerate(all_candidates_list):
                    score = z_results[i]['scores'][0]
                    label = z_results[i]['labels'][0]
                    
                    # 判斷條件：1. 信心分數高 或 2. 是核心食物關鍵詞
                    if (label in candidate_labels and score > zero_shot_threshold) or \
                       any(food_key in phrase for food_key in core_food_keywords):
                        # 排除「這家XX」「下次」等特殊詞
                        if not any(exclude in phrase for exclude in ["這家", "下次", "服務", "湯頭", "口味"]):
                            # 確保不是以「的」、「很」結尾的片語
                            if not phrase.endswith("的") and not phrase.endswith("很") and not phrase.endswith("了"):
                                filtered_foods.add(phrase)
                                food_counter[phrase] += 1
                    
                # 記錄口味詞
                for flavor in ckip_flavors:
                    flavor_counter[flavor] += 1
                    
                print(f"候選詞數量：NER({len(ner_candidates)})、CKIP({len(ckip_candidates)})、組合({len(phrase_candidates)})")
                print(f"偵測到食物：{sorted(filtered_foods)}")
                print(f"偵測到口味：{sorted(ckip_flavors)}")
                print(f"分析耗時: {time.time() - start_time:.2f} 秒")
            else:
                print("未偵測到食物相關詞")

        total_time = time.time() - total_start_time
        print(f"\n{'='*50}")
        print(f"【食物實體分析報告】(總耗時: {total_time:.2f} 秒)")
        print(f"{'='*50}")
        
        # 1. 食物出現次數
        print("\n【1. 食物出現次數】")
        if food_counter:
            for food, cnt in food_counter.most_common():
                print(f"  {food}: {cnt}")
        else:
            print("  無食物詞被偵測到")
        
        # 2. 口味出現次數
        print("\n【口味詞出現次數】")
        if flavor_counter:
            for flavor, cnt in flavor_counter.most_common():
                print(f"  {flavor}: {cnt}")
        else:
            print("  無口味詞被偵測到")
        
        # 3. 名詞+名詞組合（食物種類）統計
        print("\n【名詞+名詞組合（食物種類）】")
        if nn_counter:
            for phrase, cnt in nn_counter.most_common(15):  # 只顯示前15名
                print(f"  {phrase}: {cnt}")
            if len(nn_counter) > 15:
                print(f"  ...共 {len(nn_counter)} 種組合 (僅顯示前15名)")
        else:
            print("  無名詞+名詞組合被偵測到")
        
        # 4. 形容詞+名詞組合
        print("\n【形容詞+名詞組合】")
        if an_counter:
            for phrase, cnt in an_counter.most_common(15):
                print(f"  {phrase}: {cnt}")
            if len(an_counter) > 15:
                print(f"  ...共 {len(an_counter)} 種組合 (僅顯示前15名)")
        else:
            print("  無形容詞+名詞組合被偵測到")
            
        # 5. 名詞+形容詞組合
        print("\n【名詞+形容詞組合（口味描述）】")
        if na_counter:
            for phrase, cnt in na_counter.most_common(15):
                print(f"  {phrase}: {cnt}")
            if len(na_counter) > 15:
                print(f"  ...共 {len(na_counter)} 種組合 (僅顯示前15名)")
        else:
            print("  無名詞+形容詞組合被偵測到")
        
        # 6. 三連詞與四連詞名詞組合
        print("\n【三連詞名詞組合】")
        if nnn_counter:
            for phrase, cnt in nnn_counter.most_common(15):
                print(f"  {phrase}: {cnt}")
            if len(nnn_counter) > 15:
                print(f"  ...共 {len(nnn_counter)} 種組合 (僅顯示前15名)")
        else:
            print("  無三連詞組合被偵測到")
            
        print("\n【四連詞名詞組合】")
        if nnnn_counter:
            for phrase, cnt in nnnn_counter.most_common(15):
                print(f"  {phrase}: {cnt}")
            if len(nnnn_counter) > 15:
                print(f"  ...共 {len(nnnn_counter)} 種組合 (僅顯示前15名)")
        else:
            print("  無四連詞組合被偵測到")
        
        # 7. 將所有組合類型與單一名詞一起合併，做最長唯一化，統一顯示於「目前有吃的食物有哪些」
        print("\n【目前有吃的食物有哪些】")
        # 收集所有 relevant 食物詞
        all_food_candidates = set()
        # 單一名詞
        all_food_candidates.update([food for food, cnt in food_counter.most_common() if not any(x in food for x in ["這家", "服務", "下次"]) and food not in exclude_foods])
        # 名詞+名詞組合
        all_food_candidates.update([phrase for phrase in nn_counter.keys() if not any(x in phrase for x in ["這家", "服務", "下次"]) and phrase not in exclude_foods])
        # 形容詞+名詞組合
        all_food_candidates.update([phrase for phrase in an_counter.keys() if not any(x in phrase for x in ["這家", "服務", "下次"]) and phrase not in exclude_foods])
        # 名詞+形容詞組合
        all_food_candidates.update([phrase for phrase in na_counter.keys() if not any(x in phrase for x in ["這家", "服務", "下次"]) and phrase not in exclude_foods])
        # 三連詞名詞組合
        all_food_candidates.update([phrase for phrase in nnn_counter.keys() if not any(x in phrase for x in ["這家", "服務", "下次"]) and phrase not in exclude_foods])
        # 四連詞名詞組合
        all_food_candidates.update([phrase for phrase in nnnn_counter.keys() if not any(x in phrase for x in ["這家", "服務", "下次"]) and phrase not in exclude_foods])

        # 只保留最長、最具體的（如有卡拉雞腿與卡拉雞腿堡，只留卡拉雞腿堡）
        all_food_candidates = sorted(all_food_candidates, key=lambda x: -len(x))  # 先長後短
        # 只要某個食物名稱是另一個更長名稱的子字串（不論開頭或中間），就不顯示短的那個
        filtered_foods = []
        for food in all_food_candidates:
            if not any(food != other and food in other for other in all_food_candidates):
                filtered_foods.append(food)
        # 去重
        filtered_foods = list(dict.fromkeys(filtered_foods))
        # 過濾設施類詞彙
        facility_terms = ["店", "廳", "館", "餐廳", "屋", "攤", "小吃"]
        filtered_foods = [food for food in filtered_foods if not any(food.endswith(term) for term in facility_terms)]
        filtered_foods = [food for food in filtered_foods if not food.endswith("皮")]
        filtered_foods = [food for food in filtered_foods if not food.endswith("外")]
        if filtered_foods:
            for food in filtered_foods:
                print(f"  {food}")
        else:
            print("  無偵測到食物")

if __name__ == "__main__":
    print("==== 食物實體專用 Pipeline 啟動中 ====\n")
    start_time = time.time()
    CKIPTransformersTests.setUpClass()
    tester = CKIPTransformersTests()
    tester.test_fake_post_analysis()
    print(f"\n==== 分析完成，總執行時間: {time.time() - start_time:.2f} 秒 ====\n")