import logging
import time
import random
import csv
import os
import requests
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import re
from utils import sanitize_filename, get_next_id, format_intro_content

def open_url(driver, url):
    """打開指定的 URL"""
    try:
        driver.get(url)
    except TimeoutException:
        logging.error("打開URL時超時，請檢查網絡連接或URL是否正確。")

def scroll_reviews(driver, store_name, pause_time=3, max_no_change_attempts=5, batch_size=50, max_scrolls=10000, store_id=None):
    """
    持續滾動評論區直到沒有新評論，並以 all_reviews.json 為依據計算數量
    """
    try:
        if store_id is None:
            logging.warning("未提供店家編號，無法追蹤評論數量")
            return

        review_count = 0
        review_with_text_count = 0
        all_reviews_file = "all_reviews.json"
        if os.path.exists(all_reviews_file):
            with open(all_reviews_file, 'r', encoding='utf-8') as f:
                all_reviews = json.load(f)
            for row in all_reviews:
                if row and row[0] == str(store_id):
                    review_count += 1
                    if row[4] and row[4] != "無評論":
                        review_with_text_count += 1

        if review_with_text_count >= 60:
            logging.info(f"店家 {store_name}（編號：{store_id}）已達到60則有效評論上限，跳過抓取")
            update_completion_status(store_id, "已完成", f"已達到60則有效評論上限")
            return
        if review_count >= 160:
            logging.info(f"店家 {store_name}（編號：{store_id}）已達到160則評論上限，跳過抓取")
            update_completion_status(store_id, "已完成", f"已達到160則評論上限")
            return

        scrollable_div = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde'))
        )
        last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        scroll_count = 0
        no_change_attempts = 0
        processed_reviews = set()
        while no_change_attempts < max_no_change_attempts and scroll_count < max_scrolls:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            scroll_count += 1
            time.sleep(random.uniform(0.2, 0.3))
            reviews = driver.find_elements(By.CLASS_NAME, 'jftiEf')
            logging.info(f"第 {scroll_count} 次滾動，已加載 {len(reviews)} 條評論。")
            new_reviews = [review for review in reviews if review not in processed_reviews]
            if new_reviews:
                remaining_reviews = min(60 - review_with_text_count, 160 - review_count)
                if remaining_reviews <= 0:
                    logging.info(f"店家 {store_name}（編號：{store_id}）已達到評論上限")
                    if review_with_text_count >= 60:
                        update_completion_status(store_id, "已完成", f"已達到60則有效評論上限")
                    else:
                        update_completion_status(store_id, "已完成", f"已達到160則評論上限")
                    break
                reviews_to_process = min(len(new_reviews[:batch_size]), max(50, remaining_reviews * 2))
                new_text_reviews = fetch_reviews(driver, store_name, new_reviews[:reviews_to_process], store_id)
                processed_reviews.update(new_reviews[:reviews_to_process])
                review_with_text_count += new_text_reviews
                if review_with_text_count >= 60:
                    logging.info(f"店家 {store_name}（編號：{store_id}）已達到60則有效評論上限")
                    update_completion_status(store_id, "已完成", f"已達到60則有效評論上限")
                    break
            if new_height == last_height:
                no_change_attempts += 1
                logging.info(f"沒有更多新評論，連續未增加評論次數：{no_change_attempts}")
                time.sleep(pause_time)
            else:
                no_change_attempts = 0
                last_height = new_height
            if no_change_attempts >= max_no_change_attempts:
                logging.info("連續多次未增加評論，停止滾動。")
                update_completion_status(store_id, "已完成", "已抓取所有可用評論")
                break
    except Exception as e:
        logging.error(f"滾動評論區時出錯：{e}")
        logging.error("詳細錯誤信息：", exc_info=True)

def sort_reviews_by_latest(driver):
    """點擊排序按鈕並選擇最新排序"""
    try:
        sort_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="排序評論"]'))
        )
        sort_button.click()
        time.sleep(0.5)
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.fxNQSd[data-index="1"]'))
        ).click()
        time.sleep(1)
        logging.info("已選擇最新排序。")
    except Exception as e:
        logging.error(f"選擇最新排序時錯：{e}")

