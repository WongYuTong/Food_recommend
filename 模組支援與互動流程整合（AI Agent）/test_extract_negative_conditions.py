import requests

url = "http://localhost:8000/agent/extract_negative_conditions/"

# 測試案例：句子 + 預期排除項目
test_cases = [
    ("我不想吃牛肉麵和甜點、義大利麵", {"牛肉麵", "甜點", "義大利麵"}),
    ("不要火鍋和燒烤", {"火鍋", "燒烤"}),
    ("不吃拉麵、壽司以及甜食", {"拉麵", "壽司", "甜食"}),
    ("別推薦牛排、還有漢堡！", {"牛排", "漢堡"}),
    ("不想要飲料或炸雞、鹽酥雞", {"飲料", "炸雞", "鹽酥雞"}),
    ("我今天都可以，看你決定，不過不想吃麻辣鍋", {"麻辣鍋"})
]

# 統計測試結果
total_tests = len(test_cases)
passed_tests = 0
failed_tests = []

# 執行每個測試案例
for i, (sentence, expected) in enumerate(test_cases, start=1):
    response = requests.post(url, json={"text": sentence})
    actual = set(response.json().get("excluded", []))

    passed = actual == expected
    if passed:
        passed_tests += 1
        print(f"\n🧪 測試 {i}: {sentence}")
        print(f"✅ 預期：{expected}")
        print(f"📥 回傳：{actual}")
        print("🎉 測試通過")
    else:
        failed_tests.append((i, sentence, expected, actual))
        print(f"\n🧪 測試 {i}: {sentence}")
        print(f"✅ 預期：{expected}")
        print(f"📥 回傳：{actual}")
        print("❌ 測試失敗")

# 統整結果
print(f"\n📊 測試結果：{passed_tests}/{total_tests} 通過")

if failed_tests:
    print("\n❗ 失敗測試一覽：")
    for i, sentence, expected, actual in failed_tests:
        print(f"- 測試 {i}: {sentence}")
        print(f"  預期：{expected}")
        print(f"  實際：{actual}")