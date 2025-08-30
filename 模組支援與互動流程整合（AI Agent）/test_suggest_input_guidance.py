import sys
import os
import requests
from termcolor import colored

# ✅ 設定匯入路徑：將 'agent_module' 資料夾加進來
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_module'))

# ✅ 匯入 sample_data 中的 GUIDANCE_TEST_INPUTS
from sample_data import GUIDANCE_TEST_INPUTS

# 🌐 API URL（功能三-2：語意引導建議）
API_URL = "http://localhost:8000/agent/suggest_input_guidance/"

def test_suggest_input_guidance():
    print(colored("🎯 功能三-2：語意引導建議 測試開始", "cyan"))
    print("--------------------------------------------------")

    success_count = 0

    for idx, item in enumerate(GUIDANCE_TEST_INPUTS):
        text = item["text"]
        expected_levels = set(item.get("expected_levels", []))
        expected_keywords = set(item.get("expected_keywords", []))

        payload = {
            "type": "text",
            "text": text
        }

        try:
            response = requests.post(API_URL, json=payload)
            result = response.json()
            data = result.get("data", {})
            actual_levels = set(data.get("level", []))
            guidance = data.get("guidance", "")

            print(f"📝 測試 {idx + 1}: {text}")
            print("🔁 回傳狀態碼:", response.status_code)

            if result.get("status") == "success" and isinstance(actual_levels, set):

                # ✅ 判斷是否包含所有預期分類
                level_ok = expected_levels.issubset(actual_levels)

                # ✅ 判斷 guidance 是否包含所有關鍵字
                keyword_ok = all(keyword in guidance for keyword in expected_keywords)

                if level_ok and keyword_ok:
                    print(colored("✅ 判斷正確", "green"))
                    success_count += 1
                else:
                    print(colored("❌ 判斷錯誤", "red"))
                    if not level_ok:
                        print(f"   ▶ 預期分類：{expected_levels}")
                        print(f"   ▶ 實際分類：{actual_levels}")
                    if not keyword_ok:
                        print(f"   ▶ 預期關鍵字：{expected_keywords}")
                        print(f"   ▶ guidance 回傳：{guidance}")
            else:
                print(colored("❌ 回傳格式錯誤或缺少欄位", "red"))
                print("回傳內容：", result)

        except Exception as e:
            print(colored(f"🚨 發生錯誤：{e}", "red"))

        print("--------------------------------------------------")

    total = len(GUIDANCE_TEST_INPUTS)
    print(colored(f"\n📊 測試完成：共 {success_count}/{total} 筆通過\n", "cyan"))

if __name__ == "__main__":
    test_suggest_input_guidance()
