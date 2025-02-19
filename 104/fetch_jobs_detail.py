import json
import time

# 自建模組
from utils import multi_thread_get_jobs, connect_db

# 連線資料庫、選擇要使用的資料庫與集合
client = connect_db()
db = client["104"]
jobs_collection = db["jobs"]
detail_collection = db["jobs_detail"]

# 取得所有文件，並從每份文件中取出 job id 與組成 ajax_url
documents = jobs_collection.find({})
job_urls = []
for doc in documents:
    if "link" in doc and "job" in doc["link"]:
        job_link = doc["link"]["job"]
        job_id = job_link.rstrip("/").split("/")[-1]
        ajax_url = f"https://www.104.com.tw/job/ajax/content/{job_id}"
        job_urls.append(ajax_url)

# 定義每一批次要處理的數量，例如每批處理 50 個 URL
batch_size = 50

# 分批次處理 job_urls
for i in range(0, len(job_urls), batch_size):
    batch_urls = job_urls[i:i + batch_size]

    # 先過濾掉已存在於 MongoDB 的 URL
    filtered_urls = []
    for url in batch_urls:
        if not detail_collection.find_one({"_id": url}):
            filtered_urls.append(url)

    # 如果過濾後的列表為空，則跳過本批次
    if not filtered_urls:
        print(f"批次 {(i // batch_size) + 1}/{(len(job_urls) + batch_size - 1) // batch_size} 中所有職缺資料皆已存在，跳過此批次")
        continue

    print(f"處理批次 {(i // batch_size) + 1}/{(len(job_urls) + batch_size - 1) // batch_size}")

    # 使用 multi_thread_get_jobs 處理這一批次，max_workers 設為過濾後的數量
    data_results = multi_thread_get_jobs(filtered_urls, max_workers=len(filtered_urls))

    # 將每個 URL 與對應的資料存入 MongoDB，並以 URL 作為主鍵 (_id)
    for url, data in data_results.items():
        try:
            job_detail = json.loads(data)
        except json.JSONDecodeError as e:
            print(f"解析 {url} 的 JSON 時發生錯誤：{e}")
            continue

        job_detail["_id"] = url
        try:
            detail_collection.replace_one({"_id": url}, job_detail, upsert=True)
            print(f"""儲存 / 更新 {url} 文件
公司：{job_detail["data"]["header"]["custName"]}
人數：{job_detail["data"]["employees"]}
薪資：{job_detail["data"]["jobDetail"]["salary"]}
職缺：{job_detail["data"]["header"]["jobName"]}""")
            print("==============================================================")
        except Exception as e:
            print(f"儲存 {url} 文件時發生錯誤：{e}")

    # 批次處理完後，等待一段時間以避免過快連續請求
    # wait = random.randint(3, 30)
    # print(f"等待 {wait} 秒後繼續")
    time.sleep(3)