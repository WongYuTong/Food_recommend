import requests

url = "http://localhost:8000/agent/generate_prompt/"

# 測試資料：輸入句 → 預期等級與提示內容（部分可模糊比對）
test_cases = [
    {
        "input": "我還沒想好要吃什麼",
        "expected_level": "輕微",
        "expected_prompt_contains": "簡單一點的"
    },
    {
        "input": "都可以啦",
        "expected_level": "中等",
        "expected_prompt_contains": "偏好什麼類型"
    },
    {
        "input": "你決定吧",
        "expected_level": "明確",
        "expected_prompt_contains": "排除不愛吃的"
    },
    {
        "input": "不知道吃什麼",
        "expected_level": "明確",
        "expected_prompt_contains": "排除不愛吃的"
    },
    {
        "input": "我需要想一下",
        "expected_level": "輕微",
        "expected_prompt_contains": "簡單一點的"
    },
    {
        "input": "我今天沒意見",
        "expected_level": "明確",
        "expected_prompt_contains": "排除不愛吃的"
    },
    {
        "input": "我想吃披薩",
        "expected_level": "無",
        "expected_prompt_contains": "有特別想吃的嗎"
    }
]

# 統計變數
passed = 0
failed = 0

# 執行測試
for i, case in enumerate(test_cases, start=1):
    response = requests.post(url, json={"input": case["input"]})
    result = response.json()
    level = result.get("level")
    prompt = result.get("prompt", "")

    print(f"\n🧪 測試 {i}: {case['input']}")
    print(f"✅ 預期 level：{case['expected_level']}")
    print(f"📥 回傳 level：{level}")
    print(f"🔍 回傳 prompt：{prompt}")

    if level == case["expected_level"] and case["expected_prompt_contains"] in prompt:
        print("🎉 測試通過")
        passed += 1
    else:
        print("❌ 測試失敗")
        failed += 1

# 總結
print(f"\n📊 測試結果：{passed}/{len(test_cases)} 通過，{failed} 失敗")
