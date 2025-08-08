import requests

url = "http://localhost:8000/agent/suggest_input_guidance/"

# 測試清單：每筆包含輸入句、預期guidance關鍵字清單、預期分類level
test_cases = [
    ("我不吃辣", ["清爽", "湯品", "排除"], "飲食偏好"),
    ("我不吃牛", ["牛", "排除"], "飲食偏好"),
    ("海鮮過敏", ["海鮮", "排除"], "飲食偏好"),
    ("我吃素", ["素食", "蔬食"], "飲食偏好"),
    ("朋友聚餐", ["朋友", "聚會", "多人"], "用餐場合"),
    ("家人吃飯", ["家庭", "多人", "寬敞"], "用餐場合"),
    ("今天是約會", ["約會", "氣氛", "咖啡廳"], "用餐場合"),
    ("有點商務需求", ["正式", "穩重", "高評價"], "用餐場合"),
    ("要幫朋友慶生", ["慶生", "氣氛", "包廂"], "用餐場合"),
    ("要帶小孩一起吃", ["小孩", "兒童", "親子"], "用餐場合"),
    ("要請長輩吃飯", ["長輩", "家庭", "安靜"], "用餐場合"),
    ("想找便宜的餐廳", ["便宜", "平價", "不貴"], "預算"),
    ("來點高級的", ["高級", "高端", "精緻"], "預算"),
    ("想吃宵夜", ["宵夜", "深夜"], "時段"),
    ("早午餐有推薦嗎", ["早午餐"], "時段"),
    ("有推薦的早餐嗎", ["早餐"], "時段"),
    ("想吃甜點", ["甜點"], "料理類型"),
    ("拉麵好嗎", ["拉麵", "日式"], "料理類型"),
    ("最近很想吃韓式", ["韓式"], "料理類型"),
    ("中式餐廳推薦", ["中式"], "料理類型"),
    ("義大利麵好吃嗎", ["義大利麵", "義式"], "料理類型"),
    ("想吃漢堡", ["漢堡", "美式"], "料理類型"),
    ("今天吃不多", ["輕食", "早午餐"], "飲食狀態"),
    ("我趕時間", ["快速", "外帶"], "飲食狀態"),
    ("天氣冷想吃熱的", ["湯品", "火鍋", "熱"], "飲食狀態"),
    ("今天想吃辣的", ["辣", "麻辣", "川菜"], "飲食狀態"),
    ("想吃清淡的", ["清淡", "清爽", "湯品"], "飲食狀態"),
    ("不要火鍋", ["排除"], "排除語句"),
    ("不想吃韓式", ["排除", "韓式"], "排除語句"),
    ("隨便", ["建議", "輸入"], "其他"),  # fallback
]

success_count = 0
fail_count = 0
failed_cases = []

print("\n🎯 開始測試 SuggestInputGuidanceView...\n")

for idx, (text, expected_keywords, expected_level) in enumerate(test_cases, 1):
    try:
        response = requests.post(url, json={"text": text})
        result_json = response.json()
        guidance = result_json.get("guidance", "")
        level = result_json.get("level", "無")

        guidance_ok = any(keyword in guidance for keyword in expected_keywords)
        level_ok = level == expected_level

        print(f"🧪 測試 {idx:2}: {text}")
        print(f"📥 回傳內容: guidance='{guidance}', level='{level}'")

        if guidance_ok and level_ok:
            print("✅ 結果：✔️ 通過\n")
            success_count += 1
        else:
            print(f"❌ 結果：❌ 失敗")
            if not guidance_ok:
                print(f"   ⛔ guidance 未包含期望關鍵詞：{expected_keywords}")
            if not level_ok:
                print(f"   ⛔ level 錯誤，預期：{expected_level}，實際：{level}")
            print()
            fail_count += 1
            failed_cases.append((text, guidance, level, expected_keywords, expected_level))

    except Exception as e:
        print(f"❌ 測試錯誤：{e}\n")
        fail_count += 1

print("📊 測試總結")
print(f"✔️ 通過數量：{success_count}")
print(f"❌ 失敗數量：{fail_count}")

if failed_cases:
    print("\n📌 失敗案例彙整：")
    for text, guidance, level, expected_keywords, expected_level in failed_cases:
        print(f"- 測試輸入：{text}")
        print(f"  guidance 回傳：{guidance}")
        print(f"  level 回傳：{level}")
        print(f"  guidance 應含關鍵詞：{expected_keywords}")
        print(f"  預期分類：{expected_level}\n")