import sys
import os
import requests
from termcolor import colored

# ✅ 匯入 sample data
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_module'))
from sample_data import RESTAURANTS_SAMPLE

# ✅ API URL
API_URL = "http://localhost:8000/agent/generate_recommend_reasons/"

# ✅ 預期關鍵詞（已加入補強後的詞彙）
EXPECTED_KEYWORDS = {
    "小確幸甜點店": {"甜點", "大安區", "甜點評價高", "價格實惠", "高評價", "文青風格"},
    "阿牛燒肉": {"燒肉", "板橋區", "份量大", "適合聚餐", "偏高價位", "美式風格"},
    "拉麵一郎": {"拉麵", "中山區", "人氣拉麵名店", "價格中等", "日式風格", "熱門店家"},
    "夜貓咖啡屋": {"咖啡", "信義區", "氣氛佳", "夜間營業", "夜貓族", "適合宵夜"},
    "泰式小館": {"萬華區", "價格實惠", "異國風味", "東南亞風格", "地點方便"}
}

total = len(RESTAURANTS_SAMPLE)
success = 0
failures = []

print(colored("🎯 測試結果", "cyan", attrs=["bold"]))

for i, restaurant in enumerate(RESTAURANTS_SAMPLE, start=1):
    response = requests.post(API_URL, json={
        "type": "restaurant_list",
        "restaurants": [restaurant]
    })

    if response.status_code != 200:
        print(colored(f"❌ {restaurant['name']} 測試失敗（狀態碼 {response.status_code}）", "red"))
        failures.append(restaurant['name'])
        continue

    result = response.json()
    results = result.get("data", {}).get("results", [])
    if not results:
        print(colored(f"❌ {restaurant['name']} 測試失敗（無回傳資料）", "red"))
        failures.append(restaurant['name'])
        continue

    r = results[0]
    name = r.get("name", "")
    reason = r.get("recommend_reason", "")
    is_open = r.get("is_open", "")

    expected_keywords = EXPECTED_KEYWORDS.get(name, set())

    # ✅ 核心比對
    reason_pass = all(k in reason for k in expected_keywords)
    is_open_pass = isinstance(is_open, str)
    all_pass = reason_pass and is_open_pass

    if all_pass:
        success += 1
        print(colored(f"✅ {name} 測試通過", "green"))
    else:
        print(colored(f"❌ {name} 測試失敗", "red"))
        if not reason_pass:
            missing = [k for k in expected_keywords if k not in reason]
            print(colored(f"  ❌ recommend_reason 缺少：{missing}", "yellow"))
            print(colored(f"     ▶ 實際：{reason}", "blue"))
        if not is_open_pass:
            print(colored(f"  ❌ is_open 格式錯誤 ▶ 實際：{is_open}", "yellow"))
        failures.append(name)

# 📊 統整結果
print(colored("\n📊 測試總結", "cyan", attrs=["bold"]))
print(f"通過：{success}/{total}")
if failures:
    print(colored("❌ 失敗項目：", "red"), ", ".join(failures))
else:
    print(colored("🎉 全部通過！", "green", attrs=["bold"]))
