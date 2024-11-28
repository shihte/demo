from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import csv
import os
import webbrowser
import threading
import time
import logging
import sys
import traceback
import signal
import requests
from werkzeug.serving import make_server

# 設置日誌
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LwopanServer:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.server = None
        self.server_thread = None
        self.is_running = False
        # 添加基礎路徑ａａａａ
        self.base_path = self.get_base_path()
        # 設置路由
        self.setup_routes()

    def setup_routes(self):
        """設置所有路由"""
        @self.app.route('/')
        def index():
            return send_from_directory('.', 'index.html')

        @self.app.route('/script.js')
        def serve_script():
            return send_from_directory('.', 'script.js')

        @self.app.route('/search', methods=['POST'])
        def search_route():
            data = request.json
            question = data.get('question', '')
            results = self.process_input(question)
            return jsonify({'result': results})

        @self.app.route('/lwopan_logo.png')
        def serve_logo():
            return send_from_directory('.', 'lwopan_logo.png')

        @self.app.route('/404')
        def not_found():
            return send_from_directory('.', '404.html')

        @self.app.route('/how_to_codeing')
        def how_to_coding():
            return send_from_directory('.', 'how_to_codeing.html')

        @self.app.route('/<path:path>')
        def catch_all(path):
            if os.path.exists(path):
                return send_from_directory('.', path)
            else:
                return send_from_directory('.', '404.html'), 404

    def get_base_path(self):
        """獲取基礎路徑"""
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.abspath(os.path.dirname(__file__))

    def get_file_path(self, relative_path):
        """獲取文件的完整路徑"""
        return os.path.join(self.base_path, relative_path)

    def validate_id(self, id_str):
        """驗證ID是否有效"""
        try:
            id_num = int(id_str)
            return 1 <= id_num <= 184
        except ValueError:
            return False

    def opencsv(self, ID):
        """打開並讀取指定ID的CSV文件"""
        try:
            file_path = self.get_file_path(os.path.join('happyread', f"Book_{ID}.csv"))
            logger.info(f"Attempting to open file: {file_path}")

            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return []

            with open(file_path, "r", newline="", encoding="utf-8") as open_XID_csv:
                csv_reader = csv.reader(open_XID_csv)
                first_column = [row[0] for row in csv_reader]
                return first_column[1:]
        except Exception as e:
            logger.error(f"Error opening CSV {file_path}: {str(e)}")
            return []

    def search_in_book_all(self, question_numbers):
        """在book_all.csv中搜索問題編號"""
        results = []
        file_path = self.get_file_path(os.path.join('happyread', "book_all.csv"))
        logger.info(f"Searching in file: {file_path}")

        try:
            if not os.path.exists(file_path):
                logger.error(f"Book_all.csv not found: {file_path}")
                return [{"question": "錯誤", "answer": "數據文件不存在"}]

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
                        results.append({
                            "question": f"題號 {number}",
                            "answer": "找不到相關題目，請檢查是否有錯字"
                        })
        except Exception as e:
            logger.error(f"Error searching book_all: {str(e)}")
            return [{"question": "錯誤", "answer": f"讀取文件錯誤: {str(e)}"}]
        return results

    def search(self, text):
        """搜索指定文本"""
        results = []
        file_path = self.get_file_path(os.path.join('happyread', "book_all.csv"))
        logger.info(f"Searching text in file: {file_path}")

        try:
            if not os.path.exists(file_path):
                logger.error(f"Book_all.csv not found at: {file_path}")
                return [{"question": text, "answer": "數據文件不存在"}]

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
                                results.append({
                                    "question": text,
                                    "answer": "找不到相關題目，請檢查是否有錯字"
                                })
                            found = True
                            break
                    if not found:
                        results.append({
                            "question": text,
                            "answer": "找不到相關題目，請檢查是否有錯字"
                        })
                else:
                    for row in csv_reader:
                        if row and text.lower() in row[1].lower():
                            answer = row[6] if row[6] else "未新增解答"
                            if answer != "未新增解答":
                                results.append({"question": row[1], "answer": answer})
        except Exception as e:
            logger.error(f"Error searching text: {str(e)}")
            return [{"question": text, "answer": f"讀取文件錯誤: {str(e)}"}]

        if not results:
            results.append({
                "question": text,
                "answer": "找不到相關題目，請檢查是否有錯字"
            })
        return results

    def process_input(self, Q):
        """處理輸入查詢"""
        if Q.startswith("https://happyread.kh.edu.tw/"):
            if "id=" in Q:
                id_start = Q.index("id=") + 3
                id_value = Q[id_start:].split("&")[0]
                if self.validate_id(id_value):
                    question_numbers = self.opencsv(id_value)
                    if question_numbers:
                        results = self.search_in_book_all(question_numbers)
                        if not results or all(result["answer"] == "未新增解答" 
                                           for result in results):
                            return [{"question": Q, 
                                   "answer": "找不到相關題目，請檢查是否有錯字"}]
                        return results
            return [{"question": Q, "answer": "找不到相關題目，請檢查是否有錯字"}]
        else:
            return self.search(Q)

    def run_server_thread(self, host, port):
        """在線程中運行服務器"""
        self.server = make_server(host, port, self.app)
        self.is_running = True
        self.server.serve_forever()

    def start_server(self, host='127.0.0.1', port=5000):
        """啟動服務器"""
        if not self.is_running:
            self.server_thread = threading.Thread(
                target=self.run_server_thread,
                args=(host, port)
            )
            self.server_thread.daemon = True
            self.server_thread.start()
            time.sleep(1)
            logger.info(f"Server started at http://{host}:{port}")
            return True
        return False

    def stop_server(self):
        """停止服務器"""
        if self.is_running and self.server:
            self.is_running = False
            self.server.shutdown()
            self.server = None
            if self.server_thread:
                self.server_thread.join(timeout=1)
            logger.info("Server stopped")
            return True
        return False

def main():
    try:
        server = LwopanServer()
        if server.start_server():
            logger.info("Server started successfully")
            # 打開瀏覽器
            webbrowser.open('http://127.0.0.1:5000')
            
            # 等待用戶按 Ctrl+C 停止服務器
            def signal_handler(sig, frame):
                logger.info("Stopping server...")
                server.stop_server()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.pause()
            
    except Exception as e:
        # 保存錯誤信息到文件
        with open('error_log.txt', 'w') as f:
            f.write(f"Error: {str(e)}\n")
            f.write(traceback.format_exc())
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 保存錯誤信息到文件
        with open('error_log.txt', 'w') as f:
            f.write(f"Critical Error: {str(e)}\n")
            f.write(traceback.format_exc())
        sys.exit(1)