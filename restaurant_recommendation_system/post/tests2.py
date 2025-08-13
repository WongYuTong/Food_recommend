from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from tqdm import tqdm
import re
from collections import Counter

class CKIPTransformersTests:
    @classmethod
    def setUpClass(cls):
        cls.ws_driver = CkipWordSegmenter(model="bert-base")
        cls.pos_driver = CkipPosTagger(model="bert-base")
        cls.zero_shot = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")
        cls.sentiment = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        # 加入 NER pipeline
        cls.ner = pipeline("ner", model="ckiplab/bert-base-chinese-ner", tokenizer="ckiplab/bert-base-chinese-ner", aggregation_strategy="simple")

    def test_fake_post_analysis(self):
        exclude_nouns = set(["東西", "餐點", "料理", "食物", "東西們"])
        # 新增排除泛用詞與描述性詞彙
        exclude_foods = set([
            # 描述性、泛指、雜訊詞
            "口","有機","份","公共","一","一份","本家","家","價格", "湯頭", "質感", "份量", "口味", "部分", "一些", "這家", "新品", "主廚手藝", "香氣", "甜點部分", "肉質", "肉品", "味噌湯鹹度", "紅豆餡", "紅豆餅外皮", "冰塊", "茶香", "抹茶布丁口感", "九層塔香氣", "巧克力慕斯蛋", "糕", "白飯", "餅皮", "餡", "肉", "甜麵醬", "青菜", "菜", "飲料", "醬料", "蔥段", "布丁口感", "慕斯蛋糕", "蛋糕味道"
        ])
        # 讀取 all_reviews.json 前 50 則非 "無評論" 的評論
        import json
        with open("all_reviews.json", "r", encoding="utf-8") as f:
            all_reviews = json.load(f)
        fake_posts = []
        for item in all_reviews:
            review = item.get("評論內容", "").strip()
            if review and review != "無評論":
                fake_posts.append(review)
            if len(fake_posts) >=100:
                break
        # 可自訂常見食物/口味詞庫
        flavor_keywords = set(["鹹", "甜", "辣", "苦", "酸", "香", "口味"])
        food_keywords = set([
            "火鍋", "壽司", "牛排", "冰淇淋", "拉麵", "小菜", "燒肉", "霜淇淋", "蛋糕", "布丁", "雞肉", "豬排", "蝦仁", "飯", "麵", "餅", "奶茶", "咖哩", "鴨", "牛肉", "雞", "魚", "豆腐", "紅豆", "抹茶", "巧克力", "芒果", "檸檬", "九層塔", "馬鈴薯", "蒜香", "椒麻", "炸雞", "炸豬排", "冰沙", "燉飯", "義大利麵", "甜點", "慕斯", "小黃瓜"])
        # 移除泛用詞如湯頭、青菜、飲料、醬料、餡、餅皮、蔥段、餅、餡、家火鍋等
        food_counter = Counter()
        flavor_counter = Counter()

        candidate_labels = ["食物", "食物種類", "食物口味"]
        # 統計名詞+名詞、三連詞、四連詞、名詞+形容詞組合
        nn_counter = Counter()  # 名詞+名詞
        nnn_counter = Counter() # 三連詞
        nnnn_counter = Counter() # 四連詞
        na_counter = Counter()  # 名詞+形容詞

        for idx, content in enumerate(tqdm(fake_posts, desc="分析貼文")):
            print(f"\n=== 貼文{idx+1} ===")
            print("原文：", content)
            # 1. 先用 NER 抽取所有產品類（部分食物會被標為產品）
            ner_results = self.ner(content)
            ner_foods = set([ent['word'] for ent in ner_results if ent['entity_group'] == 'PRODUCT'])
            # 2. CKIP 斷詞抓食物/口味關鍵字
            ws = self.ws_driver([content])[0]
            pos = self.pos_driver([ws])[0]
            ckip_foods = set()
            ckip_flavors = set()
            cur_phrase = []
            for i in range(len(ws)):
                w, p = ws[i], pos[i]
                # 名詞+名詞組合（只要組合不在 exclude_foods，且兩詞都不在 exclude_foods）
                if p.startswith("N") and i+1 < len(ws):
                    if pos[i+1].startswith("N"):
                        nn_phrase = ws[i] + ws[i+1]
                        if (
                            nn_phrase not in exclude_foods
                            and ws[i] not in exclude_foods
                            and ws[i+1] not in exclude_foods
                        ):
                            nn_counter[nn_phrase] += 1
                    # 三連詞
                    if i+2 < len(ws) and pos[i+1].startswith("N") and pos[i+2].startswith("N"):
                        nnn_phrase = ws[i] + ws[i+1] + ws[i+2]
                        if (
                            nnn_phrase not in exclude_foods
                            and ws[i] not in exclude_foods
                            and ws[i+1] not in exclude_foods
                            and ws[i+2] not in exclude_foods
                        ):
                            nnn_counter[nnn_phrase] += 1
                    # 四連詞
                    if i+3 < len(ws) and pos[i+1].startswith("N") and pos[i+2].startswith("N") and pos[i+3].startswith("N"):
                        nnnn_phrase = ws[i] + ws[i+1] + ws[i+2] + ws[i+3]
                        if (
                            nnnn_phrase not in exclude_foods
                            and ws[i] not in exclude_foods
                            and ws[i+1] not in exclude_foods
                            and ws[i+2] not in exclude_foods
                            and ws[i+3] not in exclude_foods
                        ):
                            nnnn_counter[nnnn_phrase] += 1
                    # 名詞+形容詞
                    if pos[i+1].startswith("A"):
                        na_phrase = ws[i] + ws[i+1]
                        if ws[i] not in exclude_foods and ws[i+1] not in exclude_foods and na_phrase not in exclude_foods:
                            na_counter[na_phrase] += 1
                # 原本的名詞片語擷取
                if p.startswith("N"):
                    cur_phrase.append(w)
                else:
                    if cur_phrase:
                        phrase = ''.join(cur_phrase)
                        # 過濾：只保留非雜訊詞、長度<=6且無空格
                        if (
                            phrase not in exclude_nouns
                            and phrase not in exclude_foods
                            and len(phrase) <= 6
                            and ' ' not in phrase
                        ):
                            ckip_foods.add(phrase)
                        cur_phrase = []
                    # 口味詞
                    if w in flavor_keywords:
                        ckip_flavors.add(w)
            if cur_phrase:
                phrase = ''.join(cur_phrase)
                if (
                    phrase not in exclude_nouns
                    and phrase not in exclude_foods
                    and len(phrase) <= 6
                    and ' ' not in phrase
                ):
                    ckip_foods.add(phrase)
            # 3. 合併 NER 與 CKIP 結果，僅排除 exclude_foods
            all_candidates = (ner_foods | ckip_foods) - exclude_foods
            filtered_foods = set()
            for phrase in all_candidates:
                # 只要長度<=6且無空格
                if (
                    len(phrase) <= 6
                    and ' ' not in phrase
                ):
                    # zero-shot 判斷是否為食物/口味主題
                    z_result = self.zero_shot(phrase, candidate_labels=candidate_labels)
                    if z_result['labels'][0] in candidate_labels and z_result['scores'][0] > 0.5:
                        filtered_foods.add(phrase)
            for food in filtered_foods:
                food_counter[food] += 1
            for flavor in ckip_flavors:
                flavor_counter[flavor] += 1
            print(f"偵測到食物：{sorted(filtered_foods)}")
            print(f"偵測到口味：{sorted(ckip_flavors)}")

        print("\n=== 食物/口味統計 ===")
        print("食物出現次數：")
        for food, cnt in food_counter.most_common():
            print(f"  {food}: {cnt}")
        print("口味出現次數：")
        for flavor, cnt in flavor_counter.most_common():
            print(f"  {flavor}: {cnt}")
        print("\n名詞+名詞組合（食物種類）統計：")
        for phrase, cnt in nn_counter.most_common():
            print(f"  {phrase}: {cnt}")
        print("三連詞名詞組合：")
        for phrase, cnt in nnn_counter.most_common():
            print(f"  {phrase}: {cnt}")
        print("四連詞名詞組合：")
        for phrase, cnt in nnnn_counter.most_common():
            print(f"  {phrase}: {cnt}")
        print("名詞+形容詞組合（口味描述）統計：")
        for phrase, cnt in na_counter.most_common():
            print(f"  {phrase}: {cnt}")
        # 顯示單一名詞（食物）統計
        print("\n單一名詞（食物）統計：")
        # 單一名詞 = 出現在 food_counter 但不在 nn_counter 的詞
        nn_set = set(nn_counter.keys())
        for food, cnt in food_counter.most_common():
            if all(food not in phrase for phrase in nn_set):
                print(f"  {food}: {cnt}")

if __name__ == "__main__":
    CKIPTransformersTests.setUpClass()
    tester = CKIPTransformersTests()
    tester.test_fake_post_analysis()