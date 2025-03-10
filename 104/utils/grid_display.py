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
    """
    Split the query into terms and identify operators
    
    Parameters:
        query (str): The search query string
        
    Returns:
        list: A list of dictionaries containing terms and their operators
    """
    # Check if the query contains AND or OR operators
    has_and = "&" in query
    has_or = "|" in query
    
    if has_and and has_or:
        # If both operators are present, split by & first (AND has higher precedence)
        and_groups = query.split("&")
        result = []
        
        for and_group in and_groups:
            # For each AND group, split by | to get OR terms
            or_terms = and_group.split("|")
            or_terms = [term.strip() for term in or_terms if term.strip()]
            
            if len(or_terms) > 1:
                # If we have multiple OR terms in this group
                result.append({"operator": "OR", "terms": or_terms})
            elif len(or_terms) == 1:
                # If we have only one term in this group
                result.append({"operator": "SINGLE", "terms": or_terms})
        
        return result
    elif has_and:
        # If only AND operator is present
        terms = query.split("&")
        terms = [term.strip() for term in terms if term.strip()]
        return [{"operator": "SINGLE", "terms": [term]} for term in terms]
    elif has_or:
        # If only OR operator is present
        terms = query.split("|")
        terms = [term.strip() for term in terms if term.strip()]
        return [{"operator": "OR", "terms": terms}]
    else:
        # If no operators are present, split by traditional delimiters
        terms = re.split(r'[,，、]', query)
        terms = [term.strip() for term in terms if term.strip()]
        return [{"operator": "SINGLE", "terms": [term]} for term in terms]

def filter_by_keywords(data, parsed_terms):
    """
    Filter data based on keywords and specified fields with support for AND/OR operations
    
    Parameters:
        data (pd.DataFrame): The data to filter
        parsed_terms (list): List of dictionaries containing terms and operators
    
    Returns:
        pd.DataFrame: Filtered data
    """
    if not parsed_terms:
        return data
    
    # Process all groups with AND logic between them
    and_results = []
    
    for group in parsed_terms:
        group_terms = group["terms"]
        operator = group["operator"]
        
        if operator == "OR":
            # Process all terms in this group with OR logic
            or_mask = process_term(data, group_terms[0])
            for term in group_terms[1:]:
                or_mask = or_mask | process_term(data, term)
            and_results.append(or_mask)
        else:
            # Single term, no OR logic needed
            and_results.append(process_term(data, group_terms[0]))
    
    # Combine all group results with AND logic
    if and_results:
        final_mask = and_results[0]
        for mask in and_results[1:]:
            final_mask = final_mask & mask
        return data[final_mask]
    else:
        return data

