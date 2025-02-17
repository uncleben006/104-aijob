import requests
import json
from urllib.parse import quote_plus

def list_jobs(page=1, jobs_list=None):
    if jobs_list is None:
        jobs_list = []
    
    # 基本 URL 與參數設定
    base_url = "https://www.104.com.tw/jobs/search/api/jobs"
    area = "6001001001,6001001002,6001001004,6001001003,6001001005,6001001006,6001001007,6001001011,6001002000,6001005000"
    jobsource = "joblist_search"
    # 注意：參數中若有中文，傳入 GET 請求時 requests 會自動處理編碼，
    # 但在生成 Referer 時需要先對 keyword 進行 URL 編碼
    keyword_raw = "python, AI, 數據"
    keyword = quote_plus(keyword_raw)
    mode = "s"
    pagesize = 500

    # 組成 GET 參數（requests 會自動編碼）
    params = {
        "area": area,
        "jobsource": jobsource,
        "keyword": keyword_raw,  # 傳入原始字串，讓 requests 自動處理編碼
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

    print(f"Fetching page {page}...")
    response = requests.get(base_url, headers=headers, params=params)
    data = response.json()
    print(data)

    # 將本頁的資料加入 jobs_list
    jobs = data.get("data", [])
    jobs_list.extend(jobs)

    # 取得分頁資訊：若當前頁小於最後一頁，則遞迴呼叫取得下一頁資料
    metadata = data.get("metadata", {})
    pagination = metadata.get("pagination", {})
    current_page = pagination.get("currentPage", page)
    last_page = pagination.get("lastPage", page)

    if current_page < last_page:
        return list_jobs(page=current_page + 1, jobs_list=jobs_list)
    else:
        return jobs_list

if __name__ == "__main__":
    all_jobs = list_jobs()
    # 印出所有資料，設定 ensure_ascii=False 以正確顯示中文，indent=2 提升可讀性
    print(json.dumps(all_jobs, ensure_ascii=False, indent=2))