import requests
import csv
import time
import os

API_KEY = "AIzaSyBvS3p5kuIRe32iieiUnZ6Wge6u7NiLMQA"
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

# 讀取已完成 place_id
def load_completed_place_ids():
    if os.path.exists("completed_place_ids.txt"):
        with open("completed_place_ids.txt", "r") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_completed_place_ids(place_ids):
    with open("completed_place_ids.txt", "a") as f:
        for pid in place_ids:
            f.write(pid + "\n")

# 查詢行政區餐廳
def get_restaurants_by_district(district):
    all_results = []
    params = {
        'query': f"{district} 餐廳",
        'key': API_KEY,
        'language': 'zh-TW'
    }

    while True:
        res = requests.get(TEXT_SEARCH_URL, params=params)
        data = res.json()
        results = data.get('results', [])
        all_results.extend(results)

        if 'next_page_token' in data:
            time.sleep(2)
            params['pagetoken'] = data['next_page_token']
        else:
            break
    return all_results

# 寫入 CSV（避免重複）
def save_to_csv(district, results, completed_ids):
    new_place_ids = []
    file_exists = os.path.exists("restaurants.csv")
    with open("restaurants.csv", "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['place_id', '名稱', '地址', '評分', '評論數', '經度', '緯度', '行政區'])

        for r in results:
            pid = r.get("place_id")
            if pid not in completed_ids:
                writer.writerow([
                    pid,
                    r.get("name"),
                    r.get("formatted_address"),
                    r.get("rating"),
                    r.get("user_ratings_total"),
                    r["geometry"]["location"]["lng"],
                    r["geometry"]["location"]["lat"],
                    district
                ])
                new_place_ids.append(pid)
                print(f"✅ 新增：{r.get('name')}")
    return new_place_ids

# 主流程
def run():
    completed_ids = load_completed_place_ids()

    with open("districts.txt", "r", encoding="utf-8") as f:
        districts = [line.strip() for line in f.readlines()]

    for district in districts:
        print(f"📍 抓取 {district} 中...")
        results = get_restaurants_by_district(district)
        new_ids = save_to_csv(district, results, completed_ids)
        save_completed_place_ids(new_ids)
        completed_ids.update(new_ids)
        time.sleep(1)  # 避免 API 過快

if __name__ == "__main__":
    run()
