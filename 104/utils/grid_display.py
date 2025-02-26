import streamlit as st
from st_aggrid import AgGrid

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
    
    with st.container(): 
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.title(title)
        with col2:
            search_query = st.text_input("搜尋(逗號分隔)", "")
        with col3:
            exclude_query = st.text_input("排除(逗號分隔)", "")

    # 先根據包含關鍵字篩選
    if search_query:
        search_terms = [term.strip() for term in search_query.split(',')]
        mask = filtered_data.apply(
            lambda row: any(
                row.astype(str).str.contains(term, case=False, na=False).any()
                for term in search_terms
            ), axis=1
        )
        filtered_data = filtered_data[mask]

    # 再根據排除關鍵字進行過濾
    if exclude_query:
        exclude_terms = [term.strip() for term in exclude_query.split(',')]
        mask_exclude = filtered_data.apply(
            lambda row: all(
                not row.astype(str).str.contains(term, case=False, na=False).any()
                for term in exclude_terms
            ), axis=1
        )
        filtered_data = filtered_data[mask_exclude]

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
        "rowHeight": 100,
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
