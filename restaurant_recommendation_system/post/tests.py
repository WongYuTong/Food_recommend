from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from transformers import pipeline
from tqdm import tqdm
import re
from keybert import KeyBERT

class CKIPTransformersTests:
    @classmethod
    def setUpClass(cls):
        # CKIP 斷詞、詞性
        cls.ws_driver = CkipWordSegmenter(model="bert-base")
        cls.pos_driver = CkipPosTagger(model="bert-base")
        # Zero-shot 分類模型（支援繁體中文）
        cls.zero_shot = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")
        # 三分類情感分析模型（多語，支援繁體中文）
        cls.sentiment = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        # KeyBERT 關鍵詞抽取模型
        cls.kw_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')

    def test_fake_post_analysis(self):
        fake_posts = [
            "這家火鍋的湯頭很棒，服務生態度親切，價格也很合理，下次還會再來！",
            "壽司不新鮮，環境有點髒亂，服務也不太好。",
            "牛排很好吃，CP值高，推薦給大家！",
            "冰淇淋口味普通，服務速度很慢。",
            "拉麵湯頭太鹹，價格偏貴，但環境很舒適。"
        ]
        # 使用「其他」分類
        candidate_labels = ["食物", "服務", "價格", "環境", "其他"]
        sentiment_labels = ["正面", "中立", "負面"]

        # 總結性質的關鍵詞保持不變
        overall_keywords = ["再來", "推薦", "不會再來", "下次", "大家", "值得", "不推", "不推薦"]

        for idx, content in enumerate(tqdm(fake_posts, desc="分析貼文")):
            print(f"\n=== 貼文{idx+1} ===")
            print("原文：", content)

            # 斷句，包含逗號
            sentences = re.split(r'[。！？!？，,]', content)
            sentences = [s for s in sentences if s.strip()]

            # 斷詞與詞性標註（每句）
            ws_list = self.ws_driver(sentences)
            pos_list = self.pos_driver(ws_list)

            last_keywords = None
            sentence_to_keywords = []
            keyword_to_category = {}
            keyword_to_sentences = {}

            for sent, ws, pos in zip(sentences, ws_list, pos_list):
                # 判斷是否為總結句，但不再自動歸為「其他」
                is_summary = any(kw in sent for kw in overall_keywords)
                
                # 移除短句自動歸類為「其他」的邏輯
                # is_summary = is_summary or len(sent) < 6
                
                # 用 KeyBERT 抽取每句的關鍵詞（top 1~2）
                keywords = [kw for kw, score in self.kw_model.extract_keywords(sent, top_n=2)]
                print(f"句子：「{sent}」→ 關鍵詞：{keywords}")
                if keywords:
                    last_keywords = keywords
                    for keyword in keywords:
                        if keyword not in keyword_to_category:
                            # 若為總結句，直接分類為「其他」
                            if is_summary:
                                best_label = "其他"
                                score = 1.0
                            else:
                                result = self.zero_shot(keyword, candidate_labels=candidate_labels)
                                best_label = result['labels'][0]
                                score = result['scores'][0]
                            
                            # 如果關鍵詞明顯與價格相關，優先分類為「價格」
                            if "價格" in keyword or "貴" in keyword or "便宜" in keyword or "CP" in keyword:
                                best_label = "價格"
                                score = 1.0
                            
                            # 如果關鍵詞明顯與食物相關，優先分類為「食物」
                            if any(food in keyword for food in ["湯頭", "口味", "牛排", "拉麵", "冰淇淋", "壽司"]):
                                best_label = "食物"
                                score = 1.0
                                
                            if best_label != "其他" and score <= 0.5:
                                continue
                            keyword_to_category[keyword] = best_label
                            keyword_to_sentences.setdefault(keyword, []).append(sent)
                else:
                    # 無關鍵詞，補述上一個關鍵詞
                    if last_keywords:
                        for keyword in last_keywords:
                            keyword_to_sentences.setdefault(keyword, []).append(sent)
                sentence_to_keywords.append(last_keywords)

            # 每個分類的情感分數累加
            category_sentiments = {cat: [] for cat in candidate_labels}

            # 針對每個關鍵詞的所有相關句子做情感分析
            for keyword, cat in keyword_to_category.items():
                print(f"\n  關鍵詞：{keyword}（分類：{cat}）")
                for sent in keyword_to_sentences.get(keyword, []):
                    sent_result = self.sentiment(sent, candidate_labels=sentiment_labels)
                    sent_label = sent_result['labels'][0]
                    sent_score = sent_result['scores'][0]
                    print(f"    句子：「{sent}」→ 情感：{sent_label}（分數：{sent_score:.2f}）")
                    # 轉換為分數：正面+1，中立0，負面-1
                    if sent_label == "正面":
                        score_val = sent_score
                    elif sent_label == "負面":
                        score_val = -sent_score
                    else:
                        score_val = 0
                    category_sentiments[cat].append(score_val)

            # 顯示分類與情感分析加總結果
            print("\n分類與情感分析加總結果：")
            for cat, scores in category_sentiments.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    # 判斷總體情感
                    if avg_score > 0.2:
                        overall = "正面"
                    elif avg_score < -0.2:
                        overall = "負面"
                    else:
                        overall = "中立"
                    print(f"  {cat}：平均情感分數 {avg_score:.2f}，細項：{scores}，總體：{overall}")

if __name__ == "__main__":
    CKIPTransformersTests.setUpClass()
    tester = CKIPTransformersTests()
    tester.test_fake_post_analysis()