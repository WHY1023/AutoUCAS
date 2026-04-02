import requests
import time
import datetime
import random
import urllib3
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import tkinter.font as tkfont

# 禁用未验证 HTTPS 请求的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UCASAutoSignerApp:
    LEGACY_SESSION_ID = "220B4BF64B92633F236393F811A8586A"
    DEFAULT_VERIFY_URL = "http://iclass.ucas.edu.cn:88/ve/webservices/mobileCheck.shtml?method=mobileLogin&username=${0}&password=${1}&lx=${2}"
    
    BASE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Referer": "https://servicewechat.com/wxdd3bd7d4acf54723/56/page-frame.html"
    }

    # 配色方案
    COLOR_BG = "#f4f7f6"
    COLOR_FG = "#333333"
    COLOR_SUBTILE = "#7f8c8d"
    COLOR_LOG_BG = "#ffffff"
    COLOR_PRIMARY = "#3498db"
    COLOR_SUCCESS = "#2ecc71"
    COLOR_DANGER = "#e74c3c"

    def __init__(self, root):
        self.root = root
        self.root.title("IWP - 课程助手")
        self.root.geometry("620x580") # 稍微调高了一点点窗口以适应多出的文字
        self.root.minsize(580, 540)
        self.root.configure(bg=self.COLOR_BG)
        
        self.uid = None
        self.session_id = self.LEGACY_SESSION_ID
        self.time_delta = 0 
        self.session = requests.Session()
        self.session.verify = False 
        self.stop_event = threading.Event()

        self.setup_ui()

    def setup_ui(self):
        self.style = ttk.Style()
        self.style.theme_use('clam') 
        
        self.style.configure("TFrame", background=self.COLOR_BG)
        self.style.configure("TLabelframe", background=self.COLOR_BG, foreground=self.COLOR_FG, font=("Microsoft YaHei", 9, "bold"))
        self.style.configure("TLabelframe.Label", background=self.COLOR_BG, foreground=self.COLOR_FG)

        self.style.configure("TLabel", background=self.COLOR_BG, foreground=self.COLOR_FG, font=("Microsoft YaHei", 9))
        self.style.configure("Subtitle.TLabel", foreground=self.COLOR_SUBTILE, font=("Microsoft YaHei", 8))
        self.style.configure("TEntry", fieldbackground="white", font=("Consolas", 10))

        self.style.configure("TButton", font=("Microsoft YaHei", 9), borderwidth=0, focuscolor=self.COLOR_BG)
        self.style.map("TButton", background=[('pressed', '#dddddd'), ('active', '#eeeeee')])

        self.style.configure("Start.TButton", foreground="white", background=self.COLOR_SUCCESS, font=("Microsoft YaHei", 9, "bold"))
        self.style.map("Start.TButton", background=[('pressed', '#27ae60'), ('active', '#2fdf78'), ('disabled', '#bdc3c7')])

        self.style.configure("Stop.TButton", foreground="white", background=self.COLOR_DANGER, font=("Microsoft YaHei", 9, "bold"))
        self.style.map("Stop.TButton", background=[('pressed', '#c0392b'), ('active', '#e85a4a'), ('disabled', '#bdc3c7')])

        main_frame = ttk.Frame(self.root, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 1. 标题区 ---
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        self.title_font = tkfont.Font(family="Helvetica Neue", size=18, weight="bold")
        w_I_space = self.title_font.measure("I ")
        w_W = self.title_font.measure("W")
        w_dyn1_work = self.title_font.measure("ork for ")
        w_dyn1_want = self.title_font.measure("ant to ")
        max_dyn1 = max(w_dyn1_work, w_dyn1_want)
        w_P = self.title_font.measure("P")
        w_dyn2_prog = self.title_font.measure("rogress")
        w_dyn2_play = self.title_font.measure("lay")
        max_dyn2 = max(w_dyn2_prog, w_dyn2_play)
        
        total_w = w_I_space + w_W + max_dyn1 + w_P + max_dyn2
        canvas_w = 400
        canvas_h = 40
        start_x = (canvas_w - total_w) // 2
        
        self.title_canvas = tk.Canvas(header_frame, width=canvas_w, height=canvas_h, bg=self.COLOR_BG, highlightthickness=0)
        self.title_canvas.pack()
        
        y_pos = canvas_h // 2
        
        self.title_canvas.create_text(start_x, y_pos, text="I ", font=self.title_font, fill=self.COLOR_PRIMARY, anchor=tk.W)
        x_W = start_x + w_I_space
        self.title_canvas.create_text(x_W, y_pos, text="W", font=self.title_font, fill=self.COLOR_PRIMARY, anchor=tk.W)
        x_dyn1 = x_W + w_W
        self.item_dyn1 = self.title_canvas.create_text(x_dyn1, y_pos, text="ork for ", font=self.title_font, fill=self.COLOR_PRIMARY, anchor=tk.W)
        x_P = x_dyn1 + max_dyn1
        self.title_canvas.create_text(x_P, y_pos, text="P", font=self.title_font, fill=self.COLOR_PRIMARY, anchor=tk.W)
        x_dyn2 = x_P + w_P
        self.item_dyn2 = self.title_canvas.create_text(x_dyn2, y_pos, text="rogress", font=self.title_font, fill=self.COLOR_PRIMARY, anchor=tk.W)

        subtitle_label = ttk.Label(header_frame, text="仅供学习使用", style="Subtitle.TLabel")
        subtitle_label.pack(pady=(2, 0))

        self.anim_state = 0
        self.root.after(2500, lambda: self.animate_title_step(0, "out"))

        # --- 2. 账号设置区 ---
        account_frame = ttk.LabelFrame(main_frame, text=" 身份认证 ", padding="15")
        account_frame.pack(fill=tk.X, pady=5)

        ttk.Label(account_frame, text="学号:").grid(row=0, column=0, padx=(0, 10), pady=8, sticky=tk.W)
        self.phone_var = tk.StringVar()
        phone_entry = ttk.Entry(account_frame, textvariable=self.phone_var, width=22)
        phone_entry.grid(row=0, column=1, pady=8, sticky=tk.W)
        phone_entry.focus_set()

        ttk.Label(account_frame, text="密码:").grid(row=0, column=2, padx=(20, 10), pady=8, sticky=tk.W)
        self.pwd_var = tk.StringVar(value="Ucas@2025")
        ttk.Entry(account_frame, textvariable=self.pwd_var, width=22).grid(row=0, column=3, pady=8, sticky=tk.W)

        # --- 3. 参数与控制区 (使用纵向排版适应注释文字) ---
        control_panel_frame = ttk.Frame(main_frame)
        control_panel_frame.pack(fill=tk.X, pady=10)

        # 左侧：参数设置区
        settings_frame = ttk.Frame(control_panel_frame)
        settings_frame.pack(side=tk.LEFT)

        # 提前签到模块
        ttk.Label(settings_frame, text="提前 (分):").grid(row=0, column=0, sticky=tk.W)
        self.ahead_var = tk.IntVar(value=20)
        ttk.Entry(settings_frame, textvariable=self.ahead_var, width=6).grid(row=0, column=1, padx=(5, 10), sticky=tk.W)
        ttk.Label(settings_frame, text="课堂开始前多久签到，建议10-20分钟", style="Subtitle.TLabel").grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))

        # 刷新间隔模块
        ttk.Label(settings_frame, text="刷新 (分):").grid(row=2, column=0, sticky=tk.W)
        self.refresh_var = tk.IntVar(value=30)
        ttk.Entry(settings_frame, textvariable=self.refresh_var, width=6).grid(row=2, column=1, padx=(5, 10), sticky=tk.W)
        ttk.Label(settings_frame, text="多久刷新一次课表，建议小于提前签到时间", style="Subtitle.TLabel").grid(row=3, column=0, columnspan=2, sticky=tk.W)

        # 右侧：按钮区 (垂直居中对齐)
        btns_frame = ttk.Frame(control_panel_frame)
        btns_frame.pack(side=tk.RIGHT, anchor=tk.CENTER)

        self.btn_check = ttk.Button(btns_frame, text="单次检查", command=self.on_check_clicked, width=10)
        self.btn_check.pack(side=tk.LEFT, padx=5)

        self.btn_start = ttk.Button(btns_frame, text="▶ 启动挂机", command=self.on_start_clicked, style="Start.TButton", width=12)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ttk.Button(btns_frame, text="⏹ 停止", command=self.on_stop_clicked, style="Stop.TButton", state=tk.DISABLED, width=8)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        # --- 4. 日志输出区 ---
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        ttk.Label(log_frame, text="运行日志", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 5))

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, 
                                                 font=("Consolas", 9), bg=self.COLOR_LOG_BG, fg=self.COLOR_FG,
                                                 relief="flat", highlightbackground="#e0e0e0", highlightthickness=1)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state='disabled')
        
        self.log_area.tag_config("SUCCESS", foreground=self.COLOR_SUCCESS)
        self.log_area.tag_config("DANGER", foreground=self.COLOR_DANGER)
        self.log_area.tag_config("WARNING", foreground="#f39c12")
        self.log_area.tag_config("TIME", foreground="#95a5a6")

        self.log("系统初始化完成。")

    # ==========================================
    # 动画与色彩计算逻辑
    # ==========================================
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def interpolate_color(self, c1, c2, alpha):
        rgb1 = self.hex_to_rgb(c1)
        rgb2 = self.hex_to_rgb(c2)
        r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * alpha)
        g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * alpha)
        b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * alpha)
        return self.rgb_to_hex((r, g, b))

    def animate_title_step(self, step=0, direction="out"):
        steps = 20
        if direction == "out":
            alpha = 1.0 - (step / steps)
        else:
            alpha = (step / steps)
            
        current_color = self.interpolate_color(self.COLOR_BG, self.COLOR_PRIMARY, alpha)
        self.title_canvas.itemconfig(self.item_dyn1, fill=current_color)
        self.title_canvas.itemconfig(self.item_dyn2, fill=current_color)
        
        if step < steps:
            self.root.after(40, lambda: self.animate_title_step(step+1, direction))
        else:
            if direction == "out":
                self.anim_state = (self.anim_state + 1) % 2
                if self.anim_state == 0:
                    self.title_canvas.itemconfig(self.item_dyn1, text="ork for ")
                    self.title_canvas.itemconfig(self.item_dyn2, text="rogress")
                else:
                    self.title_canvas.itemconfig(self.item_dyn1, text="ant to ")
                    self.title_canvas.itemconfig(self.item_dyn2, text="lay")
                
                self.root.after(1000, lambda: self.animate_title_step(0, "in"))
            else:
                self.root.after(3000, lambda: self.animate_title_step(0, "out"))

    # ==========================================
    # 日志与网络逻辑
    # ==========================================
    def log(self, msg, level="INFO"):
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        tag = None
        clean_msg = msg
        if msg.startswith("✅") or "成功" in msg:
            tag = "SUCCESS"
        elif msg.startswith("❌") or "失败" in msg:
            tag = "DANGER"
        elif msg.startswith("⚠️") or "过期" in msg:
            tag = "WARNING"
        elif msg.startswith("🚀") or msg.startswith("🛑") or msg.startswith("⏳"):
            clean_msg = " " + msg 

        def append():
            self.log_area.configure(state='normal')
            self.log_area.insert(tk.END, f"[{current_time}] ", "TIME")
            if tag:
                self.log_area.insert(tk.END, f"{clean_msg}\n", tag)
            else:
                self.log_area.insert(tk.END, f"{clean_msg}\n")
            self.log_area.see(tk.END)
            self.log_area.configure(state='disabled')
        self.root.after(0, append)

    def login(self):
        phone = self.phone_var.get().strip()
        pwd = self.pwd_var.get().strip()
        
        if not phone or not pwd:
            self.log("⚠️ 请先填写学号！")
            return False

        url = "https://iclass.ucas.edu.cn:8181/app/user/login.action"
        payload = {"phone": phone, "password": pwd, "userLevel": "1", "verificationType": "1", "verificationUrl": self.DEFAULT_VERIFY_URL}
        
        headers = self.BASE_HEADERS.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["sessionId"] = self.session_id

        self.log("正在尝试登录...")
        try:
            resp = self.session.post(url, data=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
            if "result" not in data or "id" not in data["result"]:
                self.log("❌ 登录失败，请检查账号。")
                return False
                
            self.uid = data["result"]["id"]
            self.session_id = data["result"].get("sessionId", self.LEGACY_SESSION_ID)
            self.log(f"✅ 登录成功！欢迎, {data['result'].get('userName', '未知用户')}")
            return True
        except Exception as e:
            self.log(f"❌ 登录请求发生错误: {e}")
            return False

    def get_today_courses(self):
        url = "https://iclass.ucas.edu.cn:8181/app/course/get_stu_course_sched.action"
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        payload = {"id": self.uid, "dateStr": date_str}
        
        headers = self.BASE_HEADERS.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["sessionId"] = self.session_id
        
        try:
            resp = self.session.post(url, data=payload, headers=headers)
            if resp.status_code == 401:
                self.log("⚠️ 会话已过期，准备重新登录...")
                return None
            resp.raise_for_status()
            
            server_date_str = resp.headers.get("Date")
            if server_date_str:
                server_time = datetime.datetime.strptime(server_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                local_time = datetime.datetime.utcnow()
                self.time_delta = (server_time - local_time).total_seconds()
            
            data = resp.json()
            return data.get("result", [])
        except Exception as e:
            self.log(f"⚠️ 获取课表失败: {e}")
            return []

    def sign_course(self, time_table_id, course_name):
        url = "https://iclass.ucas.edu.cn:8181/app/course/stu_scan_sign.action"
        client_now = int(time.time() * 1000)
        server_now = client_now + int(self.time_delta * 1000)
        timestamp = server_now - random.randint(1000, 3000)
        
        params = {"id": self.uid, "timeTableId": time_table_id, "timestamp": timestamp}
        headers = self.BASE_HEADERS.copy()
        headers["sessionId"] = self.session_id
        
        try:
            resp = self.session.get(url, params=params, headers=headers)
            resp.raise_for_status()
            self.log(f"🎯 [{course_name}] 签到成功！")
            return True
        except Exception as e:
            self.log(f"❌ [{course_name}] 签到失败: {e}")
            return False

    def check_and_sign_once(self):
        try:
            ahead_mins = self.ahead_var.get()
        except tk.TclError:
            self.log("⚠️ 提前时间必须是整数！")
            return

        courses = self.get_today_courses()
        if courses is None:
            if self.login():
                courses = self.get_today_courses()
            else:
                return

        if not courses:
            self.log("今日暂无课程或拉取失败。")
            return

        self.log(f"刷新成功：今日共 {len(courses)} 门课程。")
        server_now_ms = int(time.time() * 1000) + int(self.time_delta * 1000)
        sign_ahead_ms = ahead_mins * 60 * 1000
        
        for course in courses:
            course_name = course.get("courseName", "未知课程")
            status = str(course.get("signStatus", "0"))
            time_table_id = course.get("uuid") or course.get("id")
            
            if status == "1":
                continue 
            if not time_table_id:
                continue
                
            begin_time_str = course.get("classBeginTime", "")
            end_time_str = course.get("classEndTime", "")
            
            if len(begin_time_str) <= 8:
                today_prefix = datetime.datetime.now().strftime("%Y-%m-%d")
                begin_time_str = f"{today_prefix} {begin_time_str}"
                end_time_str = f"{today_prefix} {end_time_str}"
                
            try:
                begin_time_ms = int(datetime.datetime.strptime(begin_time_str, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
                end_time_ms = int(datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
            except ValueError:
                continue
                
            if (server_now_ms >= (begin_time_ms - sign_ahead_ms)) and (server_now_ms <= end_time_ms):
                self.log(f"⏳ 触发自动签到: [{course_name}]")
                self.sign_course(time_table_id, course_name)
                time.sleep(2)

    def _daemon_worker(self):
        try:
            refresh_interval = self.refresh_var.get()
        except tk.TclError:
            self.log("⚠️ 刷新间隔必须是整数！")
            self.root.after(0, self.on_stop_clicked)
            return

        self.log("🚀 守护进程已启动，后台挂机中...")
        while not self.stop_event.is_set():
            self.check_and_sign_once()
            if self.stop_event.wait(timeout=refresh_interval * 60):
                break
        self.log("🛑 守护进程已安全停止。")

    def on_check_clicked(self):
        if not self.uid:
            threading.Thread(target=self._silent_login_and_check, daemon=True).start()
        else:
            threading.Thread(target=self.check_and_sign_once, daemon=True).start()

    def _silent_login_and_check(self):
        if self.login():
            self.check_and_sign_once()

    def on_start_clicked(self):
        if not self.phone_var.get():
            self.log("⚠️ 请填写学号！")
            return
            
        self.btn_start.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self.btn_check.configure(state=tk.DISABLED)
        
        self.stop_event.clear()
        thread = threading.Thread(target=self._daemon_daemon_launcher)
        thread.daemon = True
        thread.start()

    def _daemon_daemon_launcher(self):
        if not self.uid:
            if not self.login():
                self.root.after(0, self.on_stop_clicked) 
                return
        self._daemon_worker()

    def on_stop_clicked(self):
        self.stop_event.set()
        self.btn_start.configure(state=tk.NORMAL)
        self.btn_check.configure(state=tk.NORMAL)
        self.btn_stop.configure(state=tk.DISABLED)

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    root = tk.Tk()
    app = UCASAutoSignerApp(root)
    root.mainloop()