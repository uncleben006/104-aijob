import re
import pandas as pd
import streamlit as st
# https://staggrid-examples.streamlit.app/ AgGrid document
from st_aggrid import AgGrid
from st_aggrid import JsCode
from .connect_db import connect_db
import datetime
import hashlib
import json

def split_terms(query):
    return [term.strip() for term in re.split(r'[,，、]', query) if term.strip()]

def filter_by_keywords(data, query, fields):
    """
    根據關鍵字和指定欄位篩選數據
    
    參數:
        data (pd.DataFrame): 要篩選的數據
        query (str): 搜尋關鍵字，多個關鍵字用逗號分隔
        fields (list): 要搜尋的欄位列表
    
    返回:
        pd.DataFrame: 篩選後的數據
    """
    if not query or not fields:
        return data
    
    search_terms = split_terms(query)
    mask = data.apply(
        lambda row: any(
            any(
                term.lower() in str(row[field]).lower() 
                for field in fields if pd.notna(row[field])
            )
            for term in search_terms
        ), axis=1
    )
    return data[mask]

def filter_by_exclusion(data, query, fields):
    """
    根據排除關鍵字和指定欄位篩選數據
    
    參數:
        data (pd.DataFrame): 要篩選的數據
        query (str): 排除關鍵字，多個關鍵字用逗號分隔
        fields (list): 要排除的欄位列表
    
    返回:
        pd.DataFrame: 篩選後的數據
    """
    if not query or not fields:
        return data
    
    exclude_terms = split_terms(query)
    mask = data.apply(
        lambda row: all(
            not any(
                term.lower() in str(row[field]).lower() 
                for field in fields if pd.notna(row[field])
            )
            for term in exclude_terms
        ), axis=1
    )
    return data[mask]

