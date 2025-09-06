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
    print(colored("🎯 整合測試：功能一 → 四 → 二 + 多層驗證", "cyan"))
    print("--------------------------------------------------")

    success_count = 0
    keyword_pass_case_count = 0
    exclude_pass_case_count = 0
    exclude_name_pass_case_count = 0

    for idx, item in enumerate(INTEGRATION_TEST_INPUTS):
        text = item.get("text", "")
        expected_keywords = item.get("expected_keywords", [])
        expected_excludes = item.get("expected_excludes", [])
        must_exclude_names = item.get("must_exclude_names", [])
        min_results = item.get("min_results", None)
        allow_backfill = item.get("allow_backfill", None)

        print(f"📝 測試 {idx + 1}: {text}")

        payload = {
            "text": text,
            "user_input": text  # 同步傳入 user_input 給功能二
        }
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
                server_excluded = result.get("excluded_items", [])
                if server_excluded:
                    print(colored(f"🧹 伺服器排除詞：{server_excluded}", "blue"))

                restaurants = result.get("data", {}).get("results", [])

                if restaurants:
                    print(colored(f"✅ 成功回傳 {len(restaurants)} 間推薦餐廳", "green"))

                    # ✅ 回傳數量檢查
                    if isinstance(min_results, int) and len(restaurants) < min_results:
                        if payload.get("allow_backfill", False):
                            print(colored(f"   ❌ 餐廳數不足（需至少 {min_results} 間）", "red"))
                        else:
                            print(colored(f"   ℹ️ 純過濾模式少於 {min_results} 間為正常", "yellow"))

                    all_keywords_ok = True
                    all_excludes_ok = True
                    all_exclude_names_ok = True

                    for r in restaurants:
                        name = r.get("name", "❓")
                        reason = r.get("recommend_reason", "")
                        tags = r.get("tags", []) or r.get("matched_tags", [])

                        print(f"   🍽️ {name} → {reason}")

                        # ✅ 關鍵詞驗證
                        missed = [kw for kw in expected_keywords if kw not in reason]
                        if missed:
                            print(colored(f"   ❌ 未命中關鍵詞: {missed}", "yellow"))
                            all_keywords_ok = False
                        elif expected_keywords:
                            print(colored("   ✅ 關鍵詞全部命中", "green"))

                        # ✅ 排除詞驗證
                        if expected_excludes:
                            include_flag = any(
                                ex in name or any(ex in tag for tag in tags)
                                for ex in expected_excludes
                            )
                            if include_flag:
                                print(colored(f"   ❌ 命中排除詞：{expected_excludes}", "red"))
                                all_excludes_ok = False

                        # ✅ 指定排除餐廳名稱驗證
                        if name in must_exclude_names:
                            print(colored(f"   ❌ 餐廳名稱 {name} 應排除但仍出現", "red"))
                            all_exclude_names_ok = False

                    # ✅ 每題統計累加
                    if expected_keywords:
                        if all_keywords_ok:
                            keyword_pass_case_count += 1
                    else:
                        keyword_pass_case_count += 1  # 無期望視為通過

                    if all_excludes_ok:
                        print(colored("   ✅ 排除詞驗證通過", "cyan"))
                        exclude_pass_case_count += 1

                    if all_exclude_names_ok:
                        print(colored("   ✅ 餐廳名稱排除驗證通過", "cyan"))
                        exclude_name_pass_case_count += 1

                    success_count += 1
                else:
                    print(colored("❌ 沒有回傳任何推薦餐廳", "red"))
            else:
                print(colored("❌ 回傳失敗或格式錯誤", "red"))
                print("🔍 回傳內容：", result)

        except Exception as e:
            print(colored(f"🚨 發生例外錯誤：{e}", "red"))

        print("--------------------------------------------------")

    total = len(INTEGRATION_TEST_INPUTS)

    print(colored("\n⚠️ 注意：目前測試集僅含 5 間餐廳，排除後數量可能小於 5 屬正常。", "yellow"))

    print(colored(f"\n📊 測試完成：共 {success_count}/{total} 筆成功回傳", "cyan"))
    print(colored(f"🧠 關鍵詞命中（按題）：{keyword_pass_case_count}/{total}", "cyan"))
    print(colored(f"🧹 排除詞命中（按題）：{exclude_pass_case_count}/{total}", "cyan"))
    print(colored(f"🚫 餐廳名稱排除（按題）：{exclude_name_pass_case_count}/{total}", "cyan"))

if __name__ == "__main__":
    test_integration()