def fetch_store_links(driver, keyword, latitude, longitude, zoom_level, max_scrolls=10, pause_time=3):
    """使用關鍵字滾動獲取所有店家的鏈接，並儲存店家資訊"""
    store_links = set()  # 使用集合避免重複
    try:
        driver.get(f'https://www.google.com/maps/search/{keyword}/@{latitude},{longitude},{zoom_level}z')
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))).click()
        except Exception:
            pass

        scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
        driver.execute_script("""
            var scrollableDiv = arguments[0];
            function scrollWithinElement(scrollableDiv) {
                return new Promise((resolve, reject) => {
                    var totalHeight = 0;
                    var distance = 1000;
                    var scrollDelay = 10000;
                    
                    var timer = setInterval(() => {
                        var scrollHeightBefore = scrollableDiv.scrollHeight;
                        var elementsBefore = scrollableDiv.querySelectorAll('div[jsaction]').length;
                        scrollableDiv.scrollBy(0, distance);
                        totalHeight += distance;

                        if (totalHeight >= scrollHeightBefore) {
                            totalHeight = 0;
                            setTimeout(() => {
                                var scrollHeightAfter = scrollableDiv.scrollHeight;
                                var elementsAfter = scrollableDiv.querySelectorAll('div[jsaction]').length;
                                if (scrollHeightAfter > scrollHeightBefore || elementsAfter > elementsBefore) {
                                    return;
                                } else {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, scrollDelay);
                        }
                    }, 200);
                });
            }
            return scrollWithinElement(scrollableDiv);
        """, scrollable_div)

        items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')
        logging.info(f"找到 {len(items)} 個店家。")

        for item in items:
            try:
                # 等待元素可點擊，最多等待2秒
                WebDriverWait(item, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))
                )
                # 嘗試更精確的選擇器
                link_element = item.find_element(By.CSS_SELECTOR, 'a[href*="maps/place"]')
                if not link_element:
                    link_element = item.find_element(By.CSS_SELECTOR, 'a')
                
                link = link_element.get_attribute('href')
                if link:
                    store_links.add(link)
                    logging.info(f"成功獲取店家連結: {link[:60]}...")
                else:
                    logging.warning("找到連結元素但無法獲取href屬性")
                
                # # 獲取店名與評價
                # store_name = item.find_element(By.CSS_SELECTOR, 'div.qBF1Pd').text
                # try:
                #     rating = item.find_element(By.CSS_SELECTOR, 'span.MW4etd').text
                # except NoSuchElementException:
                #     rating = "無星數"
                    
                # save_store_info(store_name, rating, latitude, longitude,keyword)  # 存入 CSV
            except TimeoutException:
                logging.warning(f"等待連結元素超時，可能不是有效店家項目")
            except NoSuchElementException as e:
                logging.warning(f"找不到連結元素: {str(e).split('Stacktrace')[0]}")
            except Exception as e:
                logging.error(f"獲取店家鏈接時出錯：{str(e).split('Stacktrace')[0]}")

    except Exception as e:
        logging.error(f"獲取店家鏈接時出錯：{e}")
    return list(store_links)

def open_reviews(driver):
    """點擊評論按鈕"""
    try:
        reviews_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "評論")]'))
        )
        reviews_button.click()
        time.sleep(1)
    except Exception as e:
        logging.error(f"點擊評論按鈕時出錯：{e}")

