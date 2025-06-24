import sys
import logging
from utils import initialize_driver
from scraper import open_url, click_update_results_checkbox, fetch_store_links, fetch_intro_info, fetch_places_from_api, open_reviews, sort_reviews_by_latest, scroll_reviews
import time
import json

sys.stdout.reconfigure(encoding='utf-8')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    keywords = "火鍋"  # 你可以根據需求修改
    town_json_path = "town.json"
    api_key = ""    
    store_json = "store_intros.json"

    # 第一步：呼叫 Google Place API 取得店家資訊
    with open(town_json_path, "r", encoding="utf-8") as f:
        towns = json.load(f)

    # 篩選臺北市的前六筆鄉鎮區
    target_towns = [t for t in towns if t["CountyName"] == "臺北市"][:6]

    for town in target_towns:
        lat = town["latitude"]
        lng = town["longitude"]
        output_json = f"store_intros_{town['TownName']}.json"
        # 1. 先抓這一區的店家資訊
        fetch_places_from_api(
            town_json_path=None,
            keywords=keywords,
            api_key=api_key,
            radius=2000,
            output_json=output_json,
            lat=lat,
            lng=lng
        )
        # 2. 針對這一區的店家抓簡介與評論
        with open(output_json, 'r', encoding='utf-8') as f:
            stores = json.load(f)
        driver = initialize_driver()
        try:
            for store in stores:
                if store.get("是否已完成") == "已完成":
                    continue
                url = store.get("店家google map網址")
                store_name = store.get("店名")
                store_id = store.get("編號")
                if not url:
                    logging.warning(f"{store_name} 沒有 Google Map 網址，跳過")
                    continue
                driver.get(url)
                time.sleep(2)
                fetch_intro_info(driver, store_name, url, json_path=store_json)
                logging.info(f"完成抓取店家 {store_name} 的簡介。")
                time.sleep(1)
                # 抓取評論流程
                try:
                    open_reviews(driver)
                    sort_reviews_by_latest(driver)
                    scroll_reviews(driver, store_name, pause_time=3, batch_size=50, store_id=store_id)
                    logging.info(f"完成抓取店家 {store_name} 的評論。")
                except Exception as e:
                    logging.error(f"抓取評論時出錯：{e}")
                time.sleep(1)
        except Exception as e:
            logging.error(f"錯誤：{e}")
        finally:
            driver.quit()

if __name__ == "__main__":
    main() 