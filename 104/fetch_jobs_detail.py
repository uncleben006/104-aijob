import json
import time

# 自建模組
from utils import multi_thread_get_jobs, connect_db

# 連線資料庫、選擇要使用的資料庫與集合
client = connect_db()
db = client["104"]
jobs_collection = db["jobs"]
detail_collection = db["jobs_detail"]

# 取得爬下的所有職缺列表
documents = jobs_collection.find({})
job_urls = [doc["_id"] for doc in documents]

# 從職缺詳情中刪除已經關閉的職缺資料
result = detail_collection.delete_many({"_id": {"$nin": job_urls}})
print(f"刪除 {result.deleted_count} 筆已關閉的職缺詳情")

# 找到未爬取的職缺 URL
fetched_urls = [doc["_id"] for doc in detail_collection.find({}, {"_id": 1})]
remaining_urls = set(job_urls) - set(fetched_urls)

# remaining_urls 是頁面 URL，要轉成 ajax URL 來爬取職缺詳情
job_ajax_urls = []
for url in remaining_urls:
    job_id = url.rstrip("/").split("/")[-1]
    ajax_url = f"https://www.104.com.tw/job/ajax/content/{job_id}"
    job_ajax_urls.append(ajax_url)

# 分批爬取尚未爬取過的 job_ajax_urls
batch_size = 50
for i in range(0, len(job_ajax_urls), batch_size):
    batch_urls = job_ajax_urls[i:i + batch_size]
    print(f"處理批次 {(i // batch_size) + 1}/{(len(job_ajax_urls) + batch_size - 1) // batch_size}")

    # 使用 multi_thread_get_jobs 處理這一批次
    data_results = multi_thread_get_jobs(batch_urls)

    # 將每個 URL 與對應的資料存入 MongoDB，並以 URL 作為主鍵 (_id)
    for url, data in data_results.items():
        try:
            job_detail = json.loads(data)
        except json.JSONDecodeError as e:
            print(f"解析 {url} 的 JSON 時發生錯誤：{e}")
            continue

        job_detail = job_detail["data"]
        job_detail["_id"] = url
        try:
            detail_collection.insert_one(job_detail)
            print(f"儲存 {url} 文件成功")
            print(f"公司：{job_detail['header']['custName']}")
            print(f"人數：{job_detail['employees']}")
            print(f"薪資：{job_detail['jobDetail']['salary']}")
            print(f"職缺：{job_detail['header']['jobName']}")
            print("==============================================")
        except Exception as e:
            print(f"儲存 {url} 文件時發生錯誤：{e}")

    time.sleep(3)