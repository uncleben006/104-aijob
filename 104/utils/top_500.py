import csv
import re
from .connect_db import connect_db, jobs_detail_project, jobs_condition

def top_500(csv_filename="104/taiwan_500.csv"):
    
    # 讀取 CSV 檔案，這次以「公司名稱」作為 key
    top_companies = {}
    with open(csv_filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 注意去除可能多餘的空白
            company_name = row['公司名稱'].strip()
            top_companies[company_name] = row

    # 取得 CSV 中所有的公司名稱
    company_names = list(top_companies.keys())

    # 連線資料庫，選擇使用的資料庫與集合
    client = connect_db()
    db = client["104"]
    collection = db["jobs_detail"]

    # mongodb pipeline
    project = jobs_detail_project() # 顯示 jobs_detail 中所需欄位
    condition = jobs_condition()
    sort = { '$sort': {'company': -1} }
    pipeline = [project, condition, sort]

    # record-by-record 交叉比對的方式
    matched_jobs = []
    for doc in collection.aggregate(pipeline, allowDiskUse=True):
        cust_name = doc["company"]
        # 檢查是否有任一個註冊名稱存在於 cust_name 中
        if any(registered_name in cust_name for registered_name in company_names):
            matched_jobs.append(doc)

    cust_name_set =  set(doc["company"] for doc in matched_jobs)
    missing = len(set(company_names)) - len(cust_name_set)

    print(f"已找到 {len(matched_jobs)} 筆符合條件且位於前五百大企業的職缺資料")
    print(f"全台前五百大企業中有 {len(cust_name_set)} 間公司開放職缺於 104 當中")
    print(f"全台前五百大企業中有 {missing} 間公司未在 104 中開放職缺")
    return matched_jobs

if __name__ == '__main__':
    top_500()