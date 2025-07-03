#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os
import requests
import sys
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_store_types(json_path="store_intros.json", api_key="AIzaSyCkt8b_YpZnHF_1BwINjS2ZAr58i2nJ6_o"):
    """
    檢查store_intros.json中所有店家的店家類型欄位，
    如果欄位為空但有place_id，則嘗試從Google Places API獲取類型資料
    """
    if not os.path.exists(json_path):
        logging.error(f"找不到檔案 {json_path}")
        return
    
    try:
        # 讀取現有店家資料
        with open(json_path, 'r', encoding='utf-8') as f:
            stores = json.load(f)
        
        updated_count = 0
        error_count = 0
        
        for i, store in enumerate(stores):
            store_name = store.get("店名", "未知店名")
            place_id = store.get("編號", "")
            
            # 檢查是否有編號(place_id)，且店家類型欄位為空
            if place_id and ("店家類型" not in store or store["店家類型"] == ""):
                logging.info(f"店家 {store_name} (編號: {place_id}) 的店家類型欄位為空，嘗試從API獲取資料")
                
                try:
                    # 從Google Places API獲取店家類型資料
                    detail_url = (
                        f"https://maps.googleapis.com/maps/api/place/details/json?"
                        f"place_id={place_id}&language=zh-TW&fields=types&key={api_key}"
                    )
                    detail_resp = requests.get(detail_url)
                    detail_data = detail_resp.json()
                    
                    # 檢查API響應狀態
                    if detail_data.get('status') != 'OK':
                        logging.warning(f"API 回傳非 OK: {detail_data.get('status')}, {detail_data.get('error_message', '')}")
                        error_count += 1
                        continue
                    
                    # 獲取類型數據
                    detail = detail_data.get('result', {})
                    types = detail.get('types', [])
                    if types is None:
                        types = []
                    
                    types_str = ','.join(types) if types else ""
                    
                    if types_str:
                        # 更新店家類型欄位
                        stores[i]["店家類型"] = types_str
                        logging.info(f"已更新店家 {store_name} 的店家類型: {types_str}")
                        updated_count += 1
                    else:
                        logging.warning(f"店家 {store_name} 無法從API獲取類型資料")
                    
                    # 避免API請求速率過快
                    time.sleep(0.2)
                    
                except Exception as e:
                    logging.error(f"更新店家 {store_name} 的類型資料時出錯: {e}")
                    error_count += 1
        
        # 如果有更新，寫回文件
        if updated_count > 0:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(stores, f, ensure_ascii=False, indent=2)
            logging.info(f"成功更新了 {updated_count} 家店家的類型資料")
        else:
            logging.info("沒有店家需要更新類型資料")
        
        if error_count > 0:
            logging.warning(f"有 {error_count} 家店家更新類型資料時出錯")
        
        return updated_count
    
    except Exception as e:
        logging.error(f"更新店家類型資料時出錯: {e}")
        return 0

def main():
    """主函數，檢查命令行參數並執行更新"""
    # 指定 store_intros.json 文件路徑
    json_path = "store_intros.json"
    
    # 如果命令行有指定API key，則使用命令行的API key
    api_key = "AIzaSyCkt8b_YpZnHF_1BwINjS2ZAr58i2nJ6_o"
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    # 如果命令行有指定文件路徑，則使用命令行的文件路徑
    if len(sys.argv) > 2:
        json_path = sys.argv[2]
    
    logging.info(f"開始更新 {json_path} 中店家的類型資料...")
    
    # 執行更新
    updated_count = update_store_types(json_path, api_key)
    
    logging.info(f"更新完成，共更新了 {updated_count} 家店家的類型資料")

if __name__ == "__main__":
    main() 