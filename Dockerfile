FROM python:3.13-slim

# 安裝 cron 與其他系統套件
RUN apt-get update && apt-get install -y cron

# 安裝 Poetry
RUN pip install poetry

WORKDIR /app

# 複製 Poetry 依賴檔案
COPY pyproject.toml poetry.lock ./

# 設定 Poetry 不建立虛擬環境，並全域安裝依賴（不安裝專案本身）
RUN poetry config virtualenvs.create false && poetry install --no-root

# 複製所有專案檔案
COPY . .

# 複製 crontab 設定檔
COPY my-cron /etc/cron.d/my-cron

# 補上缺失的換行符、修改權限並載入 crontab
RUN sed -i -e '$a\' /etc/cron.d/my-cron && \
    chmod 0644 /etc/cron.d/my-cron && \
    crontab /etc/cron.d/my-cron

# 建立 log 檔以供 cron 輸出記錄
RUN touch /var/log/cron.log

# 前景執行 cron
CMD ["cron", "-f"]