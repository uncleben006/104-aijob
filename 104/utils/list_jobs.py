import json
import time
import random
import requests
from urllib.parse import quote_plus

def list_jobs_by_area(area_id, page=1, jobs_list=None):
    """
    針對單一區域，遞迴取得該區域所有分頁的職缺資料。
    """
    if jobs_list is None: jobs_list = []
    
    # URL 參數
    base_url = "https://www.104.com.tw/jobs/search/api/jobs"
    jobsource = "joblist_search"
    keyword_raw = "python, AI, 數據"
    keyword = quote_plus(keyword_raw)
    mode = "s"
    pagesize = 500

    params = {
        "area": area_id,
        "jobsource": jobsource,
        "keyword": keyword_raw,
        "mode": mode,
        "page": page,
        "pagesize": pagesize
    }

    referer = (
        f"https://www.104.com.tw/jobs/search/?jobsource={jobsource}"
        f"&keyword={keyword}&mode={mode}&order=15&page={page}"
        f"&area={area_id}&pagesize={pagesize}&version={random.randint(1, 1000)}"
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

    print(f"爬取第 {page} 頁: ", end=" ")
    response = requests.get(base_url, headers=headers, params=params)
    data = response.json()
    print(response.text[:22] + "..." + response.text[-20:])

    # 出現錯誤則 10 秒後重試一次
    if "error" in data:
        print("發生錯誤，3 秒後重試...")
        time.sleep(3)
        return list_jobs_by_area(area_id, page, jobs_list)
    
    # 取得該頁資料
    try: jobs = data["data"] 
    except Exception as e: print(f"中斷程式：無法取得此地區第 {page} 頁的資料，可能是 104 或網路問題")
    jobs_list.extend(jobs)

    # 取得分頁資訊，若還有下一頁，則繼續遞迴
    metadata = data.get("metadata")
    pagination = metadata.get("pagination")
    expected_total = pagination.get("total")
    current_page = pagination.get("currentPage", page)
    last_page = pagination.get("lastPage", page)

    if current_page < last_page:
        time.sleep(2) # 等待 2 秒以防止過快連續請求
        return list_jobs_by_area(area_id, current_page + 1, jobs_list)
    else:
        # 當所有分頁取回後，將 link 作為 ID，並回傳職缺資料以及預計數量
        seen_jobs, unique_jobs = set(), []
        for job in jobs_list:
            job_id = job["link"]["job"]
            if job_id not in seen_jobs:
                seen_jobs.add(job_id)
                unique_jobs.append(job)
        return unique_jobs, expected_total

def list_jobs(areas, index=0, all_jobs=None):
    """
    針對多個區域的陣列，用遞迴依序取得每個區域的職缺資料，
    並合併所有結果。
    """

    if all_jobs is None: all_jobs = []

    # 終止條件：當 index 超過陣列長度，就回傳結果
    if index >= len(areas): 
        seen_jobs, unique_jobs = set(), []
        for job in all_jobs:
            job_id = job["link"]["job"]
            if job_id not in seen_jobs:
                seen_jobs.add(job_id)
                job["_id"] = job_id
                unique_jobs.append(job)
        return unique_jobs

    area_keys = list(areas.keys())
    current_area_id = area_keys[index]
    current_area = areas[current_area_id]
    print(f"開始爬取 {current_area}區 職缺...")
    area_jobs, expected_total = list_jobs_by_area(current_area_id) # 逐頁取得該地區資料
    print(f"{current_area}地區職缺預期總數：{expected_total}")
    print(f"{current_area}地區職缺實際取得數：{len(area_jobs)}")
    print("==============================================================")
    all_jobs.extend(area_jobs)
    return list_jobs(areas, index + 1, all_jobs)

# 使用範例
if __name__ == "__main__":
    # 將各區域代碼整理成陣列（可根據需求調整）
    areas = {
        "6001001001": "中正",
        "6001001002": "大同",
        "6001001003": "中山",
        "6001001004": "松山",
        "6001001005": "大安",
        "6001001006": "萬華",
        "6001001007": "信義",
        "6001001011": "南港",
        "6001002003": "板橋",
        "6001002014": "永和",
        "6001002015": "中和",
        "6001002016": "土城",
        "6001002017": "三峽",
        "6001002018": "鶯歌",
        "6001002019": "樹林",
        "6001002020": "三重",
        "6001002021": "新莊",
        "6001002022": "泰山",
        "6001002024": "蘆洲",
        "6001002025": "五股",
        "6001005000": "桃園",
        "6001006000": "新竹",
    }
    all_jobs = list_jobs(areas)
    # 印出所有職缺資料，設定 ensure_ascii=False 以正確顯示中文，indent=2 提升可讀性
    print(json.dumps(all_jobs, ensure_ascii=False, indent=2))