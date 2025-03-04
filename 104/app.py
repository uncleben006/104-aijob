import re
import pandas as pd
from utils import connect_db, jobs_detail_project, display_job_grid, jobs_condition

# 連線資料庫、選擇要使用的資料庫與集合
client = connect_db()
db = client["104"]
collection = db["jobs_detail"]

# mongodb pipeline
project = jobs_detail_project() # 顯示 jobs_detail 中所需欄位
condition = jobs_condition() # 篩選掉我不想要的職務 title
sort = { '$sort': {'company': -1} }
pipeline = [project, condition, sort]

# 執行 Aggregation Pipeline
filtered_data = pd.DataFrame(pd.DataFrame(collection.aggregate(pipeline, allowDiskUse=True))).copy()

# 使用 streamlit run 顯示資料
display_job_grid(filtered_data, title="AI相關職缺")