from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from transformers import pipeline
from tqdm import tqdm
import re

class CKIPTransformersTests:
    @classmethod
    def setUpClass(cls):
        cls.ws_driver = CkipWordSegmenter(model="bert-base")
        cls.pos_driver = CkipPosTagger(model="bert-base")
        cls.zero_shot = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")
        cls.sentiment = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")

    def test_fake_post_analysis(self):
        fake_posts = [
            "這家火鍋的湯頭很棒，服務生態度親切，價格也很合理，下次還會再來！",
            "壽司不新鮮，環境有點髒亂，服務也不太好。",
            "牛排很好吃，CP值高，推薦給大家！",
            "冰淇淋口味普通，服務速度很慢。",
            "拉麵湯頭太鹹，價格偏貴，但環境很舒適。",
            "拉麵湯頭很鹹但是我很喜歡XD",
            "拉麵湯頭很鹹，但是我很喜歡XD",
        ]
        candidate_labels = ["食物", "服務", "價格", "環境", "整體"]
        sentiment_labels = ["正面", "中立", "負面"]
        turn_words = ["但是", "但", "可是", "不過"]

        for idx, content in enumerate(tqdm(fake_posts, desc="分析貼文")):
            print(f"\n=== 貼文{idx+1} ===")
            print("原文：", content)

            # 只用句號、驚嘆號、問號斷句，保留逗號內部子句
            sentences = re.split(r'[。！？!？]', content)
            sentences = [s for s in sentences if s.strip()]

            last_food_noun = None  # 記錄最後找到的食物主題詞

            for sent in sentences:
                # 先用逗號切分所有子句
                sub_sentences = re.split(r'[，,]', sent)
                for sub_sent in sub_sentences:
                    if not sub_sent.strip():
                        continue
                    
                    # 如果子句以轉折詞開頭，使用上一個子句的食物主題詞
                    starts_with_turn = False
                    for turn in turn_words:
                        if sub_sent.strip().startswith(turn):
                            starts_with_turn = True
                            if last_food_noun:  # 使用上一個子句的食物主題詞
                                turn_clause = sub_sent.replace(turn, "").strip()
                                ws_turn = self.ws_driver([turn_clause])[0]
                                pos_turn = self.pos_driver([ws_turn])[0]
                                noun_candidates_turn = [w for w, p in zip(ws_turn, pos_turn) if p.startswith("N")]
                                has_food_noun_turn = False
                                has_other_noun_turn = False
                                for noun in noun_candidates_turn:
                                    result = self.zero_shot(noun, candidate_labels=candidate_labels)
                                    best_label = result['labels'][0]
                                    score = result['scores'][0]
                                    if best_label == "食物" and score > 0.5:
                                        has_food_noun_turn = True
                                    elif best_label != "食物" and score > 0.5:
                                        has_other_noun_turn = True
                                        
                                # 只有當轉折後子句沒有自己的主題詞時，才將情感歸屬到上一句的食物主題詞
                                if not has_food_noun_turn and not has_other_noun_turn:
                                    sent_result = self.sentiment(turn_clause, candidate_labels=sentiment_labels)
                                    sent_label = sent_result['labels'][0]
                                    sent_score = sent_result['scores'][0]
                                    print(f"句子：「{sub_sent}」→ 食物主題詞：{last_food_noun}")
                                    print(f"    主要情感（以轉折後為主）：{sent_label}（分數：{sent_score:.2f}）")
                            break
                            
                    if starts_with_turn:
                        continue  # 已處理轉折詞開頭的子句，跳過後續處理
                        
                    # 如果子句中間有轉折詞，做特殊處理
                    if any(w in sub_sent for w in turn_words):
                        sub_sents = re.split(r'(但是|但|可是|不過)', sub_sent)
                        if len(sub_sents) > 1:
                            main_clause = ''.join(sub_sents[:-2]).strip() if len(sub_sents) > 2 else sub_sents[0].strip()
                            turn_clause = sub_sents[-1].strip()
                            if not main_clause or not turn_clause:
                                continue
                            # 1. 先找主句的食物主題詞
                            ws_main = self.ws_driver([main_clause])[0]
                            pos_main = self.pos_driver([ws_main])[0]
                            noun_candidates_main = [w for w, p in zip(ws_main, pos_main) if p.startswith("N")]
                            food_noun = None
                            for noun in noun_candidates_main:
                                result = self.zero_shot(noun, candidate_labels=candidate_labels)
                                best_label = result['labels'][0]
                                score = result['scores'][0]
                                if best_label == "食物" and score > 0.5:
                                    food_noun = noun
                                    last_food_noun = food_noun  # 更新最後找到的食物主題詞
                                    break
                            # 2. 再判斷轉折後子句是否有自己的主題詞（如環境）
                            ws_turn = self.ws_driver([turn_clause])[0]
                            pos_turn = self.pos_driver([ws_turn])[0]
                            noun_candidates_turn = [w for w, p in zip(ws_turn, pos_turn) if p.startswith("N")]
                            has_food_noun_turn = False
                            has_other_noun_turn = False
                            for noun in noun_candidates_turn:
                                result = self.zero_shot(noun, candidate_labels=candidate_labels)
                                best_label = result['labels'][0]
                                score = result['scores'][0]
                                if best_label == "食物" and score > 0.5:
                                    has_food_noun_turn = True
                                elif best_label != "食物" and score > 0.5:
                                    has_other_noun_turn = True
                            # 3. 只有當轉折後子句沒有自己的主題詞時，才將情感歸屬到前一句的食物主題詞
                            if food_noun and not has_food_noun_turn and not has_other_noun_turn:
                                sent_result = self.sentiment(turn_clause, candidate_labels=sentiment_labels)
                                sent_label = sent_result['labels'][0]
                                sent_score = sent_result['scores'][0]
                                print(f"句子：「{sub_sent}」→ 食物主題詞：{food_noun}")
                                print(f"    主要情感（以轉折後為主）：{sent_label}（分數：{sent_score:.2f}）")
                        continue  # 這個子句已處理，跳過
                        
                    # 沒有轉折詞，正常處理
                    main_clause = sub_sent.strip()
                    ws_main = self.ws_driver([main_clause])[0]
                    pos_main = self.pos_driver([ws_main])[0]
                    noun_candidates = [w for w, p in zip(ws_main, pos_main) if p.startswith("N")]
                    food_noun = None
                    for noun in noun_candidates:
                        result = self.zero_shot(noun, candidate_labels=candidate_labels)
                        best_label = result['labels'][0]
                        score = result['scores'][0]
                        if best_label == "食物" and score > 0.5:
                            food_noun = noun
                            break
                    if food_noun:
                        sent_result = self.sentiment(sub_sent, candidate_labels=sentiment_labels)
                        sent_label = sent_result['labels'][0]
                        sent_score = sent_result['scores'][0]
                        print(f"句子：「{sub_sent}」→ 食物主題詞：{food_noun}")
                        print(f"    主要情感：{sent_label}（分數：{sent_score:.2f}）")
                        last_food_noun = food_noun  # 更新最後找到的食物主題詞

if __name__ == "__main__":
    CKIPTransformersTests.setUpClass()
    tester = CKIPTransformersTests()
    tester.test_fake_post_analysis()