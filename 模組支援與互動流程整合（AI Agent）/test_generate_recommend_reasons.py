import requests
import json

url = "http://localhost:8000/agent/generate_recommend_reasons/"

test_data = [
    {
        "input": {
            "name": "這一小鍋 台北車站店",
            "rating": 4.8,
            "address": "台北市中正區忠孝西路",
            "is_open": True,
            "ai_reason": "",
            "comment_summary": "",
            "highlight": "甜點評價高",
            "matched_tags": ["火鍋", "高評價"],
            "distance": "400 公尺",
            "reason_score": 0.92,
            "price_level": "$$",
            "review_count": 302
        },
        "expected_keywords": ["甜點評價高", "火鍋", "高評價", "價格中等", "位於中正區"]
    },
    {
        "input": {
            "name": "某某燒肉店",
            "rating": 4.2,
            "address": "台北市信義區松壽路",
            "is_open": False,
            "ai_reason": "",
            "comment_summary": "氣氛佳、座位舒適",
            "highlight": "",
            "matched_tags": ["燒肉"],
            "distance": "800 公尺",
            "reason_score": 0.75,
            "price_level": "$$$",
            "review_count": 189
        },
        "expected_keywords": ["氣氛佳", "燒肉", "偏高價位", "位於信義區"]
    },
    {
        "input": {
            "name": "平價小吃店",
            "rating": 3.8,
            "address": "新北市板橋區文化路",
            "is_open": True,
            "ai_reason": "",
            "comment_summary": "",
            "highlight": "",
            "matched_tags": [],
            "distance": "600 公尺",
            "reason_score": None,
            "price_level": "$",
            "review_count": 88
        },
        "expected_keywords": ["整體評價不錯", "價格實惠", "位於板橋區"]
    }
]

expected_keys = [
    "name", "recommend_reason", "highlight", "tags",
    "price_level", "review_count", "is_open",
    "map_url", "distance", "reason_score", "reason_summary"
]

# 發送 POST 請求
response = requests.post(url, json={"restaurants": [t["input"] for t in test_data]})
print("📥 狀態碼:", response.status_code)

if response.status_code != 200:
    print("❌ API 請求失敗")
    exit()

results = response.json().get("results", [])
success_count = 0
failures = []

print("\n🎯 開始比對結果...\n")

for i, (res, test) in enumerate(zip(results, test_data), 1):
    name = res.get("name", f"第{i}筆資料")
    print(f"🧪 測試 {i}: {name}")

    missing_keys = [k for k in expected_keys if k not in res]
    missing_keywords = [kw for kw in test["expected_keywords"] if kw not in res.get("recommend_reason", "")]

    if not missing_keys and not missing_keywords:
        print("✅ 通過")
        success_count += 1
    else:
        print("❌ 失敗")
        if missing_keys:
            print("  ⛔ 缺少欄位:", missing_keys)
        if missing_keywords:
            print("  ⛔ 推薦理由缺少關鍵字:", missing_keywords)
        failures.append({"name": name, "missing_keys": missing_keys, "missing_keywords": missing_keywords})

    print("-" * 40)

# 測試總結
print("\n📊 測試總結")
print(f"✔️ 通過數量：{success_count}")
print(f"❌ 失敗數量：{len(results) - success_count}")

if failures:
    print("\n📌 詳細失敗原因：")
    for fail in failures:
        print(f"- {fail['name']}")
        if fail["missing_keys"]:
            print("  缺少欄位:", fail["missing_keys"])
        if fail["missing_keywords"]:
            print("  推薦理由缺少關鍵詞:", fail["missing_keywords"])
