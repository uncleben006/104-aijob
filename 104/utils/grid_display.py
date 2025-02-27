import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import re

def display_job_grid(data, title):
    """
    Display a job data grid with search and filter functionality
    
    Args:
        data: pandas DataFrame containing the job data
        title: str, the title to display above the grid
    """
    # 設定頁面佈局為 wide
    st.set_page_config(layout="wide")

    filtered_data = data.copy()
    total_count = len(data)
    
    # 創建一個容器來放置標題
    title_container = st.container()
    
    with st.container(): 
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            search_fields = st.multiselect(
                "選擇要搜尋的欄位 (多選)",
                options=filtered_data.columns.tolist(),
                default="job"
            )
        with col2:
            search_query = st.text_input("搜尋(逗號分隔)", "")
        with col3:
            exclude_fields = st.multiselect(
                "選擇要排除的欄位 (多選)",
                options=filtered_data.columns.tolist(),
                default="job"
            )
        with col4:
            exclude_query = st.text_input("排除(逗號分隔)", "")

    # 先根據包含關鍵字篩選
    if search_query and search_fields:
        search_terms = split_terms(search_query)
        mask = filtered_data.apply(
            lambda row: any(
                any(
                    term.lower() in str(row[field]).lower() 
                    for field in search_fields if pd.notna(row[field])
                )
                for term in search_terms
            ), axis=1
        )
        filtered_data = filtered_data[mask]

    # 再根據排除關鍵字進行過濾
    if exclude_query and exclude_fields:
        exclude_terms = split_terms(exclude_query)
        mask_exclude = filtered_data.apply(
            lambda row: all(
                not any(
                    term.lower() in str(row[field]).lower() 
                    for field in exclude_fields if pd.notna(row[field])
                )
                for term in exclude_terms
            ), axis=1
        )
        filtered_data = filtered_data[mask_exclude]
    
    # 更新標題顯示，包含過濾後的數據數量
    filtered_count = len(filtered_data)
    status_text = f"共 {filtered_count} 筆資料"
    if filtered_count < total_count:
        status_text += f" (原始資料: {total_count} 筆)"
    
    # 在標題容器中顯示標題和數據計數
    with title_container:
        st.html(f"<div><span style='font-size: 2em; font-weight: bold;'>{title}</span>\
        <span style='margin-left: 1em;'>{status_text}</span></div><hr>")

    # 建立完整的 columnDefs
    columns = []
    for col in filtered_data.columns:
        if col in ["other", "detail"]:
            columns.append({
                "field": col,
                "wrapText": True,
                "minWidth": 350,
                "cellStyle": {"overflow": "auto"},
            })
        elif col == "link":
            columns.append({
                "field": col,
                "wrapText": True,
                "minWidth": 220,
                "sortable": False
            })
        elif col in ["job", "company"]:
            columns.append({
                "field": col,
                "wrapText": True,
                "autoHeight": True,
                "minWidth": 220
            })
        else:
            columns.append({
                "field": col,
                "wrapText": True,
                "minWidth": 150
            })

    grid_options = {
        "columnDefs": columns,
        "rowHeight": 75,
        "headerHeight": 25,
        "defaultColDef": {
            "resizable": True,
            "sortable": True,
            "filter": True,
            "flex": 1,
            "minWidth": 150,
        },
        "domLayout": "normal"
    }

    return AgGrid(filtered_data, gridOptions=grid_options, height=750)

def split_terms(query):
    return [term.strip() for term in re.split(r'[,，、]', query) if term.strip()]
