import os
import re
import json
import time
import random
from dotenv import load_dotenv
from pymongo import MongoClient

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
collection = db["jobs_detail"]

# 從 jobs_detail 集合取出所有資料
pipeline = [
    {
        "$project": {
            "_id": 0,
            "link": {
                "$concat": [
                    "https://www.104.com.tw/job/",
                    {
                        "$substrCP": [
                            "$_id",
                            {"$subtract": [{"$strLenCP": "$_id"}, 5]},
                            5
                        ]
                    }
                ]
            },
            "job": "$data.header.jobName",
            "company": "$data.header.custName",
            "address": "$data.jobDetail.addressRegion",
            "industry": "$data.industry",
            "employees": {
                "$cond": [
                    {"$eq": ["$data.employees", "暫不提供"]},
                    0,
                    {
                        "$toInt": {
                            "$replaceAll": {
                                "input": "$data.employees",
                                "find": "人",
                                "replacement": ""
                            }
                        }
                    }
                ]
            },
            "salary": "$data.jobDetail.salary",
            "salaryType": "$data.jobDetail.salaryType",
            "specialty": {
                "$reduce": {
                    "input": {
                        "$map": {
                            "input": "$data.condition.specialty",
                            "as": "item",
                            "in": "$$item.description"
                        }
                    },
                    "initialValue": "",
                    "in": {
                        "$concat": [
                            "$$value",
                            {"$cond": [{"$eq": ["$$value", ""]}, "", ", "]},
                            "$$this"
                        ]
                    }
                }
            },
            "skill": {
                "$reduce": {
                    "input": {
                        "$map": {
                            "input": "$data.condition.skill",
                            "as": "item",
                            "in": "$$item.description"
                        }
                    },
                    "initialValue": "",
                    "in": {
                        "$concat": [
                            "$$value",
                            {"$cond": [{"$eq": ["$$value", ""]}, "", ", "]},
                            "$$this"
                        ]
                    }
                }
            },
            "other": "$data.condition.other",
            "detail": "$data.jobDetail.jobDescription"
        }
    },
    {
        "$match": {
            "$and": [
                {"job": {"$not": re.compile("企劃|業務")}},
                {"other": {"$not": re.compile("企劃|業務")}},
                {"detail": {"$not": re.compile("企劃|業務")}}
            ]
        }
    },
    {
        "$sort": {"employees": 1}
    }
]

# 執行 Aggregation Pipeline
results = collection.aggregate(pipeline)

for job_detail in results:
    # print(job_detail["_id"])
    print(job_detail)
# 將取得的資料轉成 JSON 格式的陣列並印出
# print(json.dumps(jobs_detail_data, ensure_ascii=False, indent=2))