def fetch_reviews(driver, store_name, reviews, store_id=None):
    """
    抓取評論並保存到 all_reviews.json
    """
    try:
        all_reviews_file = "all_reviews.json"
        current_date = time.strftime("%Y-%m-%d")
        new_text_reviews_count = 0  # 追蹤新增的有效評論數量

        # 讀取已存在的評論
        if os.path.exists(all_reviews_file):
            with open(all_reviews_file, 'r', encoding='utf-8') as f:
                all_reviews = json.load(f)
        else:
            all_reviews = []

        existing_reviews = set()
        for row in all_reviews:
            if len(row) >= 4:
                existing_reviews.add((row[0], row[1], row[3]))  # (店家編號, 用戶, 日期)

        logging.info(f"共找到 {len(reviews)} 條評論：\n")

        for review in reviews:
            try:
                # 先檢查評論是否有全文按鈕
                try:
                    try:
                        review_content = review.find_element(By.CLASS_NAME, 'MyEned')
                    except NoSuchElementException:
                        review_content = review.find_element(By.CLASS_NAME, 'jJc9Ad')
                    full_text_button = review_content.find_element(By.CSS_SELECTOR, 'button.w8nwRe.kyuRq[aria-label="顯示更多"]')
                    if full_text_button and full_text_button.is_displayed():
                        logging.info("找到全文按鈕，點擊展開...")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", full_text_button)
                        full_text_button.click()
                        time.sleep(0.1)
                        retry_count = 0
                        max_retries = 5
                        while retry_count < max_retries:
                            time.sleep(0.1)
                            try:
                                retry_button = review_content.find_element(By.CSS_SELECTOR, 'button.w8nwRe.kyuRq[aria-label="顯示更多"]')
                                if retry_button.is_displayed():
                                    logging.info(f"檢測到全文按鈕仍然存在，第 {retry_count + 1} 次嘗試點擊...")
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", retry_button)
                                    time.sleep(0.1)
                                    retry_button.click()
                                    time.sleep(0.1)
                                    retry_count += 1
                                else:
                                    break
                            except NoSuchElementException:
                                break
                        if retry_count >= max_retries:
                            logging.info("已達到最大重試次數，停止嘗試點擊全文按鈕")
                except NoSuchElementException:
                    logging.info("未找到全文按鈕或評論內容區域")
                except Exception as e:
                    logging.info(f"處理全文按鈕時出錯: {str(e).split('Stacktrace')[0]}")

                user_name = review.find_element(By.CLASS_NAME, 'd4r55').text
                rating_text = review.find_element(By.CLASS_NAME, 'kvMYJc').get_attribute("aria-label")
                rating = ''.join(filter(str.isdigit, rating_text))
                review_date = review.find_element(By.CLASS_NAME, 'rsqaWe').text

                user_profile_url = "無評論記錄網址"
                try:
                    user_profile_button = review.find_element(By.CSS_SELECTOR, 'button.al6Kxe')
                    if user_profile_button:
                        user_profile_url = user_profile_button.get_attribute('data-href')
                        logging.info(f"找到用戶評論記錄網址：{user_profile_url}")
                except NoSuchElementException:
                    logging.info("未找到用戶評論記錄網址")
                except Exception as e:
                    logging.error(f"獲取用戶評論記錄網址時出錯：{e}")

                is_duplicate = (str(store_id), user_name, review_date) in existing_reviews

                if not is_duplicate:
                    try:
                        review_text = "無評論"
                        structured_review_text = "無類別及評分"
                        try:
                            review_text_element = review.find_element(By.CSS_SELECTOR, 'span.wiI7pd')
                            if review_text_element:
                                review_text = review_text_element.text.replace('\n', ' ').strip()
                                logging.info(f"{user_name} 評論文字：{review_text}")
                        except NoSuchElementException:
                            logging.info("未找到文字評論")
                            review_text = "無評論"
                        try:
                            structured_review = review.find_element(By.CSS_SELECTOR, 'div[jslog="127691"]')
                            if structured_review:
                                structured_review_text = structured_review.text.replace('\n', ' ').strip()
                                logging.info(f"{user_name} 類別及評分：{structured_review_text}")
                        except NoSuchElementException:
                            logging.info("未找到類別及評分")
                            structured_review_text = "無類別及評分"
                    except Exception as e:
                        logging.error(f"處理評論文本時出錯：{e}")
                        review_text = "無評論"
                        structured_review_text = "無類別及評分"

                    # 寫入 all_reviews.json
                    all_reviews.append([
                        store_id, user_name, rating, review_date, review_text, structured_review_text, current_date, user_profile_url
                    ])
                    existing_reviews.add((str(store_id), user_name, review_date))
                    if review_text != "無評論":
                        new_text_reviews_count += 1
                    logging.info(f"抓取評論: 用戶: {user_name}, 評分: {rating}, 日期: {review_date}, 評論: {review_text}")
                    logging.info('-' * 30)
                else:
                    logging.info(f"評論已存在（店家編號 {store_id}、用戶 {user_name}、日期 {review_date} 都相同），跳過")
            except Exception as e:
                logging.error(f"無法解析評論的部分內容：{e}")

        # 回寫 all_reviews.json
        with open(all_reviews_file, 'w', encoding='utf-8') as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=2)
        logging.info(f"本次新增 {len(reviews)} 條評論，其中有含文字的評論 {new_text_reviews_count} 條。")
        return new_text_reviews_count  # 返回新增的有效評論數量
    except Exception as e:
        logging.error(f"抓取評論時出錯：{e}")

