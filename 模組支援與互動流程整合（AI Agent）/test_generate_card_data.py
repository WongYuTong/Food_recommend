import sys
import os
import requests
from termcolor import colored

# ✅ 設定匯入路徑：將 'agent_module' 資料夾加進來
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_module'))

# ✅ 匯入 sample_data 中的 RESTAURANTS_SAMPLE
from sample_data import RESTAURANTS_SAMPLE

# ✅ 統一使用 API_URL 常數
API_URL = "http://localhost:8000/agent/generate_card_data/"

# ✅ 成功與失敗統計
success_count = 0
fail_count = 0

print(colored("🎯 測試結果", "cyan", attrs=["bold"]))

# ✅ 發送 POST 請求
response = requests.post(API_URL, json={"type": "restaurant_list", "restaurants": RESTAURANTS_SAMPLE})
status_code = response.status_code
print("狀態碼:", status_code)

# ✅ 要比對的欄位清單（已升級）
required_keys = [
    "name", "address", "rating", "tags", "highlight",
    "distance", "distance_m", "recommend_reason", "review_count",
    "price_level", "is_open", "map_url", "features", "style",
    "opening_hours", "has_coupon", "image_url"
]

# ✅ 若成功回傳資料才進行比對
if status_code == 200:
    results = response.json().get("data", {}).get("results", [])

    for i, result in enumerate(results):
        expected = RESTAURANTS_SAMPLE[i]
        name = result.get("name", "未知名稱")
        print(colored(f"\n🔍 測試資料：{name}", attrs=["bold"]))

        match = True  # 這筆資料整體是否通過
        for key in required_keys:
            value = result.get(key, None)
            expected_value = expected.get(key, None)

            # ✅ List 比對：允許包含關鍵值，不要求完全一致
            if isinstance(value, list):
                if key == "features":
                    print(colored(f"  ℹ️ features 為模擬產出，實際值：{value}", "cyan"))
                    continue  # 不比對
                expected_set = set(expected_value) if isinstance(expected_value, list) else set()
                actual_set = set(value)
                if expected_set and not expected_set.issubset(actual_set):
                    match = False
                    print(colored(f"  ❌ {key} 不符", "red"))
                    print(f"     ▶ 預期含有：{expected_set}")
                    print(f"     ▶ 實際：{actual_set}")

            # ✅ map_url 格式比對
            elif key == "map_url":
                if "https://www.google.com/maps/search/" not in value or name not in value:
                    match = False
                    print(colored(f"  ❌ {key} 格式不符", "red"))
                    print(f"     ▶ 回傳：{value}")

            # ✅ recommend_reason 關鍵字比對（不含 $，轉為文字描述）
            elif key == "recommend_reason":
                expected_keywords = set(expected.get("matched_tags", []))
                if expected.get("highlight"):
                    expected_keywords.add(expected["highlight"])
                price_map = {"$": "價格實惠", "$$": "價格中等", "$$$": "偏高價位"}
                price_word = price_map.get(expected.get("price_level", ""), "")
                if price_word:
                    expected_keywords.add(price_word)
                actual_parts = set(value.replace("、", ",").split(","))
                if not expected_keywords.issubset(actual_parts):
                    match = False
                    print(colored(f"  ❌ {key} 不包含所有關鍵字", "red"))
                    print(f"     ▶ 預期含有：{expected_keywords}")
                    print(f"     ▶ 實際：{actual_parts}")

            # ✅ is_open 合理值比對
            elif key == "is_open":
                if value not in ["營業中", "休息中", "無資料"]:
                    match = False
                    print(colored(f"  ❌ {key} 不符合格式", "red"))
                    print(f"     ▶ 實際：{value}")

            # ✅ style 語尾模糊比對（"文青" vs "文青風"）
            elif key == "style":
                if expected_value and expected_value not in value:
                    match = False
                    print(colored(f"  ❌ {key} 不符", "red"))
                    print(f"     ▶ 預期包含：{expected_value}")
                    print(f"     ▶ 實際：{value}")

            # ✅ opening_hours 改為接受固定預設值
            elif key == "opening_hours":
                if value != "11:00 - 21:00":
                    match = False
                    print(colored(f"  ❌ {key} 預設值不符", "red"))
                    print(f"     ▶ 實際：{value}")

            # ✅ 其他欄位直接比對
            else:
                if expected_value is not None and value != expected_value:
                    match = False
                    print(colored(f"  ❌ {key} 不符", "red"))
                    print(f"     ▶ 預期：{expected_value}")
                    print(f"     ▶ 實際：{value}")

        if match:
            success_count += 1
            print(colored(f"✅ {name} 測試通過", "green"))
        else:
            fail_count += 1
            print(colored(f"❌ {name} 測試失敗", "red"))

else:
    print(colored("❌ 無法取得成功回應，請確認伺服器有啟動", "red"))

# ✅ 統整結果
total = success_count + fail_count
print("\n" + colored("📊 測試總結", attrs=["bold"]))
print(colored(f"🎉 成功：{success_count} / {total}", "green"))
print(colored(f"❗ 失敗：{fail_count} / {total}", "red" if fail_count > 0 else "green"))
