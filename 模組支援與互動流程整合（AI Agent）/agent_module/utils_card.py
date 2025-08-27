import re

# ✅ 產生 Google Map 搜尋連結
def generate_map_url(name: str) -> str:
    return f"https://www.google.com/maps/search/{name}"

# ✅ 格式化營業狀態
def format_open_status(is_open_raw) -> str:
    if isinstance(is_open_raw, bool):
        return "營業中" if is_open_raw else "休息中"
    elif isinstance(is_open_raw, str):
        return is_open_raw
    else:
        return "無資料"

# ✅ 從地址中擷取行政區（如「大安區」、「板橋區」）
def extract_district(address: str) -> str:
    match = re.search(r'(台北市|新北市)?(\w{2,3}區)', address)
    return match.group(2) if match else ""

# ✅ 根據價格層級轉為描述
def generate_price_description(price_level: str) -> str:
    mapping = {
        "$": "價格實惠",
        "$$": "價格中等",
        "$$$": "偏高價位"
    }
    return mapping.get(price_level, "")

# ✅ 整合標籤、亮點、地區、價格，產生推薦理由（功能四用）
def generate_recommend_reason(tags: list, highlight: str, district: str, price_desc: str) -> str:
    keywords = set(tags)
    if highlight:
        keywords.add(highlight)
    if district:
        keywords.add(district)
    if price_desc:
        keywords.add(price_desc)
    return "、".join(keywords)

