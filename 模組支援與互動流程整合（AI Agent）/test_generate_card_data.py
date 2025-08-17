import requests
from termcolor import cprint

url = "http://localhost:8000/agent/generate_card_data/"

test_restaurants = [
    {"name": "小確幸甜點店", "rating": 4.6, "address": "台北市大安區忠孝東路"},
    {"name": "阿牛燒肉", "rating": 4.2, "address": "新北市板橋區文化路"},
    {"name": "健康素食坊", "rating": 4.8, "address": "台中市西區健行路"},
    {"name": "宵夜拉麵", "rating": 4.4, "address": "台北市信義區松壽路"},
    {"name": "老王牛肉麵", "rating": 3.9, "address": "桃園市中壢區中正路"},
    {"name": "陽光咖啡館", "rating": 4.9, "address": "台北市中山區林森北路"},
    {"name": "快樂漢堡王", "rating": 4.3, "address": "新北市新莊區中平路"}
]

required_fields = [
    "name", "rating", "address", "tags", "highlight", "distance",
    "reason", "review_count", "price_level", "is_open", "map_url",
    "features", "style", "opening_hours", "distance_m"
]

response = requests.post(url, json={"restaurants": test_restaurants})

print("\n📡 正在發送 POST 請求...")
print("📥 狀態碼:", response.status_code)

if response.status_code != 200:
    cprint(f"❌ 發送失敗，內容：{response.text}", "red")
    exit()

results = response.json().get("results", [])
passed, failed = 0, 0
failed_details = []

print("\n🎯 開始比對結果...\n")

for i, res in enumerate(results):
    name = res.get("name", f"測試 {i+1}")
    missing = [f for f in required_fields if f not in res]
    if missing:
        failed += 1
        cprint(f"🧪 測試 {i+1}: {name}", "yellow")
        cprint(f"❌ 失敗 - 缺少欄位: {missing}", "red")
        failed_details.append((name, missing))
    else:
        passed += 1
        cprint(f"🧪 測試 {i+1}: {name}", "cyan")
        cprint("✅ 通過", "green")
    print("-" * 40)

# 📊 總結
print("\n📊 測試總結")
cprint(f"✔️ 通過數量： {passed}", "green")
cprint(f"❌ 失敗數量： {failed}", "red")

if failed_details:
    print("\n📌 詳細失敗原因：")
    for name, missing in failed_details:
        print(f"- {name}")
        print("  缺少欄位:", missing)