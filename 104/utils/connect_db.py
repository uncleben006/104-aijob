import os
from dotenv import load_dotenv
from pymongo import MongoClient

# 載入 .env 檔案中的環境變數
load_dotenv()

def connect_db():
    # 讀取環境變數
    MONGO_PORT = os.getenv("MONGO_PORT", "27017")
    MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
    MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "root")

    # 建立 MongoDB 連線字串（假設 MongoDB 在本機運行）
    uri = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@localhost:{MONGO_PORT}"
    return MongoClient(uri)