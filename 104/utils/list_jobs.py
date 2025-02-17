import requests
import json
from urllib.parse import quote_plus

def list_jobs_by_area(area, page=1, jobs_list=None):
    """
    針對單一區域，遞迴取得該區域所有分頁的職缺資料。
    """
    if jobs_list is None:
        jobs_list = []
    
    # 基本 URL 與參數設定
    base_url = "https://www.104.com.tw/jobs/search/api/jobs"
    jobsource = "joblist_search"
    keyword_raw = "python, AI, 數據"
    keyword = quote_plus(keyword_raw)
    mode = "s"
    pagesize = 500

    # 組成 GET 參數（傳入原始字串，讓 requests 自動處理編碼）
    params = {
        "area": area,  # 單一區域
        "jobsource": jobsource,
        "keyword": keyword_raw,
        "mode": mode,
        "page": page,
        "pagesize": pagesize
    }

    # 根據參數組成 Referer URL（其中 keyword 已做 URL 編碼）
    referer = (
        f"https://www.104.com.tw/jobs/search/?jobsource={jobsource}"
        f"&keyword={keyword}&mode={mode}&order=15&page={page}"
        f"&area={area}&pagesize={pagesize}"
    )

    # HTTP request headers
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,de;q=0.5,fr;q=0.4,ko;q=0.3,ja;q=0.2",
        "Connection": "keep-alive",
        "Referer": referer,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/133.0.0.0 Safari/537.36"),
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"'
    }

    print(f"Fetching area {area} page {page}...")
    response = requests.get(base_url, headers=headers, params=params)
    data = response.json()
    
    # 取得本頁資料
    jobs = data.get("data", [])
    jobs_list.extend(jobs)

    # 取得分頁資訊，若還有下一頁，則繼續遞迴
    metadata = data.get("metadata", {})
    pagination = metadata.get("pagination", {})
    current_page = pagination.get("currentPage", page)
    last_page = pagination.get("lastPage", page)

    if current_page < last_page:
        return list_jobs_by_area(area, current_page + 1, jobs_list)
    else:
        return jobs_list

def list_jobs(areas, index=0, all_jobs=None):
    """
    針對多個區域的陣列，用遞迴依序取得每個區域的職缺資料，
    並合併所有結果。
    """
    if all_jobs is None:
        all_jobs = []
    # 終止條件：當 index 超過陣列長度，就回傳結果
    if index >= len(areas):
        return all_jobs

    current_area = areas[index]
    print(f"Processing area: {current_area}")
    area_jobs = list_jobs_by_area(current_area)
    all_jobs.extend(area_jobs)
    return list_jobs(areas, index + 1, all_jobs)

if __name__ == "__main__":
    # 將各區域代碼整理成陣列（可根據需求調整）
    areas = [
        "6001001001", "6001001002", "6001001003", "6001001004", # 中正、大同、中山、松山
        "6001001005", "6001001006", "6001001007", "6001001011", # 大安、萬華、信義、南港
        "6001002003", "6001002014", "6001002015", "6001002016", # 板橋、永和、中和、土城
        "6001002017", "6001002018", "6001002019", "6001002020", # 三峽、鶯歌、樹林、三重
        "6001002021", "6001002022", "6001002024", "6001002025", # 新莊、泰山、蘆洲、五股
        "6001005000", # 桃園
        "6001006000", # 新竹
    ]
    all_jobs = list_jobs(areas)
    # 印出所有職缺資料，設定 ensure_ascii=False 以正確顯示中文，indent=2 提升可讀性
    print(json.dumps(all_jobs, ensure_ascii=False, indent=2))