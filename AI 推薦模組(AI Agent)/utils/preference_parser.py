# utils/preference_parser.py

import re

def parse_preference_from_text(text):
    like_patterns = ["喜歡", "愛吃", "想吃", "偏好", "要吃"]
    dislike_patterns = ["不喜歡", "不吃", "討厭"]

    preferences = {
        "喜歡": [],
        "不喜歡": []
    }

    def clean_item(item):
        # 去除常見前綴動詞
        for prefix in ["吃", "要吃", "想吃"]:
            if item.startswith(prefix):
                item = item[len(prefix):]
        return item.strip()

    # 處理喜歡類
    for pattern in like_patterns:
        matches = re.findall(f"{pattern}[^，。；!?、]*", text)
        for match in matches:
            items_str = match.replace(pattern, "")
            items = re.split("[、和與,，及 ]", items_str)
            items = [clean_item(item) for item in items if item.strip()]
            preferences["喜歡"].extend(items)

    # 處理不喜歡類
    for pattern in dislike_patterns:
        matches = re.findall(f"{pattern}[^，。；!?、]*", text)
        for match in matches:
            items_str = match.replace(pattern, "")
            items = re.split("[、和與,，及 ]", items_str)
            items = [clean_item(item) for item in items if item.strip()]
            preferences["不喜歡"].extend(items)

    # 清除重複
    preferences["喜歡"] = list(set(preferences["喜歡"]))
    preferences["不喜歡"] = list(set(preferences["不喜歡"]))

    # 移除喜歡與不喜歡衝突的項目（只保留於「不喜歡」）
    preferences["喜歡"] = [item for item in preferences["喜歡"] if item not in preferences["不喜歡"]]

    # 若兩者皆為空，回傳無特別偏好
    if not preferences["喜歡"] and not preferences["不喜歡"]:
        return ["無特別偏好"]

    return preferences