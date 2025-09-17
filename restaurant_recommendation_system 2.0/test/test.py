# tw_places_reviews.py
# pip install requests python-dotenv tqdm psycopg2-binary
import os, time, csv, hashlib, json
from typing import List, Dict, Any, Set
import requests
from dotenv import load_dotenv
from tqdm import tqdm

WRITE_TO_DB = False  # 若要寫入 Postgres，改成 True（本版預設只輸出 CSV 4 欄）

# ========== 載入 .env ==========
load_dotenv()
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY")
assert API_KEY, "請在 .env 設定 GOOGLE_PLACES_API_KEY 或 GOOGLE_API_KEY"

# 可選：資料庫（Postgres）
DATABASE_URL = os.getenv("DATABASE_URL")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# ========== Google API 端點 ==========
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL     = "https://maps.googleapis.com/maps/api/place/details/json"

# ========== 參數（依配額調整） ==========
REQUESTS_PER_SECOND = 6      # 不要太高，避免 throttle
DETAILS_FIELDS = "name,formatted_address,place_id,rating,user_ratings_total,reviews"
LANGUAGE = "zh-TW"
REGION = "tw"
RETRY_LIMIT = 3

# ========== 路徑設定 ==========
AREAS_PATH = "test/areas.txt"                           # 相對路徑
STATE_PATH = "state/google_reviews_seen.json"      # 跨次去重狀態
OUTPUT_CSV = "output/tw_google_reviews.csv"        # 本次輸出（覆寫）
RUN_PER_PLACE = 5                                  # 每家店本次最多輸出幾筆新評論

os.makedirs("state", exist_ok=True)
os.makedirs("output", exist_ok=True)

# ========== DB（可選）==========
def get_pg_conn():
    import psycopg2
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )

def ensure_table():
    import psycopg2
    sql = """
    CREATE TABLE IF NOT EXISTS reviews (
        id SERIAL PRIMARY KEY,
        source TEXT NOT NULL,
        place_id TEXT,
        place_name TEXT,
        place_address TEXT,
        place_rating REAL,
        user_ratings_total INT,
        author_name TEXT,
        author_rating REAL,
        text TEXT,
        rel_time TEXT,
        language TEXT,
        text_hash CHAR(40),
        raw_json JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE (source, place_id, text_hash)
    );
    """
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

def insert_rows(rows: List[Dict[str, Any]]):
    """若要寫 DB，rows 需包含完整欄位；本版預設只輸出 CSV，不呼叫此函式。"""
    if not rows:
        return
    import psycopg2
    sql = """
    INSERT INTO reviews (
        source, place_id, place_name, place_address, place_rating, user_ratings_total,
        author_name, author_rating, text, rel_time, language, text_hash, raw_json
    ) VALUES (
        %(source)s, %(place_id)s, %(place_name)s, %(place_address)s, %(place_rating)s, %(user_ratings_total)s,
        %(author_name)s, %(author_rating)s, %(text)s, %(rel_time)s, %(language)s, %(text_hash)s, %(raw_json)s
    )
    ON CONFLICT (source, place_id, text_hash) DO NOTHING;
    """
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute(sql, r)
        conn.commit()

# ========== HTTP & API ==========
def throttle():
    time.sleep(1.0 / REQUESTS_PER_SECOND)

def http_get(url, params):
    for attempt in range(RETRY_LIMIT):
        try:
            throttle()
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            status = data.get("status")
            if status in ("OK", "ZERO_RESULTS"):
                return data
            if status in ("OVER_QUERY_LIMIT", "RESOURCE_EXHAUSTED"):
                time.sleep(4 * (attempt + 1))  # 退避
                continue
            return data
        except Exception:
            time.sleep(2 * (attempt + 1))
    return {"status": "ERROR", "results": []}

def text_search_all_pages(query: str):
    params = {"query": query, "region": REGION, "language": LANGUAGE, "key": API_KEY}
    out = []
    token = None
    for _ in range(5):  # 最多翻幾頁
        if token:
            params["pagetoken"] = token
        data = http_get(TEXT_SEARCH_URL, params)
        if data.get("status") == "OK":
            out.extend(data.get("results", []))
            token = data.get("next_page_token")
            if not token:
                break
            time.sleep(2.5)  # 官方建議等待 token 生效
        elif data.get("status") == "ZERO_RESULTS":
            break
        else:
            break
    return out

