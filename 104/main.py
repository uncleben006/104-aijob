import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient

# 自建 module
from utils import list_jobs

# 載入 .env 檔案中的環境變數
load_dotenv()

# 讀取環境變數
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "root")

# 建立 MongoDB 連線字串（假設 MongoDB 在本機運行）
uri = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@localhost:{MONGO_PORT}"
client = MongoClient(uri)

# 選擇要使用的資料庫與集合
db = client["104"]
collection = db["jobs"]

# 取的 jobs list
all_jobs = list_jobs()
# print(json.dumps(all_jobs, ensure_ascii=False, indent=2))
if all_jobs:
    result = collection.insert_many(all_jobs)
    print(f"成功插入 {len(result.inserted_ids)} 筆文件到 MongoDB。")
else:
    print("沒有資料可供插入。")