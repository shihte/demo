from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import csv
import os
import webbrowser
import threading
import time
import argparse
import sys
import logging

app = Flask(__name__)
CORS(app)

# 設置日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_resource_path(relative_path):
    """獲取資源的絕對路徑"""
    try:
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.dirname(__file__))
        
        full_path = os.path.join(base_path, relative_path)
        logger.debug(f"Resource path for {relative_path}: {full_path}")
        return full_path
    except Exception as e:
        logger.error(f"Error getting resource path: {e}")
        return os.path.abspath(relative_path)

# 重新定義目錄結構
current_dir = os.path.dirname(os.path.abspath(__file__))
happyread_dir = os.path.join(current_dir, 'happyread')  # CSV文件所在目錄
static_dir = current_dir  # 靜態文件目錄

logger.info(f"Current dir: {current_dir}")
logger.info(f"Happyread dir: {happyread_dir}")
logger.info(f"Static dir: {static_dir}")

def validate_id(id_str):
    """驗證ID是否有效"""
    try:
        id_num = int(id_str)
        return 1 <= id_num <= 184
    except ValueError:
        return False

def open_browser(host, port, delay):
    """在新線程中等待服務器啟動後打開瀏覽器"""
    def _open_browser():
        time.sleep(delay)
        url = f'http://{host}:{port}'
        webbrowser.open(url)
    
    thread = threading.Thread(target=_open_browser)
    thread.daemon = True
    thread.start()

def opencsv(ID):
    """打開並讀取CSV文件"""
    try:
        file_path = os.path.join(happyread_dir, f"Book_{ID}.csv")
        logger.debug(f"Opening CSV file: {file_path}")
        with open(file_path, "r", newline="", encoding="utf-8") as open_XID_csv:
            csv_reader = csv.reader(open_XID_csv)
            first_column = [row[0] for row in csv_reader]
            return first_column[1:]
    except FileNotFoundError:
        logger.error(f"CSV file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error opening CSV: {e}")
        return []

def search_in_book_all(question_numbers):
    """搜索多個題目"""
    results = []
    file_path = os.path.join(happyread_dir, "book_all.csv")
    logger.debug(f"Searching in book_all.csv: {file_path}")
    try:
        with open(file_path, "r", newline="", encoding="utf-8") as book_answer:
            csv_reader = list(csv.reader(book_answer))
            for number in question_numbers:
                found = False
                for row in csv_reader:
                    if row and row[0] == number:
                        answer = row[6] if row[6] else "未新增解答"
                        if answer != "未新增解答":
                            results.append({"question": row[1], "answer": answer})
                        found = True
                        break
                if not found:
                    results.append({"question": f"題號 {number}", "answer": "找不到相關題目，請檢查是否有錯字"})
    except Exception as e:
        logger.error(f"Error searching book_all: {e}")
        return [{"question": "錯誤", "answer": "找不到相關題目，請檢查是否有錯字"}]
    return results

def search(text):
    """搜索單個題目或關鍵字"""
    results = []
    file_path = os.path.join(happyread_dir, "book_all.csv")
    logger.debug(f"Searching text '{text}' in book_all.csv: {file_path}")
    try:
        with open(file_path, "r", newline="", encoding="utf-8") as book_answer:
            csv_reader = list(csv.reader(book_answer))
            if text.isdigit():
                found = False
                for row in csv_reader:
                    if row and row[0] == text:
                        answer = row[6] if row[6] else "未新增解答"
                        if answer != "未新增解答":
                            results.append({"question": row[1], "answer": answer})
                        else:
                            results.append({"question": text, "answer": "找不到相關題目，請檢查是否有錯字"})
                        found = True
                        break
                if not found:
                    results.append({"question": text, "answer": "找不到相關題目，請檢查是否有錯字"})
            else:
                for row in csv_reader:
                    if row and text.lower() in row[1].lower():
                        answer = row[6] if row[6] else "未新增解答"
                        if answer != "未新增解答":
                            results.append({"question": row[1], "answer": answer})
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return [{"question": text, "answer": "找不到相關題目，請檢查是否有錯字"}]

    if not results:
        results.append({"question": text, "answer": "找不到相關題目，請檢查是否有錯字"})

    return results

def process_input(Q):
    """處理輸入查詢"""
    logger.debug(f"Processing input: {Q}")
    if Q.startswith("https://happyread.kh.edu.tw/"):
        if "id=" in Q:
            id_start = Q.index("id=") + 3
            id_value = Q[id_start:].split("&")[0]
            if validate_id(id_value):
                question_numbers = opencsv(id_value)
                if question_numbers:
                    results = search_in_book_all(question_numbers)
                    if not results or all(result["answer"] == "未新增解答" for result in results):
                        return [{"question": Q, "answer": "找不到相關題目，請檢查是否有錯字"}]
                    return results
                else:
                    return [{"question": Q, "answer": "找不到相關題目，請檢查是否有錯字"}]
            else:
                return [{"question": Q, "answer": "找不到相關題目，請檢查是否有錯字"}]
        else:
            return [{"question": Q, "answer": "找不到相關題目，請檢查是否有錯字"}]
    else:
        results = search(Q)
        return results

@app.route('/')
def index():
    return send_from_directory(static_dir, 'index.html')

@app.route('/script.js')
def serve_script():
    return send_from_directory(static_dir, 'script.js')

@app.route('/search', methods=['POST'])
def search_route():
    data = request.json
    question = data['question']
    results = process_input(question)
    return jsonify({'result': results})

@app.route('/lwopan_logo.png')
def serve_logo():
    return send_from_directory(static_dir, 'lwopan_logo.png')

@app.route('/404')
def not_found():
    return send_from_directory(static_dir, '404.html')

@app.route('/how_to_codeing')
def how_to_coding():
    return send_from_directory(static_dir, 'how_to_codeing.html')

@app.route('/<path:path>')
def catch_all(path):
    if os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    else:
        return send_from_directory(static_dir, '404.html'), 404

def main():
    parser = argparse.ArgumentParser(description='啟動 lwopan 服務器')
    parser.add_argument('--host', default='127.0.0.1', help='伺服器主機地址')
    parser.add_argument('--port', type=int, default=5000, help='伺服器端口')
    parser.add_argument('--delay', type=float, default=1.5, help='啟動瀏覽器前的延遲（秒）')
    parser.add_argument('--no-browser', action='store_true', help='不自動打開瀏覽器')
    parser.add_argument('--debug', action='store_true', help='啟用調試模式')

    args = parser.parse_args()

    if not args.debug and not args.no_browser:
        open_browser(args.host, args.port, args.delay)
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == '__main__':
    main()