def get_place_details(place_id: str):
    params = {
        "place_id": place_id,
        "language": LANGUAGE,
        "fields": DETAILS_FIELDS,
        "key": API_KEY,
    }
    data = http_get(DETAILS_URL, params)
    if data.get("status") == "OK":
        return data.get("result", {})
    return {}

# ========== 跨次去重（以評論文字 SHA1） ==========
def sha1_text(s: str) -> str:
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()

def load_state() -> Dict[str, Set[str]]:
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {pid: set(hashes) for pid, hashes in raw.items()}

def save_state(state: Dict[str, Set[str]]):
    serial = {pid: list(hashes) for pid, hashes in state.items()}
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(serial, f, ensure_ascii=False, indent=2)

def pick_new_reviews_for_place(place: Dict[str, Any], seen_set: Set[str], want: int):
    """從 Google 回傳的（最多5筆）裡，挑出未看過的前 N 筆"""
    picked = []
    for rv in (place.get("reviews") or []):
        txt = (rv.get("text") or "").replace("\n", " ").strip()
        if not txt:
            continue
        h = sha1_text(txt)
        if h in seen_set:
            continue
        picked.append({
            "place_id": place.get("place_id"),
            "place_name": place.get("name"),
            "review_rating": rv.get("rating"),
            "review_text": txt
        })
        seen_set.add(h)
        if len(picked) >= want:
            break
    return picked

# ========== 存 CSV（僅 4 欄） ==========
def save_csv(rows: List[Dict[str, Any]], out_path: str):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["place_id", "place_name", "review_rating", "review_text"])
        for r in rows:
            w.writerow([r["place_id"], r["place_name"], r["review_rating"], r["review_text"]])

if __name__ == "__main__":
    # 若 areas.txt 不存在，自動建一個起手式
    if not os.path.exists(AREAS_PATH):
        with open(AREAS_PATH, "w", encoding="utf-8") as f:
            f.write(
                "台北市 大安區 餐廳\n"
                "台北市 信義區 美食\n"
                "新北市 板橋區 餐廳\n"
                "高雄市 三民區 美食\n"
            )
        print(f"已建立範例 {AREAS_PATH}，可自行擴充關鍵字。")

    # 1) 讀關鍵字
    queries = [line.strip() for line in open(AREAS_PATH, "r", encoding="utf-8") if line.strip()]
    print(f"讀到 {len(queries)} 個搜尋關鍵字")

    # 2) Text Search 取得大量 place_id（去重）
    place_ids: Set[str] = set()
    for q in tqdm(queries, desc="TextSearch 聚合 place_id"):
        results = text_search_all_pages(q)
        for res in results:
            pid = res.get("place_id")
            if pid:
                place_ids.add(pid)
    print("累積 place_id 數量：", len(place_ids))

    # 3) 載入狀態（跨次去重）
    state = load_state()

    # 4) 逐店抓詳情 → 每店挑最多 5 筆「新」評論
    rows_out: List[Dict[str, Any]] = []
    for pid in tqdm(list(place_ids), desc="Place Details → 新評論挑選"):
        place = get_place_details(pid)
        if not place:
            continue
        seen = state.get(pid, set())
        picked = pick_new_reviews_for_place(place, seen, RUN_PER_PLACE)
        if picked:
            rows_out.extend(picked)
            state[pid] = seen  # 更新該店 seen 集合

    # 5) 存 CSV（覆寫本次結果）
    save_csv(rows_out, OUTPUT_CSV)
    print(f"本次輸出 {len(rows_out)} 筆到 {OUTPUT_CSV}")

    # 6) 更新狀態（確保下次不重複）
    save_state(state)
    print(f"跨次去重狀態已更新：{STATE_PATH}")

    # 7) （可選）寫 DB（若要，請改成把完整欄位的 rows 傳入 insert_rows）
    if WRITE_TO_DB:
        ensure_table()
        # insert_rows(full_rows)  # 這裡需要 full schema 的 rows，若需要我幫你補齊。
        print("（提示）目前 CSV 版不直接寫 DB，如需入庫請告訴我要的欄位。")
