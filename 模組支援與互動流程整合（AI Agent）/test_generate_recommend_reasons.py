import sys
import os
import requests
from termcolor import colored

# ✅ 匯入 sample data
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_module'))
from sample_data import RESTAURANTS_SAMPLE

# ✅ API URL（功能二的端點）
API_URL = "http://localhost:8000/agent/generate_recommend_reasons/"

# ✅ 關鍵詞：改成貼近實際輸出用語
EXPECTED_KEYWORDS = {
    "小確幸甜點店": {"甜點評價高", "價格實惠", "文青風格", "位於大安區"},
    "阿牛燒肉": {"燒肉", "位於板橋區", "份量大", "適合聚餐", "偏高價位", "美式風格"},
    "拉麵一郎": {"拉麵", "位於中山區", "人氣拉麵名店", "價格中等", "日式風格", "熱門店家"},
    "夜貓咖啡屋": {"氣氛佳", "位於信義區", "夜間營業", "適合夜貓子"},  # 「適合宵夜」有時也會出現
    "泰式小館": {"位於萬華區", "價格實惠", "異國風味", "東南亞風格", "地點方便"},
}

# ✅ 是否在請求時送入 user_input 來觸發補強（想測「不補強」就改 False）
SEND_USER_INPUT = True

total = len(RESTAURANTS_SAMPLE)
success = 0
failures = []

print(colored("🎯 功能二：推薦理由補強 測試開始", "cyan", attrs=["bold"]))
print("--------------------------------------------------")

for i, restaurant in enumerate(RESTAURANTS_SAMPLE, start=1):
    name = restaurant["name"]
    # 可選：給每家餐廳一段 user_input，觸發補強（沒有就送空字串）
    user_input = ""
    if SEND_USER_INPUT:
        # 針對不同店家給一點合理的偏好，讓補強更容易命中
        if "甜點" in name:
            user_input = "想要吃甜點，價格實惠一點，文青風、地點方便"
        elif "燒肉" in name:
            user_input = "朋友聚餐，份量要大，預算較高也可以"
        elif "拉麵" in name:
            user_input = "想吃日式拉麵，人氣名店，價格中等"
        elif "咖啡" in name:
            user_input = "氣氛要好，晚上想去坐坐，宵夜時段也要有"
        elif "泰式" in name:
            user_input = "想吃異國風味，東南亞風，價格實惠、地點方便"

    payload = {
        "type": "restaurant_list",
        "restaurants": [restaurant],
        "user_input": user_input
    }

    response = requests.post(API_URL, json=payload)

    print(f"📝 測試 {i}: {name}")
    print("🔁 回傳狀態碼:", response.status_code)

    if response.status_code != 200:
        print(colored(f"❌ API 錯誤（status={response.status_code}）", "red"))
        failures.append(name)
        print("--------------------------------------------------")
        continue

    try:
        result = response.json()
    except Exception as e:
        print(colored(f"❌ 回傳 JSON 無法解析：{e}", "red"))
        failures.append(name)
        print("--------------------------------------------------")
        continue

    results = result.get("data", {}).get("results", [])
    if not results:
        print(colored("❌ 無回傳資料", "red"))
        failures.append(name)
        print("--------------------------------------------------")
        continue

    r = results[0]
    recommend_reason = r.get("recommend_reason", "") or ""
    reason_summary = r.get("reason_summary", {}) or {}
    tags = r.get("tags", []) or r.get("matched_tags", []) or []
    is_open = r.get("is_open", "")

    # ✅ 驗證來源：把 name + recommend_reason + tags + reason_summary.core/extra 串起來
    fields_for_match = [name, recommend_reason]
    fields_for_match.extend(tags)
    fields_for_match.append(reason_summary.get("core", ""))
    fields_for_match.extend(reason_summary.get("extra", []))
    haystack = "、".join([str(x) for x in fields_for_match if x])

    expected_keywords = EXPECTED_KEYWORDS.get(name, set())
    missing = [k for k in expected_keywords if k not in haystack]

    # ✅ 結構驗證
    reason_valid = isinstance(reason_summary, dict) and "core" in reason_summary and "extra" in reason_summary
    is_open_valid = isinstance(is_open, str)

    if not expected_keywords:
        # 沒有定義期望的，就只驗結構
        if reason_valid and is_open_valid:
            print(colored("✅ 測試通過（僅結構）", "green"))
            success += 1
        else:
            print(colored("❌ 測試未通過（結構）", "red"))
            if not reason_valid:
                print(colored("  ❌ reason_summary 結構異常", "yellow"))
                print(f"     ▶ 實際：{reason_summary}")
            if not is_open_valid:
                print(colored(f"  ❌ is_open 格式錯誤 ▶ 實際：{is_open}", "yellow"))
            failures.append(name)
    else:
        if not missing and reason_valid and is_open_valid:
            print(colored("✅ 測試通過", "green"))
            success += 1
        else:
            print(colored("❌ 測試未通過", "red"))
            if missing:
                print(colored(f"  ❌ 缺少關鍵詞：{missing}", "yellow"))
                print(f"     ▶ 來源 haystack：{haystack}")
            if not reason_valid:
                print(colored("  ❌ reason_summary 結構異常", "yellow"))
                print(f"     ▶ 實際：{reason_summary}")
            if not is_open_valid:
                print(colored(f"  ❌ is_open 格式錯誤 ▶ 實際：{is_open}", "yellow"))
            failures.append(name)

    print("--------------------------------------------------")

# 📊 統整結果
print(colored("\n📊 測試總結", "cyan", attrs=["bold"]))
print(f"通過：{success}/{total}")
if failures:
    print(colored("❌ 失敗項目：", "red"), ", ".join(failures))
else:
    print(colored("🎉 全部通過！", "green", attrs=["bold"]))
