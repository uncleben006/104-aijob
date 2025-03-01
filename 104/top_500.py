import pandas as pd
from utils import top_500, display_job_grid

# 讀取並處理資料
csv_filename = '104/taiwan_500.csv'
top_500_company_jobs = top_500(csv_filename)

# 根據使用者輸入篩選資料
filtered_data = pd.DataFrame(top_500_company_jobs).copy()

# 使用 streamlit run 顯示資料
display_job_grid(filtered_data, title="前500公司職缺")