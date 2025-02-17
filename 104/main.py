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

# 取的 jobs list，為什麼要依地區取？因為 104 API 只會傳最多 3000 筆資料，
# 所以如果一次選擇很多地區例如台北、新北、桃園，就算系統中有 2 萬筆資料，
# 104 還是只會回傳 3000 筆資料，應該都是一些有打廣告的公司。
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
# print(json.dumps(all_jobs, ensure_ascii=False, indent=2))
if all_jobs:
    result = collection.insert_many(all_jobs)
    print(f"成功插入 {len(result.inserted_ids)} 筆文件到 MongoDB。")
else:
    print("沒有資料可供插入。")