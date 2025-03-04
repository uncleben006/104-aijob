#!/bin/bash
set -e

# 啟動 cron，放到背景執行
cron &

# 啟動第一個 Streamlit 應用，綁定 8501 port
streamlit run 104/app.py --server.port=8501 &

# 啟動第二個 Streamlit 應用，綁定 8502 port
streamlit run 104/top_500.py --server.port=8502 &

# 等待所有背景進程，保持 container 存活
wait