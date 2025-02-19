# 自建模組
from utils import list_jobs, connect_db

# 連線資料庫、選擇要使用的資料庫與集合
client = connect_db()
db = client["104"]
collection = db["jobs"]

# 定義要查詢的地區
areas = [
    "6001001001", "6001001002", "6001001003", "6001001004",  # 中正、大同、中山、松山
    "6001001005", "6001001006", "6001001007", "6001001011",  # 大安、萬華、信義、南港
    "6001002003", "6001002014", "6001002015", "6001002016",  # 板橋、永和、中和、土城
    "6001002017", "6001002018", "6001002019", "6001002020",  # 三峽、鶯歌、樹林、三重
    "6001002021", "6001002022", "6001002024", "6001002025",  # 新莊、泰山、蘆洲、五股
    "6001005000",  # 桃園
    "6001006000",  # 新竹
]

# 取得 jobs list
all_jobs = list_jobs(areas)

if all_jobs:
    # 逐筆處理 jobs，如果 job["_id"] 重複則取代原有文件
    for job in all_jobs:
        # 使用 link.job 當作 _id
        job_id = job["link"]["job"]
        job["_id"] = job_id

        # 若 _id 已存在則會被取代，若不存在則會插入新文件
        collection.replace_one({"_id": job_id}, job, upsert=True)
    
    print(f"成功 upsert {len(all_jobs)} 筆文件到 MongoDB。")
else:
    print("沒有資料可供插入。")