def display_job_grid(data, title):
    """
    顯示職缺網格
    
    參數:
        data (pd.DataFrame): 職缺數據
        title (str): 網格標題
    """

    # 連線資料庫，選擇使用的資料庫與集合
    client = connect_db()
    db = client["104"]
    collection = db["search_history"]

    # 設定頁面佈局為 wide
    st.set_page_config(layout="wide")

    # 初始化 filtered_data
    filtered_data = data.copy()
    total_count = len(data)
    
    # 創建一個容器來放置標題
    title_container = st.container()
    
    # 自定義 CSS, 隱藏提交按鈕, 調整 selectbox 
    st.markdown("""
    <style>
    div[data-testid="stFormSubmitButton"] {
        visibility: hidden;
        height: 0px;
    }
    .stSelectbox > div > div {
        font-size: 14px !important;
    }
    .stTooltipHoverTarget {
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 使用表單來包含所有搜尋欄位
    with st.form(key="search_form"):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            search_fields = st.multiselect(
                "選擇要搜尋的欄位 (多選)",
                options=filtered_data.columns.tolist(),
                default=st.session_state.get("search_fields", ['job'])
            )
        with col2:
            search_query = st.text_input(
                "搜尋(逗號分隔)", 
                f"{st.session_state.get('search_query', '')}"
            )
        with col3:
            exclude_fields = st.multiselect(
                "選擇要排除的欄位 (多選)",
                options=filtered_data.columns.tolist(),
                default=st.session_state.get("exclude_fields", ['job'])
            )
        with col4:
            exclude_query = st.text_input(
                "排除(逗號分隔)", 
                f"{st.session_state.get('exclude_query', '')}"
            )

        submit = st.form_submit_button("搜尋")

    # 先根據包含關鍵字篩選
    if search_query and search_fields:
        filtered_data = filter_by_keywords(filtered_data, search_query, search_fields)

    # 再根據排除關鍵字進行過濾
    if exclude_query and exclude_fields:
        filtered_data = filter_by_exclusion(filtered_data, exclude_query, exclude_fields)

    # 更新標題顯示，包含過濾後的數據數量
    filtered_count = len(filtered_data)
    status_text = f"共 {filtered_count} 筆資料"
    if filtered_count < total_count:
        status_text += f" (原始資料: {total_count} 筆)"
    
    # 在標題容器中顯示標題和數據計數
    with title_container:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.html(f"<div style='display: flex; align-items: center;'>\
                <span style='font-size: 1.5em; font-weight: bold;'>{title}</span></div>")
        with col2:
            history = collection.find({"grid_title": title}).sort("timestamp", -1)
            history_list = list(history)
            
            if history_list:

                # 創建選擇框
                selected_index = st.selectbox(
                    "選擇歷史記錄",
                    options=range(len(history_list))[:10], # 只保留前 10 筆
                    format_func=lambda i: f"{history_list[i]['timestamp'].strftime('%Y-%m-%d %H:%M')} -\
                        搜尋: {history_list[i]['search_query']} | \
                        排除:{history_list[i]['exclude_query']}",
                    key=f"history_select_{title}",
                    index=st.session_state.get(f"selected_index_{title}", 0)
                )

                # 監聽選擇框變化
                if st.session_state.get(f"selected_index_{title}", 0) != selected_index:
                    st.session_state[f"selected_index_{title}"] = selected_index
                    selected_record = history_list[selected_index]
                    st.session_state["search_query"] = selected_record["search_query"]
                    st.session_state["search_fields"] = selected_record["search_fields"]
                    st.session_state["exclude_query"] = selected_record["exclude_query"]
                    st.session_state["exclude_fields"] = selected_record["exclude_fields"]
                    st.rerun()
        with col3:
            st.html(f"<div style='display: flex; align-items: center; justify-content: end;'>\
                <span style='font-size: 1em;'>{status_text}</span></div>")
        

    # 建立完整的 columnDefs，參考 https://ag-grid.com/javascript-data-grid/cell-editing/
    link_cell_renderer = JsCode("""
        class LinkCellRenderer {
            init(params) {
                this.eGui = document.createElement('a');
                this.eGui.innerText = params.value;
                this.eGui.href = params.value;
                this.eGui.target = "_blank";  // 讓連結在新分頁開啟
                this.eGui.style.color = "blue";  // 設定超連結顏色
                this.eGui.style.textDecoration = "underline";  // 加底線
            }
            getGui() {
                return this.eGui;
            }
        }
    """)

    columns = []
    for col in filtered_data.columns:
        if col in ["other", "detail"]:
            columns.append({ 
                "field": col, "wrapText": True, 
                "minWidth": 350, "cellStyle": {"overflow": "auto"}
            })
        elif col in ["link"]:
            columns.append({ 
                "field": col, "wrapText": True,
                "autoHeight": True, "minWidth": 220,
                "cellRenderer": link_cell_renderer
            })
        else:
            columns.append({ 
                "field": col, "wrapText": True, 
                "minWidth": 150, "cellStyle": {"overflow": "auto"}
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

    if submit:

        # 若搜尋欄位和排除欄位都為空，則不做紀錄
        if not search_query and not exclude_query:
            st.rerun()

        # 創建搜尋記錄
        search_record = {
            "grid_title": title,
            "search_fields": search_fields,
            "search_query": search_query,
            "exclude_fields": exclude_fields,
            "exclude_query": exclude_query,
            "timestamp": datetime.datetime.now(),
            "result_count": len(filtered_data)
        }
        
        # 生成唯一ID 並檢查是否有搜過同樣內容
        record_str = json.dumps(
            {k: v for k, v in search_record.items() if k != "timestamp"}, 
            sort_keys=True
        )
        search_id = hashlib.md5(record_str.encode()).hexdigest()
        search_record["_id"] = search_id
        existing_record = collection.find_one({"_id": search_id})
        if not existing_record:
            collection.insert_one(search_record)
            # with title_container: st.success(f"已儲存搜尋記錄")
        else:
            collection.update_one(
                {"_id": search_id},
                {"$set": {"timestamp": datetime.datetime.now()}}
            )
            # with title_container:st.info(f"已更新搜尋記錄時間戳")
        st.rerun()

    return AgGrid(filtered_data, gridOptions=grid_options, height=750, allow_unsafe_jscode=True, key='grid')