def fetch_intro_info(driver, store_name, google_map_url, json_path="store_intros.json"):
    """
    只抓取店家簡介內容，並寫入 store_intros.json 的對應店家（以 google_map_url 為 key）之 "簡介" 欄位。
    """
    try:
        # 先點擊簡介按鈕
        try:
            intro_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "簡介")]'))
            )
            intro_button.click()
            time.sleep(1)
        except (NoSuchElementException, TimeoutException):
            logging.info(f"{store_name} 找不到簡介按鈕，跳過...")
            return

        # 滾動簡介區塊
        try:
            scrollable_div = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde'))
            )
            scroll_intro_section(driver, scrollable_div)
        except TimeoutException:
            logging.info(f"{store_name} 沒有找到簡介內容")

        # 抓取簡介內容
        intro_text = []
        try:
            intro_blocks = driver.find_elements(By.CLASS_NAME, 'iP2t7d')
            for block in intro_blocks:
                try:
                    content = block.text.strip()
                    if content:
                        intro_text.append(content)
                except Exception as e:
                    logging.error(f"處理簡介塊時出錯：{e}")
        except Exception as e:
            logging.error(f"抓取簡介內容時出錯：{e}")
        formatted_intro = format_intro_content(intro_text) if intro_text else "無詳細簡介"

        # 更新 json
        with open(json_path, 'r', encoding='utf-8') as f:
            stores = json.load(f)
        updated = False
        for store in stores:
            if store.get("店家google map網址") == google_map_url:
                store["簡介"] = formatted_intro
                store["是否已完成"] = "已完成"
                updated = True
                break
        if updated:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(stores, f, ensure_ascii=False, indent=2)
            logging.info(f"已更新 {store_name} 的簡介內容。")
        else:
            logging.warning(f"找不到對應店家（網址: {google_map_url}），無法寫入簡介。")
        time.sleep(1)
    except Exception as e:
        logging.error(f"抓取 {store_name} 簡介時出錯：{e}", exc_info=True)

def scroll_intro_section(driver, scrollable_div, max_scrolls=10, max_no_change_attempts=1, pause_time=1):
    """滾動簡介區塊"""
    try:
        last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        scroll_count = 0
        no_change_attempts = 0

        while no_change_attempts < max_no_change_attempts and scroll_count < max_scrolls:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(random.uniform(0.4, 0.6))
            
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            scroll_count += 1

            logging.info(f"第 {scroll_count} 次滾動，當前高度 {new_height}")

            if new_height == last_height:
                no_change_attempts += 1
                logging.info(f"未加載新內容，連續未變化次數：{no_change_attempts}")
                time.sleep(pause_time)
            else:
                no_change_attempts = 0
                last_height = new_height

            if no_change_attempts >= max_no_change_attempts:
                logging.info("簡介內容已完全加載，停止滾動。")
                break

    except Exception as e:
        logging.error(f"滾動簡介區塊時出錯：{e}", exc_info=True)

def click_update_results_checkbox(driver):
    """點擊 '地圖移動時更新結果' 復選框"""
    try:
        checkbox_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@role="checkbox"]'))
        )
        
        driver.execute_script("arguments[0].scrollIntoView(true);", checkbox_button)
        checkbox_button.click()
        logging.info("已點擊 '地圖移動時更新結果' 復選框。")
    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"點擊 '地圖移動時更新結果' 復選框時出錯：{e}") 

