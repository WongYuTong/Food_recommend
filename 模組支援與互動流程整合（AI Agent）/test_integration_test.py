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
    print(colored("🎯 整合測試：功能一 → 四 → 二 + 關鍵字驗證 + 排除驗證", "cyan"))
    print("--------------------------------------------------")

    success_count = 0
    keyword_pass_case_count = 0
    exclude_pass_case_count = 0

    for idx, item in enumerate(INTEGRATION_TEST_INPUTS):
        if isinstance(item, str):
            text = item
            expected_keywords = []
            expected_excludes = []
            min_results = None
            allow_backfill = None
        else:
            text = item.get("text", "")
            expected_keywords = item.get("expected_keywords", [])
            expected_excludes = item.get("expected_excludes", [])
            min_results = item.get("min_results", None)
            allow_backfill = item.get("allow_backfill", None)

        print(f"📝 測試 {idx + 1}: {text}")

        payload = {
            "text": text,
            "user_input": text
        }
        # 若題目有帶 allow_backfill 就覆蓋
        if allow_backfill is not None:
            payload["allow_backfill"] = bool(allow_backfill)

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
                # 顯示伺服器端實際擷取到的排除詞（方便判斷為何變少）
                server_excluded = result.get("excluded_items", [])
                if server_excluded:
                    print(colored(f"🧹 伺服器排除詞：{server_excluded}", "blue"))

                restaurants = result.get("data", {}).get("results", [])

                if restaurants:
                    print(colored(f"✅ 成功回傳 {len(restaurants)} 間推薦餐廳", "green"))

                    # ✅ min_results 檢查：補位模式才當錯誤；純過濾模式顯示提醒
                    if isinstance(min_results, int) and len(restaurants) < min_results:
                        if payload.get("allow_backfill", False):
                            print(colored(f"   ❌ 回傳餐廳數不足（期望至少 {min_results} 間；補位已開啟）", "red"))
                        else:
                            print(colored(
                                f"   ℹ️ 純過濾模式回傳 {len(restaurants)} 間（測試集小，少於 {min_results} 屬正常）",
                                "yellow"
                            ))

                    # 👉 這兩個旗標是「此題」層級
                    all_keywords_ok_for_case = True if expected_keywords else True
                    all_excludes_ok_for_case = True

                    for r in restaurants:
                        name = r.get("name", "❓")
                        reason = r.get("recommend_reason", "")
                        tags = r.get("tags", []) or r.get("matched_tags", [])

                        print(f"   🍽️ {name} → {reason}")

                        # 🔎 關鍵詞驗證（針對此餐廳）
                        if expected_keywords:
                            missed = [kw for kw in expected_keywords if kw not in reason]
                            if missed:
                                print(colored(f"   ❌ 未命中關鍵詞: {missed}", "yellow"))
                                all_keywords_ok_for_case = False
                            else:
                                print(colored(f"   ✅ 關鍵詞全部命中", "green"))

                        # 🔎 排除驗證（針對此餐廳）
                        if expected_excludes:
                            include_flag = any(
                                ex in name or any(ex in tag for tag in (tags or []))
                                for ex in expected_excludes
                            )
                            if include_flag:
                                print(colored(f"   ❌ 排除條件未生效，命中排除詞：{expected_excludes}", "red"))
                                all_excludes_ok_for_case = False

                    # 👉 每「題」的總結
                    if expected_keywords:
                        if all_keywords_ok_for_case:
                            keyword_pass_case_count += 1
                    else:
                        keyword_pass_case_count += 1

                    if all_excludes_ok_for_case:
                        print(colored("   ✅ 排除條件全部生效", "cyan"))
                        exclude_pass_case_count += 1

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

    # ⚠️ 提醒：測試集僅含 5 間餐廳
    print(colored("\n⚠️ 注意：目前的測試資料集僅含 5 間餐廳，若有排除條件，回傳少於 5 間屬正常。", "yellow"))

    print(colored(f"\n📊 測試完成：共 {success_count}/{total} 筆成功回傳", "cyan"))
    print(colored(f"🧠 關鍵詞命中（按題）：{keyword_pass_case_count}/{total}", "cyan"))
    print(colored(f"🧹 排除條件命中（按題）：{exclude_pass_case_count}/{total}", "cyan"))

if __name__ == "__main__":
    test_integration()