def process_term(data, term):
    """
    Process a single search term
    
    Parameters:
        data (pd.DataFrame): The data to search in
        term (str): The search term
        
    Returns:
        pd.Series: Boolean mask indicating matches
    """
    # Check if term contains field specification
    if re.search(r'[:：]', term):
        # Split into field and search term
        field_term = re.split(r'[:：]', term, 1)
        field = field_term[0].strip()
        search_term = field_term[1].strip()
        
        if field in data.columns:
            # Search in specified field
            return data[field].astype(str).str.lower().str.contains(search_term.lower(), na=False)
        else:
            # If field doesn't exist, search in all columns
            all_fields_mask = False
            for col in data.columns:
                col_mask = data[col].astype(str).str.lower().str.contains(search_term.lower(), na=False)
                all_fields_mask = all_fields_mask | col_mask
            return all_fields_mask
    else:
        # No field specified, search in all columns
        all_fields_mask = False
        for col in data.columns:
            col_mask = data[col].astype(str).str.lower().str.contains(term.lower(), na=False)
            all_fields_mask = all_fields_mask | col_mask
        return all_fields_mask

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
    .stHorizontalBlock {
        align-items: end;
    }
    .stFormSubmitButton {
        text-align: center;
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
        col1, col2, col3 = st.columns([5, 5, 1])
        with col1:
            search_query = st.text_input(
                "搜尋（欄位:搜尋詞&欄位:搜尋詞|欄位:搜尋詞,...）（&為AND）（|為OR）", 
                f"{st.session_state.get('search_query', '')}"
            )
        with col2:
            history = collection.find({"grid_title": title}).sort("timestamp", -1)
            history_list = list(history)
            
            if history_list:

                # 創建選擇框
                selected_index = st.selectbox(
                    "選擇歷史記錄",
                    options=range(len(history_list))[:10], # 只保留前 10 筆
                    format_func=lambda i: f"{history_list[i]['timestamp'].strftime('%Y-%m-%d %H:%M')} -\
                        搜尋: {history_list[i]['search_query']}",
                    key=f"history_select_{title}",
                    index=st.session_state.get(f"selected_index_{title}", 0)
                )

                # 監聽選擇框變化
                if st.session_state.get(f"selected_index_{title}", 0) != selected_index:
                    st.session_state[f"selected_index_{title}"] = selected_index
                    selected_record = history_list[selected_index]
                    st.session_state["search_query"] = selected_record["search_query"]
                    st.session_state["exclude_query"] = selected_record["exclude_query"]
                    st.rerun()
        with col3:
            submit = st.form_submit_button("搜尋")
        
        if submit:

            # 若搜尋欄位和排除欄位都為空，則不做紀錄
            if not search_query:
                st.rerun()

            # 創建搜尋記錄
            search_record = {
                "grid_title": title,
                "search_query": search_query,
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

    # 先根據包含關鍵字篩選
    if search_query:
        # 先將 search_query 分割成多個關鍵字
        search_terms = split_terms(search_query)
        filtered_data = filter_by_keywords(filtered_data, search_terms)

    # 更新標題顯示，包含過濾後的數據數量
    filtered_count = len(filtered_data)
    status_text = f"共 {filtered_count} 筆資料"
    if filtered_count < total_count:
        status_text += f" (原始資料: {total_count} 筆)"
    
    # 在標題容器中顯示標題和數據計數
    with title_container:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.html(f"<div style='display: flex; align-items: center;'>\
                <span style='font-size: 1.5em; font-weight: bold;'>{title}</span></div>")
        with col2:
            st.html(f"<div style='display: flex; align-items: center; justify-content: end;'>\
                <span style='font-size: 1em;'>{status_text}</span></div>")
        

    # 建立完整的 columnDefs，參考 https://ag-grid.com/javascript-data-grid/cell-editing/
    link_cell_renderer = JsCode("""
        class ButtonCellRenderer {
            init(params) {
                this.eGui = document.createElement('button');
                this.eGui.innerText = "連結";
                this.eGui.style.backgroundColor = "grey";  // Grey background
                this.eGui.style.color = "white";  // White text
                this.eGui.style.cursor = "pointer";
                
                // Add click event listener
                this.eGui.addEventListener('click', () => {
                    window.open(params.value, "_blank");
                });
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
                "resizable": True,
                "sortable": True,
                "filter": True,
                "field": col, "wrapText": True, 
                "minWidth": 350, "cellStyle": {"overflow": "auto"}
            })
        elif col in ["link"]:
            columns.append({ 
                "field": col, "wrapText": True,
                "autoHeight": True, "minWidth": 75,
                "cellRenderer": link_cell_renderer,
                "cellStyle": {"display": "flex", "justify-content": "center", "align-items": "center"}
            })
        else:
            columns.append({ 
                "resizable": True,
                "sortable": True,
                "filter": True,
                "field": col, "wrapText": True, 
                "minWidth": 150, "cellStyle": {"overflow": "auto"}
            })

    grid_options = {
        "columnDefs": columns,
        "rowHeight": 75,
        "headerHeight": 25,
        "defaultColDef": {
            "flex": 1,
            "minWidth": 150,
        },
        "domLayout": "normal"
    }

    return AgGrid(filtered_data, gridOptions=grid_options, height=750, allow_unsafe_jscode=True, key='grid')
