import sys
import os
import requests
from termcolor import colored

# ✅ 設定匯入路徑：將 'agent_module' 資料夾加進來
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_module'))

# ✅ 匯入 sample_data 中的 PROMPT_TEST_INPUTS
from sample_data import PROMPT_TEST_INPUTS

# 🌐 API URL（功能三-1：模糊提示）
API_URL = "http://localhost:8000/agent/generate_prompt/"

def test_generate_prompt():
    print(colored("🎯 功能三-1：模糊語句提示 測試開始", "cyan"))
    print("--------------------------------------------------")

    success_count = 0  # 統計通過數量

    for idx, item in enumerate(PROMPT_TEST_INPUTS):
        text = item["text"]
        expected_level = item["expected_level"]  # ✅ 修正這裡

        payload = {
            "type": "text",
            "text": text
        }

        try:
            response = requests.post(API_URL, json=payload)
            result = response.json()

            print(f"📝 測試 {idx + 1}: {text}")
            print("🔁 回傳狀態碼:", response.status_code)

            if result.get("status") == "success" and "level" in result.get("data", {}):
                actual_level = result["data"]["level"]

                if actual_level == expected_level:
                    print(colored(f"✅ 判斷正確，模糊程度：{actual_level}", "green"))
                    success_count += 1
                else:
                    print(colored("❌ 判斷錯誤", "red"))
                    print(f"   預期：{expected_level}")
                    print(f"   實際：{actual_level}")
            else:
                print(colored("❌ 回傳格式異常或缺少欄位", "red"))
                print("回傳內容：", result)

        except Exception as e:
            print(colored(f"🚨 發生錯誤：{e}", "red"))

        print("--------------------------------------------------")

    print(colored(f"\n📊 測試完成：共 {success_count}/{len(PROMPT_TEST_INPUTS)} 筆通過\n", "cyan"))

if __name__ == "__main__":
    test_generate_prompt()
