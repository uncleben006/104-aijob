import re
import pandas as pd
from utils import connect_db, jobs_detail_project, display_job_grid

# 連線資料庫、選擇要使用的資料庫與集合
client = connect_db()
db = client["104"]
collection = db["jobs_detail"]

# mongodb pipeline
project = jobs_detail_project() # 顯示 jobs_detail 中所需欄位
condition = { '$match': {'job': { '$not': re.compile(r"企劃|業務|助理|PM") } } } 
sort = { '$sort': {'company': -1} }
pipeline = [project, condition, sort]

# 執行 Aggregation Pipeline
filtered_data = pd.DataFrame(pd.DataFrame(collection.aggregate(pipeline))).copy()

# 使用 streamlit run 顯示資料
display_job_grid(filtered_data, title="所有職缺資料")