def update_completion_status(store_id, status, reason=""):
    """
    更新店家的完成狀態，直接操作 store_intros.json
    """
    csv_file = "store_intros.json"
    if not os.path.exists(csv_file):
        logging.error(f"找不到檔案 {csv_file}，無法更新完成狀態")
        return
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            stores = json.load(f)
        updated = False
        for store in stores:
            if store.get("編號") == str(store_id):
                store["是否已完成"] = status
                updated = True
                logging.info(f"更新店家（編號：{store_id}）狀態為 {status}：{reason}")
                break
        if updated:
            with open(csv_file, 'w', encoding='utf-8') as f:
                json.dump(stores, f, ensure_ascii=False, indent=2)
        else:
            logging.warning(f"找不到對應店家（編號: {store_id}），無法更新狀態。")
    except Exception as e:
        logging.error(f"更新完成狀態時出錯：{e}", exc_info=True) 

def fetch_places_from_api(town_json_path=None, keywords="", api_key="", radius=2000, output_json="store_intros.json", lat=None, lng=None):
    """
    根據 town.json 內容或直接給定經緯度與 keywords，呼叫 Google Place API 取得店家資訊，並存入 store_intros.json。
    """
    import json
    import requests
    import logging

    all_places = []
    place_ids = set()

    # 如果有 lat/lng，直接查詢
    if lat is not None and lng is not None:
        locations = [(lat, lng)]
    else:
        # 否則讀取 town_json_path
        if not town_json_path or not os.path.exists(town_json_path):
            logging.error(f"找不到 {town_json_path}")
            return
        with open(town_json_path, 'r', encoding='utf-8') as f:
            towns = json.load(f)
            if isinstance(towns, dict):
                towns = [towns]
            locations = [(t['latitude'], t['longitude']) for t in towns]

    for lat, lng in locations:
        location = f"{lat},{lng}"
        url = (
            f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
            f"location={location}&radius={radius}&keyword={keywords}&language=zh-TW&key={api_key}"
        )
        try:
            resp = requests.get(url)
            data = resp.json()
            if data.get('status') != 'OK':
                logging.warning(f"API 回傳非 OK: {data.get('status')}, {data.get('error_message', '')}")
                continue
            for result in data.get('results', []):
                place_id = result.get('place_id')
                if place_id in place_ids:
                    continue
                place_ids.add(place_id)
                # 取得詳細資料
                detail_url = (
                    f"https://maps.googleapis.com/maps/api/place/details/json?"
                    f"place_id={place_id}&language=zh-TW&fields="
                    f"place_id,name,formatted_address,geometry,opening_hours,website,types,business_status,rating,price_level,photos,url&key={api_key}"
                )
                detail_resp = requests.get(detail_url)
                detail = detail_resp.json().get('result', {})
                # 組合欄位
                place_info = {
                    "編號": detail.get('place_id', ''),
                    "店名": detail.get('name', ''),
                    "地址": detail.get('formatted_address', ''),
                    "經緯度": f"{detail.get('geometry', {}).get('location', {}).get('lat', '')},{detail.get('geometry', {}).get('location', {}).get('lng', '')}",
                    "營業時間": '\n'.join(detail.get('opening_hours', {}).get('weekday_text', [])) if detail.get('opening_hours') else '',
                    "官方網站": detail.get('website', ''),
                    "店家簡述": ','.join(detail.get('types', [])),
                    "星數": detail.get('rating', ''),
                    "價位": detail.get('price_level', ''),
                    "營業狀態": detail.get('business_status', ''),
                    "店家圖片": f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={detail.get('photos', [{}])[0].get('photo_reference', '')}&key={api_key}" if detail.get('photos') else '',
                    "店家google map網址": detail.get('url', ''),
                    "搜尋關鍵字": keywords,
                    "簡介": "無",
                    "是否已完成": "未完成"
                }
                all_places.append(place_info)
        except Exception as e:
            logging.error(f"呼叫 Google Place API 發生錯誤: {e}")
    # 寫入 json
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_places, f, ensure_ascii=False, indent=2)
    logging.info(f"已將 {len(all_places)} 筆店家資訊寫入 {output_json}")