#### streamlit run 104/top_500.py ####

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
from utils import top_500

# 讀取並處理資料
csv_filename = '104/taiwan_500.csv'
top_500_company_jobs = top_500(csv_filename)

st.set_page_config(layout="wide") # 設定頁面佈局為 wide

# 根據使用者輸入篩選資料
filtered_data = pd.DataFrame(top_500_company_jobs).copy()
categories = ["全部"] + sorted(filtered_data["company"].unique().tolist())

with st.container(): 
    col1, col2, col3, col4 = st.columns([4, 3, 1, 1])
    with col1:
        st.title("台灣 500 大公司")
    with col2:
        selected_category = st.selectbox("選擇公司", categories)
    with col3:
        search_query = st.text_input("搜尋", "")
    with col4:
        exclude_query = st.text_input("排除", "")

# 先根據包含關鍵字篩選
if search_query:
    mask = filtered_data.apply(
        lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1
    )
    filtered_data = filtered_data[mask]

# 再根據排除關鍵字進行過濾
if exclude_query:
    mask_exclude = filtered_data.apply(
        lambda row: not row.astype(str).str.contains(exclude_query, case=False, na=False).any(), axis=1
    )
    filtered_data = filtered_data[mask_exclude]

if selected_category != "全部":
    filtered_data = filtered_data[filtered_data["company"] == selected_category]

# 建立完整的 columnDefs，針對 "other" 與 "detail" 欄位加入設定
columns = []
for col in filtered_data.columns:
    print(col)
    if col in ["other", "detail"]:
        columns.append({
            "field": col,
            "wrapText": True,    # 啟用文字換行
            "minWidth": 350,
            "cellStyle": {"overflow": "auto"},
        })
    elif col == "link":
        columns.append({
            "field": col,
            "wrapText": True,    # 啟用文字換行
            "minWidth": 220,
            "sortable": False      # 禁用排序，因為這是 HTML 內容
        })
    elif col in ["job","company"]:
        columns.append({
            "field": col,
            "wrapText": True,    # 啟用文字換行
            "autoHeight": True,   # 根據內容自動調整高度
            "minWidth":  220
        })
        columns.append({
            "field": col,
            "wrapText": True,    # 啟用文字換行
            "autoHeight": True,   # 根據內容自動調整高度
            "minWidth":  220
        })
    else:
        # 其他欄位完整顯示內容
        columns.append({
            "field": col,
            "wrapText": True,    # 啟用文字換行
            "minWidth": 150
        })

grid_options = {
    "columnDefs": columns,
    "rowHeight": 100,  # 設定每一行的固定高度
    "headerHeight": 25,  # 設定表頭高度
    "defaultColDef": {
        "resizable": True,
        "sortable": True,
        "filter": True,
        "flex": 1,       # 自動調整欄寬
        "minWidth": 150, # 最小寬度
    },
    "domLayout": "normal"  # 固定高度模式
}

AgGrid(filtered_data, gridOptions=grid_options, height=750)