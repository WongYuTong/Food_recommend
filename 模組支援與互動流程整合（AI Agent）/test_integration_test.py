import sys
import os
import requests
from termcolor import colored

# ✅ 設定匯入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_module'))

# ✅ 匯入測資
from sample_data import INTEGRATION_TEST_INPUTS

# 🌐 API URL
API_URL = "http://localhost:8000/agent/integration_test/"

def test_integration():
    print(colored("🎯 整合測試：功能一 → 四 → 二 + 關鍵字驗證", "cyan"))
    print("--------------------------------------------------")

    success_count = 0
    keyword_pass_count = 0

    for idx, item in enumerate(INTEGRATION_TEST_INPUTS):
        if isinstance(item, str):
            text = item
            expected_keywords = []
        else:
            text = item.get("text", "")
            expected_keywords = item.get("expected_keywords", [])

        print(f"📝 測試 {idx + 1}: {text}")

        payload = {
            "text": text,
            "user_input": text  # ✅ 傳入使用者輸入給功能二推薦理由補強用
        }


        try:
            response = requests.post(API_URL, json=payload)
            print("🔁 回傳狀態碼:", response.status_code)

            try:
                result = response.json()
            except Exception:
                print(colored("🚨 回傳不是合法的 JSON 格式", "red"))
                print("🔍 原始回傳內容：", response.text)
                continue

            if result.get("status") == "success":
                restaurants = result.get("data", {}).get("results", [])

                if restaurants:
                    print(colored(f"✅ 成功回傳 {len(restaurants)} 間推薦餐廳", "green"))
                    for r in restaurants:
                        name = r.get("name", "❓")
                        reason = r.get("recommend_reason", "")
                        print(f"   🍽️ {name} → {reason}")

                        if expected_keywords:
                            matched = [kw for kw in expected_keywords if kw in reason]
                            missed = [kw for kw in expected_keywords if kw not in reason]

                            if missed:
                                print(colored(f"   ❌ 未命中關鍵詞: {missed}", "yellow"))
                            else:
                                print(colored(f"   ✅ 關鍵詞全部命中", "green"))
                                keyword_pass_count += 1

                    success_count += 1
                else:
                    print(colored("❌ 沒有回傳任何推薦餐廳", "red"))
            else:
                print(colored("❌ 回傳狀態異常或格式錯誤", "red"))
                print("🔍 回傳內容：", result)

        except Exception as e:
            print(colored(f"🚨 發生例外錯誤：{e}", "red"))

        print("--------------------------------------------------")

    total = len(INTEGRATION_TEST_INPUTS)
    print(colored(f"\n📊 測試完成：共 {success_count}/{total} 筆成功回傳", "cyan"))
    print(colored(f"🧠 關鍵詞完全命中筆數：{keyword_pass_count}/{total}", "cyan"))

if __name__ == "__main__":
    test_integration()