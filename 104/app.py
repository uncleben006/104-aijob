import streamlit as st
import re

# 自建模組
from utils import connect_db

# 連線資料庫、選擇要使用的資料庫與集合
client = connect_db()
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
            "$or": [
                {"job": re.compile("企劃|業務")},
                {"other": re.compile("企劃|業務")},
                {"detail": re.compile("企劃|業務")}
            ]
        }
    },
    {
        "$sort": {"employees": 1}
    }
]

# 執行 Aggregation Pipeline
data = list(collection.aggregate(pipeline))

# 使用 Streamlit 建立網頁介面
st.title("MongoDB 資料檢視器")
st.write("以下是篩選及排序後的資料：")
st.dataframe(data)  # 使用 dataframe 呈現資料，也可以用 st.write(data)

# for job_detail in results:
#     # print(job_detail["_id"])
#     print(job_detail)
# # 將取得的資料轉成 JSON 格式的陣列並印出
# # print(json.dumps(jobs_detail_data, ensure_ascii=False, indent=2))

