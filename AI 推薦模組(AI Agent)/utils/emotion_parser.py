def parse_emotion_from_text(text):
    emotion_keywords = {
        "開心": ["開心", "快樂", "療癒", "幸福"],
        "放鬆": ["放鬆", "悠閒", "舒服"],
        "解壓": ["壓力", "解壓", "需要放鬆"],
        "慶祝": ["慶祝", "聚餐", "節日"],
        "溫暖": ["溫暖", "暖", "熱呼呼"],
    }

    detected_emotions = []

    for emotion, keywords in emotion_keywords.items():
        if any(word in text for word in keywords):
            detected_emotions.append(emotion)

    if detected_emotions:
        return detected_emotions
    else:
        return ["一般"]  # 預設為一般狀態
