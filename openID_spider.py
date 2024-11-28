from time import sleep 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
import csv
import traceback

class SchoolGradeCrawler:
    def __init__(self, url, default_values=None):
        self.url = url
        self.default_values = default_values or {}
        self.driver = None
        self.results = []
        self.wait = None
        self.max_retries = 3
        self.current_progress = None

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def select_option(self, element_name, prompt, default_value=""):
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                select_element = self.wait.until(
                    EC.presence_of_element_located((By.NAME, element_name))
                )
                select = Select(select_element)
                options = [opt for opt in select.options if opt.get_attribute('value')]
                
                value = default_value or self.default_values.get(element_name)
                
                if value:
                    select.select_by_value(value)
                    if not self.default_values.get('silent', False):
                        print(f"已選擇 {prompt}: {value}")
                    sleep(1)
                    return value, [opt.get_attribute('value') for opt in options]
                
                return None, None

            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"選擇 {prompt} 失敗 (第 {attempt + 1} 次)。重試中...")
                    sleep(2)
                else:
                    print(f"無法選擇 {prompt}。錯誤: {str(e)}")
                    raise

    def restart_browser(self):
        try:
            if self.driver:
                self.driver.quit()
            
            self.setup_driver()
            self.driver.get(self.url)
            sleep(2)

            if self.current_progress:
                self.select_option("district", "區域", self.current_progress['district'])
                sleep(1)
                self.select_option("school", "學校", self.current_progress['school'])
                sleep(1)
                self.select_option("grade", "年級", self.current_progress['grade'])
                sleep(1)
            
            return True
        except Exception as e:
            print(f"重啟瀏覽器失敗: {str(e)}")
            return False

    def get_student_data(self):
        try:
            sleep(2)
            select_element = self.wait.until(
                EC.presence_of_element_located((By.NAME, "seatno"))
            )
            select = Select(select_element)
            students = []
            for option in select.options:
                if option.get_attribute('value'):
                    students.append({
                        'seat_no': option.get_attribute('value'),
                        'account': option.get_attribute('value')
                    })
            return students
        except Exception as e:
            print(f"獲取學生資料時發生錯誤: {str(e)}")
            return None

    def process_class(self, class_no):
        class_no = str(int(class_no) + 1)
        
        for retry in range(self.max_retries):
            try:
                select_element = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "classno"))
                )
                select = Select(select_element)
                select.select_by_value(class_no)
                sleep(2)

                student_data = self.get_student_data()
                if student_data:
                    class_info = {
                        "class": class_no,
                        "students": student_data,
                        "student_count": len(student_data)
                    }
                    self.results.append(class_info)
                    print(f"成功獲取班級 {class_no} 的數據，共 {len(student_data)} 筆學生資料")
                    return True
                else:
                    raise Exception("未獲取到學生資料")

            except Exception as e:
                if retry < self.max_retries - 1:
                    print(f"處理班級 {class_no} 失敗 (第 {retry + 1} 次)：{str(e)}")
                    print("嘗試重啟瀏覽器...")
                    if self.restart_browser():
                        continue
                else:
                    print(f"處理班級 {class_no} 最終失敗：{str(e)}")
                    return False

    def crawl_grade(self):
        try:
            district_value, _ = self.select_option("district", "區域")
            school_value, _ = self.select_option("school", "學校")
            grade_value, _ = self.select_option("grade", "年級")
            
            self.current_progress = {
                'district': district_value,
                'school': school_value,
                'grade': grade_value
            }

            select_element = self.wait.until(
                EC.presence_of_element_located((By.NAME, "classno"))
            )
            select = Select(select_element)
            class_options = [opt.get_attribute('value') for opt in select.options if opt.get_attribute('value')]

            print(f"\n開始爬取 {grade_value} 年級的所有班級數據...")

            for class_no in class_options:
                self.process_class(class_no)
                self.save_to_csv()
                sleep(1)

        except Exception as e:
            print(f"爬取過程發生錯誤: {str(e)}")
            print("詳細錯誤信息:")
            print(traceback.format_exc())
            raise

    def save_to_csv(self, filename="openID.csv"):
        if not self.results:
            print("沒有數據可以保存")
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                fieldnames = ['班級人數', '班級', '帳號']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for class_info in self.results:
                    for student in class_info['students']:
                        row = {
                            '班級人數': class_info['student_count'],
                            '班級': class_info['class'],
                            '帳號': student['account']
                        }
                        writer.writerow(row)
            
            print(f"數據已保存到 {filename}")

        except Exception as e:
            print(f"保存CSV文件時發生錯誤: {str(e)}")

    def run(self):
        try:
            self.setup_driver()
            self.driver.get(self.url)
            self.crawl_grade()

        except Exception as e:
            print(f"執行過程中發生錯誤: {str(e)}")
            print("詳細錯誤信息:")
            print(traceback.format_exc())
        finally:
            if self.driver:
                self.driver.quit()

def main():
    default_values = {
        "district": "802",    # 預設區域
        "school": "wfjh",     # 預設學校
        "grade": "8",         # 預設年級
        "silent": True        # 是否靜默模式
    }

    default_url = "https://kh.sso.edu.tw/auth-server-stlogin?Auth_Request_RedirectUri=https%253A%252F%252Foidc.tanet.edu.tw%252Fcncreturnpage&Auth_Request_State=a1h8GqiVsrDoNh4wHfqx3IIcWZbx0JrRRDGpc8cGzRk&Auth_Request_Response_Type=code&Auth_Request_Client_ID=cf789350df91c914eede027ce55f3ab5&Auth_Request_Nonce=bKyFuJbbQXulFBTlu3yv5o16-UOKzp4QaK7gfId4Op0&Auth_Request_Scope=openid+exchangedata&local=true"
    
    url = input("輸入URL (直接按Enter使用預設URL): ") or default_url
    
    crawler = SchoolGradeCrawler(url, default_values)
    crawler.run()

if __name__ == "__main__":
    main()