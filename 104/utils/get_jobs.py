import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 單一請求的函式
def fetch_data(url):
    time.sleep(1)
    payload = {}
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,de;q=0.5,fr;q=0.4,ko;q=0.3,ja;q=0.2',
        'Connection': 'keep-alive',
        'Referer': url,  
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }
    
    while True:
        try:
            response = requests.get(url, headers=headers, data=payload, timeout=10)
            if response.status_code == 429:
                print(f"收到 429 回應，等待 30 秒後再重試... ({url})")
                time.sleep(30)
                continue  # 重新嘗試請求
            response.raise_for_status()  # 如果狀態碼不在 200~299 會拋出例外
            return response.text
        except Exception as e:
            return f"Error fetching {url}: {e}"

# 多線程取得所有資料
def multi_thread_get_jobs(url_list, max_workers=5):
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_data, url): url for url in url_list}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            results[url] = future.result()
    return results

# 測試用範例
if __name__ == '__main__':
    url_list = [
        "https://www.104.com.tw/job/ajax/content/7n189"
    ]
    data_results = multi_thread_get_jobs(url_list, max_workers=10)