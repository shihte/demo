from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
import csv
import traceback
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

@dataclass
class StudentInfo:
    seat_no: str
    account: str

@dataclass
class ClassInfo:
    class_no: str
    students: List[StudentInfo]
    student_count: int

class SchoolGradeCrawler:
    def __init__(self, url: str, default_values: Optional[Dict] = None, max_workers: int = 4):
        self.url = url
        self.default_values = default_values or {}
        self.results: List[ClassInfo] = []
        self.max_retries = 3
        self.current_progress: Dict[str, str] = {}
        self.max_workers = max_workers
        self.results_lock = threading.Lock()
        self.thread_local = threading.local()

    def get_driver(self) -> Tuple[webdriver.Chrome, WebDriverWait]:
        """獲取或創建線程本地的 WebDriver"""
        if not hasattr(self.thread_local, 'driver'):
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            self.thread_local.driver = webdriver.Chrome(options=options)
            self.thread_local.wait = WebDriverWait(self.thread_local.driver, 10)
        return self.thread_local.driver, self.thread_local.wait

    def select_option(self, element_name: str, prompt: str, default_value: str = "") -> Tuple[str, List[str]]:
        """選擇下拉選單選項"""
        driver, wait = self.get_driver()
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                select_element = wait.until(
                    EC.presence_of_element_located((By.NAME, element_name))
                )
                select = Select(select_element)
                options = [opt.get_attribute('value') for opt in select.options if opt.get_attribute('value')]
                filtered_options = [opt for opt in options if opt]  # 過濾掉 None 值
                
                value = default_value or self.default_values.get(element_name, '')
                if not value:
                    value = ''  # 確保返回空字符串而不是 None
                
                if value:
                    select.select_by_value(value)
                    if not self.default_values.get('silent', False):
                        print(f"已選擇 {prompt}: {value}")
                    sleep(1)
                
                return value, filtered_options

            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"選擇 {prompt} 失敗 (第 {attempt + 1} 次)。重試中...")
                    sleep(2)
                else:
                    print(f"無法選擇 {prompt}。錯誤: {str(e)}")
                    raise

    def setup_initial_page(self) -> List[str]:
        """設置初始頁面並返回班級列表"""
        driver, wait = self.get_driver()
        driver.get(self.url)
        sleep(2)

        # 選擇區域、學校、年級
        district_value, _ = self.select_option("district", "區域")
        school_value, _ = self.select_option("school", "學校")
        grade_value, _ = self.select_option("grade", "年級")

        self.current_progress = {
            'district': district_value,
            'school': school_value,
            'grade': grade_value
        }

        # 獲取班級列表
        select_element = wait.until(
            EC.presence_of_element_located((By.NAME, "classno"))
        )
        select = Select(select_element)
        class_options = [opt.get_attribute('value') for opt in select.options]
        filtered_options = [opt for opt in class_options if opt]  # 過濾掉 None 值
        return filtered_options

    def get_student_data(self) -> List[StudentInfo]:
        """獲取學生資料"""
        _, wait = self.get_driver()
        sleep(2)
        select_element = wait.until(
            EC.presence_of_element_located((By.NAME, "seatno"))
        )
        select = Select(select_element)
        students = []
        for option in select.options:
            value = option.get_attribute('value')
            if value:
                students.append(StudentInfo(
                    seat_no=value,
                    account=value
                ))
        return students

    def process_class(self, class_no: str) -> Optional[ClassInfo]:
        """處理單個班級的資料"""
        driver, wait = self.get_driver()
        class_number = str(int(class_no) + 1)
        
        for retry in range(self.max_retries):
            try:
                select_element = wait.until(
                    EC.presence_of_element_located((By.NAME, "classno"))
                )
                select = Select(select_element)
                select.select_by_value(class_number)
                sleep(2)

                student_data = self.get_student_data()
                if student_data:
                    class_info = ClassInfo(
                        class_no=class_number,
                        students=student_data,
                        student_count=len(student_data)
                    )
                    with self.results_lock:
                        self.results.append(class_info)
                    print(f"成功獲取班級 {class_number} 的數據，共 {len(student_data)} 筆學生資料")
                    return class_info
                else:
                    raise Exception("未獲取到學生資料")

            except Exception as e:
                if retry < self.max_retries - 1:
                    print(f"處理班級 {class_number} 失敗 (第 {retry + 1} 次)：{str(e)}")
                    driver.refresh()
                    sleep(2)
                else:
                    print(f"處理班級 {class_number} 最終失敗：{str(e)}")
                    return None
        return None

    def process_class_with_setup(self, class_no: str) -> Optional[ClassInfo]:
        """設置頁面並處理班級"""
        try:
            driver, _ = self.get_driver()
            driver.get(self.url)
            sleep(2)

            # 恢復當前進度
            for field, value in self.current_progress.items():
                self.select_option(field, field.capitalize(), value)
                sleep(1)

            return self.process_class(class_no)
        except Exception as e:
            print(f"處理班級 {class_no} 時發生錯誤: {str(e)}")
            return None
        finally:
            driver, _ = self.get_driver()
            driver.quit()

    def get_class_count(self) -> Tuple[List[str], int]:
        """獲取班級數量"""
        driver, wait = self.get_driver()
        try:
            driver.get(self.url)
            sleep(2)

            # 選擇區域、學校、年級
            district_value, _ = self.select_option("district", "區域")
            school_value, _ = self.select_option("school", "學校")
            grade_value, _ = self.select_option("grade", "年級")

            self.current_progress = {
                'district': district_value,
                'school': school_value,
                'grade': grade_value
            }

            # 獲取班級列表
            select_element = wait.until(
                EC.presence_of_element_located((By.NAME, "classno"))
            )
            select = Select(select_element)
            class_options = [opt.get_attribute('value') for opt in select.options]
            filtered_options = [opt for opt in class_options if opt]
            
            print(f"\n檢測到 {len(filtered_options)} 個班級")
            user_input = input("請確認是否繼續爬取？(y/n): ").strip().lower()
            
            if user_input != 'y':
                print("用户取消爬取")
                return [], 0
                
            return filtered_options, len(filtered_options)
        except Exception as e:
            print(f"獲取班級數量時發生錯誤: {str(e)}")
            return [], 0
        finally:
            driver.quit()

    def crawl_grade(self) -> None:
        """使用多線程爬取年級資料"""
        try:
            class_options, total_classes = self.get_class_count()
            if total_classes == 0:
                return

            print(f"\n開始爬取所有班級數據，共 {total_classes} 個班級...")

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self.process_class_with_setup, class_no) 
                          for class_no in class_options]
                
                completed = 0
                for future in futures:
                    future.result()  # 等待任務完成
                    completed += 1
                    print(f"進度: {completed}/{total_classes} ({(completed/total_classes*100):.2f}%)")

            self.save_to_csv()

        except Exception as e:
            print(f"爬取過程發生錯誤: {str(e)}")
            print("詳細錯誤信息:")
            print(traceback.format_exc())
            raise

    def save_to_csv(self, filename: str = "openID.csv") -> None:
        """保存數據到CSV文件"""
        if not self.results:
            print("沒有數據可以保存")
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                fieldnames = ['班級人數', '班級', '帳號']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for class_info in self.results:
                    for student in class_info.students:
                        writer.writerow({
                            '班級人數': class_info.student_count,
                            '班級': class_info.class_no,
                            '帳號': student.account
                        })
            
            print(f"數據已保存到 {filename}")

        except Exception as e:
            print(f"保存CSV文件時發生錯誤: {str(e)}")

    def run(self) -> None:
        """執行爬蟲程序"""
        try:
            self.crawl_grade()
        except Exception as e:
            print(f"執行過程中發生錯誤: {str(e)}")
            print("詳細錯誤信息:")
            print(traceback.format_exc())

def main():
    default_values = {
        "district": "802",    # 預設區域
        "school": "wfjh",     # 預設學校
        "grade": "8",         # 預設年級
        "silent": True        # 是否靜默模式
    }

    default_url = "https://kh.sso.edu.tw/auth-server-stlogin?Auth_Request_RedirectUri=https%253A%252F%252Foidc.tanet.edu.tw%252Fcncreturnpage&Auth_Request_State=a1h8GqiVsrDoNh4wHfqx3IIcWZbx0JrRRDGpc8cGzRk&Auth_Request_Response_Type=code&Auth_Request_Client_ID=cf789350df91c914eede027ce55f3ab5&Auth_Request_Nonce=bKyFuJbbQXulFBTlu3yv5o16-UOKzp4QaK7gfId4Op0&Auth_Request_Scope=openid+exchangedata&local=true"
    
    url = input("輸入URL (直接按Enter使用預設URL): ").strip() or default_url
    max_workers = int(input("輸入最大線程數 (直接按Enter使用預設值4): ").strip() or "4")
    
    crawler = SchoolGradeCrawler(url, default_values, max_workers=max_workers)
    crawler.run()

if __name__ == "__main__":
    main()