import sys
import os
import requests
from termcolor import colored

# ✅ 設定匯入路徑：將 'agent_module' 資料夾加進來
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_module'))

# ✅ 匯入 sample_data 中的 NEGATIVE_INPUTS
from sample_data import NEGATIVE_INPUTS

# 🌐 API URL（統一格式）
API_URL = "http://localhost:8000/agent/extract_negative_conditions/"

def test_negative_condition_extraction():
    print(colored("🎯 功能一：反向推薦條件擷取 測試開始", "cyan"))
    print("--------------------------------------------------")

    success_count = 0
    fail_count = 0

    for idx, item in enumerate(NEGATIVE_INPUTS):
        text = item["text"]
        expected = sorted(item["expected"])

        payload = {
            "type": "text",
            "text": text
        }

        try:
            response = requests.post(API_URL, json=payload)
            result = response.json()

            print(f"📝 測試 {idx + 1}: {text}")
            print("🔁 回傳狀態碼:", response.status_code)

            if result.get("status") == "success" and isinstance(result.get("data", {}).get("excluded"), list):
                excluded_items = sorted(result["data"]["excluded"])

                if set(excluded_items) == set(expected):
                    print(colored(f"✅ 擷取成功，排除項目：{excluded_items}", "green"))
                    success_count += 1
                else:
                    fail_count += 1
                    print(colored("❌ 擷取不一致", "red"))
                    print(f"   預期值：{expected}")
                    print(f"   實際值：{excluded_items}")

                    # 額外提示差異
                    missing = set(expected) - set(excluded_items)
                    extra = set(excluded_items) - set(expected)

                    if missing:
                        print(colored(f"   🔍 少擷取：{list(missing)}", "yellow"))
                    if extra:
                        print(colored(f"   ⚠️ 多擷取：{list(extra)}", "magenta"))

            else:
                fail_count += 1
                print(colored("❌ 擷取失敗或格式異常", "red"))
                print("回傳內容：", result)

        except Exception as e:
            fail_count += 1
            print(colored(f"🚨 發生錯誤：{e}", "red"))

        print("--------------------------------------------------")

    print(colored(f"\n📊 測試完成：共 {success_count + fail_count} 筆", "cyan"))
    print(colored(f"✅ 通過：{success_count}", "green"))
    print(colored(f"❌ 失敗：{fail_count}\n", "red"))

if __name__ == "__main__":
    test_negative_condition_extraction()