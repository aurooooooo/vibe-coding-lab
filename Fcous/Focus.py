import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import datetime
import calendar

# --- 常量定义 ---
CONFIG_FILE_NAME = "todo_config.json"
DATA_FILE_NAME = "todo_data.json"
DEFAULT_FONT_SIZE = 14
DEFAULT_OPACITY = 0.98
# 窗口初始尺寸
INIT_W, INIT_H = 400, 500
MIN_WIDTH, MIN_HEIGHT = 350, 450

# --- 配色系统 ---
THEMES = {
    "dark": {
        "bg": "#09090B", "fg": "#E4E4E7",
        "input_bg": "#18181B", "input_fg": "#FAFAFA",
        "accent": "#F97316", "accent_hover": "#EA580C",
        "hover": "#27272A", "sub_text": "#71717A",
        "cal_bg": "#18181B", "cal_today": "#F97316",
        "border": "#3F3F46",
        "checkbox_border": "#71717A", "checkbox_fill": "#F97316"
    },
    "light": {
        "bg": "#FAFAFA", "fg": "#18181B",
        "input_bg": "#FFFFFF", "input_fg": "#000000",
        "accent": "#EA580C", "accent_hover": "#C2410C",
        "hover": "#F4F4F5", "sub_text": "#A1A1AA",
        "cal_bg": "#FFFFFF", "cal_today": "#EA580C",
        "border": "#A1A1AA",
        "checkbox_border": "#71717A", "checkbox_fill": "#EA580C"
    }
}


class ModernTodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus")

        # 窗口状态
        self.settings_win = None
        self.calendar_win = None

        # 加载配置
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_path, CONFIG_FILE_NAME)
        self.config = self.load_config()

        # 应用参数
        self.font_size = self.config.get("font_size", DEFAULT_FONT_SIZE)
        self.is_topmost = self.config.get("is_topmost", False)
        self.theme_mode = self.config.get("theme", "dark")
        self.data_dir = self.config.get("data_dir", self.base_path)
        self.opacity = self.config.get("opacity", DEFAULT_OPACITY)

        if not os.path.exists(self.data_dir):
            self.data_dir = self.base_path

        self.current_date = datetime.date.today()
        self.tasks_data = self.load_tasks_data()

        # 初始化窗口
        self.root.geometry(f"{INIT_W}x{INIT_H}+1400+100")
        self.root.overrideredirect(True)
        self.colors = THEMES[self.theme_mode]

        self.root.configure(bg=self.colors['bg'])
        self.root.attributes('-alpha', self.opacity)
        self.root.attributes('-topmost', self.is_topmost)

        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        self.update_fonts()
        self.setup_ui()
        self.render_tasks()

    # --- 核心配置 ---
    def load_config(self):
        default_config = {
            "font_size": DEFAULT_FONT_SIZE, "is_topmost": False,
            "theme": "dark", "data_dir": self.base_path,
            "opacity": DEFAULT_OPACITY
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    default_config.update(json.load(f))
            except:
                pass
        return default_config

    def save_config(self):
        self.config.update({
            "font_size": self.font_size, "is_topmost": self.is_topmost,
            "theme": self.theme_mode, "data_dir": self.data_dir,
            "opacity": self.opacity
        })
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except:
            pass

    def load_tasks_data(self):
        data_path = os.path.join(self.data_dir, DATA_FILE_NAME)
        if os.path.exists(data_path):
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_tasks_data(self):
        data_path = os.path.join(self.data_dir, DATA_FILE_NAME)
        try:
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(self.tasks_data, f, ensure_ascii=False)
        except:
            pass

    def update_fonts(self):
        self.font_main = ("Segoe UI", self.font_size)
        self.font_bold = ("Segoe UI", self.font_size, "bold")
        self.font_title = ("Segoe UI", self.font_size + 8, "bold")
        self.font_icon = ("Arial", 16)
        self.font_ui_small = ("Segoe UI", int(self.font_size * 0.85))
        self.font_ui_bold = ("Segoe UI", int(self.font_size * 0.85), "bold")
        # 日历专用字体 - 跟随主字号
        self.font_cal_header = ("Segoe UI", int(self.font_size * 0.8), "bold")
        self.font_cal_weekday = ("Segoe UI", int(self.font_size * 0.65))
        self.font_cal_day = ("Segoe UI", int(self.font_size * 0.65))
        self.font_cal_day_bold = ("Segoe UI", int(self.font_size * 0.65), "bold")

    # --- 自定义复选框组件 ---
    def create_checkbox(self, parent, checked=False, size=22, command=None):
        """创建方形复选框，勾选时显示√"""
        canvas = tk.Canvas(parent, width=size, height=size,
                           bg=self.colors['bg'], highlightthickness=0, cursor="hand2")

        # 保存状态和回调
        canvas.checked = checked
        canvas.command = command
        canvas.size = size

        # 绘制复选框
        self._draw_checkbox(canvas)

        # 绑定点击事件
        canvas.bind("<Button-1>", lambda e: self._toggle_checkbox(canvas))

        return canvas

    def _draw_checkbox(self, canvas):
        """绘制复选框内容"""
        canvas.delete("all")
        size = canvas.size
        padding = 2
        border_width = 2

        if canvas.checked:
            # 已勾选：填充背景 + 绘制√
            # 绘制填充的圆角矩形背景
            canvas.create_rectangle(
                padding, padding, size - padding, size - padding,
                fill=self.colors['checkbox_fill'],
                outline=self.colors['checkbox_fill'],
                width=0
            )
            # 绘制√符号
            check_color = "#FFFFFF"
            # √的坐标点（相对于size缩放）
            x1, y1 = size * 0.22, size * 0.5
            x2, y2 = size * 0.42, size * 0.72
            x3, y3 = size * 0.78, size * 0.28
            canvas.create_line(x1, y1, x2, y2, fill=check_color, width=2, capstyle='round')
            canvas.create_line(x2, y2, x3, y3, fill=check_color, width=2, capstyle='round')
        else:
            # 未勾选：只绘制边框
            canvas.create_rectangle(
                padding, padding, size - padding, size - padding,
                fill="",
                outline=self.colors['checkbox_border'],
                width=border_width
            )

    def _toggle_checkbox(self, canvas):
        """切换复选框状态"""
        canvas.checked = not canvas.checked
        self._draw_checkbox(canvas)
        if canvas.command:
            canvas.command()

    # --- UI 构建 ---
    def setup_ui(self):
        self.colors = THEMES[self.theme_mode]
        self.root.configure(bg=self.colors['bg'])

        for widget in self.root.winfo_children():
            widget.destroy()

        # 0. 主容器 (带边框)
        self.main_container = tk.Frame(self.root, bg=self.colors['bg'],
                                       highlightthickness=1, highlightbackground=self.colors['border'])
        self.main_container.pack(fill='both', expand=True)

        # 1. 顶部控制栏
        self.title_bar = tk.Frame(self.main_container, bg=self.colors['bg'], height=40)
        self.title_bar.pack(fill='x', pady=(10, 0), padx=20)
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)

        app_title = tk.Label(self.title_bar, text="Focus.", font=("Segoe UI", 12, "bold"), fg=self.colors['sub_text'],
                             bg=self.colors['bg'])
        app_title.pack(side='left')
        app_title.bind("<ButtonPress-1>", self.start_move)
        app_title.bind("<B1-Motion>", self.do_move)

        btn_frame = tk.Frame(self.title_bar, bg=self.colors['bg'])
        btn_frame.pack(side='right')

        def create_icon_btn(text, cmd, tooltip):
            color = self.colors['accent'] if (text == "📌" and self.is_topmost) else self.colors['sub_text']
            btn = tk.Label(btn_frame, text=text, fg=color, bg=self.colors['bg'], font=self.font_icon, cursor="hand2")
            btn.pack(side='left', padx=6)
            btn.bind("<Button-1>", cmd)
            btn.bind("<Enter>", lambda e: btn.config(fg=self.colors['fg']))
            btn.bind("<Leave>", lambda e: btn.config(
                fg=self.colors['accent'] if (text == "📌" and self.is_topmost) else self.colors['sub_text']))
            self.create_tooltip(btn, tooltip)
            return btn

        self.btn_pin = create_icon_btn("📌", self.toggle_topmost, "置顶窗口")
        create_icon_btn("⚙", self.open_settings, "偏好设置")

        btn_close = tk.Label(btn_frame, text="×", fg=self.colors['sub_text'], bg=self.colors['bg'], font=("Arial", 20),
                             cursor="hand2")
        btn_close.pack(side='left', padx=(6, 0))
        btn_close.bind("<Button-1>", lambda e: self.save_and_exit())
        btn_close.bind("<Enter>", lambda e: btn_close.config(fg='#EF4444'))
        btn_close.bind("<Leave>", lambda e: btn_close.config(fg=self.colors['sub_text']))

        # 2. 日期导航
        header_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        header_frame.pack(fill='x', padx=20, pady=(15, 5))

        nav_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        nav_frame.pack(fill='x')

        # 左箭头
        btn_prev = tk.Label(nav_frame, text="<", font=self.font_bold, fg=self.colors['sub_text'], bg=self.colors['bg'],
                            cursor="hand2", width=3)
        btn_prev.pack(side='left')
        btn_prev.bind("<Button-1>", lambda e: self.change_date(-1))
        btn_prev.bind("<Enter>", lambda e: btn_prev.config(fg=self.colors['accent']))
        btn_prev.bind("<Leave>", lambda e: btn_prev.config(fg=self.colors['sub_text']))

        # 右箭头
        btn_next = tk.Label(nav_frame, text=">", font=self.font_bold, fg=self.colors['sub_text'], bg=self.colors['bg'],
                            cursor="hand2", width=3)
        btn_next.pack(side='right')
        btn_next.bind("<Button-1>", lambda e: self.change_date(1))
        btn_next.bind("<Enter>", lambda e: btn_next.config(fg=self.colors['accent']))
        btn_next.bind("<Leave>", lambda e: btn_next.config(fg=self.colors['sub_text']))

        # 日期文本容器
        date_container = tk.Frame(nav_frame, bg=self.colors['bg'])
        date_container.pack(fill='both', expand=True)

        self.lbl_date = tk.Label(date_container, text="", font=self.font_title, bg=self.colors['bg'],
                                 fg=self.colors['fg'], cursor="hand2")
        self.lbl_date.pack(expand=True)

        self.lbl_date.bind("<Button-1>", self._on_date_click)
        date_container.bind("<Button-1>", self._on_date_click)

        def on_date_enter(e):
            self.lbl_date.config(fg=self.colors['accent'])

        def on_date_leave(e):
            self.lbl_date.config(fg=self.colors['fg'])

        self.lbl_date.bind("<Enter>", on_date_enter)
        self.lbl_date.bind("<Leave>", on_date_leave)
        date_container.bind("<Enter>", on_date_enter)
        date_container.bind("<Leave>", on_date_leave)

        # 3. 输入区域
        self.entry_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        self.entry_frame.pack(fill='x', padx=20, pady=15)

        input_container = tk.Frame(self.entry_frame, bg=self.colors['input_bg'], padx=10, pady=5)
        input_container.pack(fill='x')

        self.entry = tk.Entry(input_container, font=self.font_main, bg=self.colors['input_bg'],
                              fg=self.colors['input_fg'], bd=0, insertbackground=self.colors['fg'])
        self.entry.pack(side='left', fill='both', expand=True, pady=3)
        self.placeholder_text = "做点什么..."
        self.entry.insert(0, self.placeholder_text)
        self.entry.config(fg=self.colors['sub_text'])
        self.entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.entry.bind("<FocusOut>", self.on_entry_focus_out)
        self.entry.bind("<Return>", self.add_task)

        self.btn_add = tk.Label(input_container, text="+", bg=self.colors['accent'], fg='#FFF',
                                font=("Arial", 16, "bold"), width=3, cursor="hand2")
        self.btn_add.pack(side='right')
        self.btn_add.bind("<Button-1>", self.add_task)

        # 4. 任务列表容器
        self.canvas = tk.Canvas(self.main_container, bg=self.colors['bg'], bd=0, highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas, bg=self.colors['bg'])

        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=INIT_W - 45)

        self.canvas.pack(side="left", fill="both", expand=True, padx=20, pady=(0, 20))

        # 5. Grip
        self.grip = tk.Label(self.root, text=" ", bg=self.colors['bg'], cursor="size_nw_se")
        self.grip.place(relx=1.0, rely=1.0, anchor="se", width=15, height=15)
        self.grip.bind("<ButtonPress-1>", self.start_resize)
        self.grip.bind("<B1-Motion>", self.do_resize)

    def _on_date_click(self, event=None):
        """处理日期点击事件，打开日历"""
        self.open_calendar()

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # --- 设置弹窗 ---
    def open_settings(self, event=None):
        if self.settings_win and tk.Toplevel.winfo_exists(self.settings_win):
            self.settings_win.lift()
            return

        self.settings_win = tk.Toplevel(self.root)
        self.settings_win.title("")
        self.settings_win.attributes('-topmost', True)
        self.settings_win.geometry("420x480")
        self.settings_win.configure(bg=self.colors['bg'])
        self.settings_win.overrideredirect(True)

        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 210
        y = self.root.winfo_y() + 50
        self.settings_win.geometry(f"+{x}+{y}")

        tk.Frame(self.settings_win, bg=self.colors['border'], bd=1).place(x=0, y=0, relwidth=1, relheight=1)

        # Header
        header = tk.Frame(self.settings_win, bg=self.colors['bg'], height=50)
        header.pack(fill='x', padx=2, pady=2)

        title_lbl = tk.Label(header, text="偏好设置", fg=self.colors['fg'], bg=self.colors['bg'],
                             font=self.font_ui_bold)
        title_lbl.place(relx=0.5, rely=0.5, anchor="center")

        close_btn = tk.Label(header, text="×", fg=self.colors['sub_text'], bg=self.colors['bg'], font=("Arial", 18),
                             cursor="hand2")
        close_btn.pack(side='right', padx=10)
        close_btn.bind("<Button-1>", lambda e: self.settings_win.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=self.colors['fg']))

        # Scrollable Area
        container = tk.Frame(self.settings_win, bg=self.colors['bg'])
        container.pack(fill='both', expand=True, padx=2, pady=2)

        canvas = tk.Canvas(container, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.settings_win.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=380)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content = tk.Frame(scrollable_frame, bg=self.colors['bg'], padx=25, pady=10)
        content.pack(fill='both', expand=True)

        # --- 配色方案 ---
        tk.Label(content, text="配色方案", fg=self.colors['sub_text'], bg=self.colors['bg'],
                 font=self.font_ui_small).pack(anchor='w', pady=(15, 5))
        theme_btn_text = "切换至 浅色模式 ☀" if self.theme_mode == "dark" else "切换至 深色模式 🌙"
        tk.Button(content, text=theme_btn_text, command=lambda: [self.toggle_theme(), self.settings_win.destroy()],
                  bg=self.colors['input_bg'], fg=self.colors['fg'],
                  bd=0, font=self.font_ui_small, pady=8).pack(fill='x')

        # --- 文字排版 ---
        tk.Label(content, text="文字排版", fg=self.colors['sub_text'], bg=self.colors['bg'],
                 font=self.font_ui_small).pack(anchor='w', pady=(20, 5))
        f_frame = tk.Frame(content, bg=self.colors['bg'])
        f_frame.pack(fill='x')

        def set_font(size):
            self.font_size = size
            self.update_fonts()
            self.save_config()
            self.setup_ui()
            self.render_tasks()
            self.settings_win.destroy()
            self.open_settings()

        current_size = self.font_size
        for size in [14, 16, 18, 20]:
            is_active = (size == current_size)
            bg_c = self.colors['accent'] if is_active else self.colors['input_bg']
            fg_c = '#FFF' if is_active else self.colors['fg']
            tk.Button(f_frame, text=f"{size}", command=lambda s=size: set_font(s),
                      bg=bg_c, fg=fg_c, bd=0, width=5, font=self.font_ui_small).pack(side='left', padx=(0, 10))

        # --- 背景透明度 ---
        tk.Label(content, text="背景透明度", fg=self.colors['sub_text'], bg=self.colors['bg'],
                 font=self.font_ui_small).pack(anchor='w', pady=(20, 5))

        opacity_frame = tk.Frame(content, bg=self.colors['bg'])
        opacity_frame.pack(fill='x')

        # 透明度显示标签
        self.opacity_label = tk.Label(opacity_frame, text=f"{int(self.opacity * 100)}%",
                                      fg=self.colors['fg'], bg=self.colors['bg'],
                                      font=self.font_ui_bold, width=5)
        self.opacity_label.pack(side='right')

        # 使用 ttk.Scale 配合自定义样式实现橙色滑块
        style = ttk.Style()
        style.theme_use('clam')

        # 配置橙色滑块样式
        style.configure("Orange.Horizontal.TScale",
                        background=self.colors['bg'],
                        troughcolor=self.colors['input_bg'],
                        sliderthickness=16,
                        sliderlength=20)

        style.map("Orange.Horizontal.TScale",
                  background=[('active', self.colors['accent'])])

        # 创建一个自定义滑块容器
        slider_container = tk.Frame(opacity_frame, bg=self.colors['bg'])
        slider_container.pack(side='left', fill='x', expand=True, padx=(0, 10))

        # 使用Canvas绘制自定义滑块
        self.opacity_canvas = tk.Canvas(slider_container, height=30, bg=self.colors['bg'],
                                        highlightthickness=0, cursor="hand2")
        self.opacity_canvas.pack(fill='x', expand=True)

        # 滑块参数
        self.slider_padding = 10
        self.slider_height = 6
        self.knob_radius = 8

        def draw_slider(value):
            self.opacity_canvas.delete("all")
            width = self.opacity_canvas.winfo_width()
            if width < 50:
                width = 280

            track_y = 15
            track_left = self.slider_padding + self.knob_radius
            track_right = width - self.slider_padding - self.knob_radius
            track_width = track_right - track_left

            # 绘制轨道背景
            self.opacity_canvas.create_rectangle(
                track_left, track_y - self.slider_height // 2,
                track_right, track_y + self.slider_height // 2,
                fill=self.colors['input_bg'], outline=""
            )

            # 计算滑块位置 (value: 30-100)
            progress = (value - 30) / 70
            knob_x = track_left + progress * track_width

            # 绘制已填充部分（橙色）
            self.opacity_canvas.create_rectangle(
                track_left, track_y - self.slider_height // 2,
                knob_x, track_y + self.slider_height // 2,
                fill=self.colors['accent'], outline=""
            )

            # 绘制滑块圆点（橙色）
            self.opacity_canvas.create_oval(
                knob_x - self.knob_radius, track_y - self.knob_radius,
                knob_x + self.knob_radius, track_y + self.knob_radius,
                fill=self.colors['accent'], outline=""
            )

        def on_slider_click(event):
            update_slider_from_event(event)

        def on_slider_drag(event):
            update_slider_from_event(event)

        def update_slider_from_event(event):
            width = self.opacity_canvas.winfo_width()
            track_left = self.slider_padding + self.knob_radius
            track_right = width - self.slider_padding - self.knob_radius
            track_width = track_right - track_left

            # 计算点击位置对应的值
            x = max(track_left, min(event.x, track_right))
            progress = (x - track_left) / track_width
            value = int(30 + progress * 70)

            # 更新透明度
            self.opacity = value / 100.0
            self.root.attributes('-alpha', self.opacity)
            self.opacity_label.config(text=f"{value}%")
            self.save_config()

            draw_slider(value)

        self.opacity_canvas.bind("<Button-1>", on_slider_click)
        self.opacity_canvas.bind("<B1-Motion>", on_slider_drag)
        self.opacity_canvas.bind("<Configure>", lambda e: draw_slider(int(self.opacity * 100)))

        # 初始绘制
        self.root.after(10, lambda: draw_slider(int(self.opacity * 100)))

        # --- 数据存储 ---
        tk.Label(content, text="数据存储", fg=self.colors['sub_text'], bg=self.colors['bg'],
                 font=self.font_ui_small).pack(anchor='w', pady=(20, 5))
        path_box = tk.Frame(content, bg=self.colors['input_bg'], padx=10, pady=10)
        path_box.pack(fill='x')
        tk.Label(path_box, text=self.data_dir, fg=self.colors['sub_text'], bg=self.colors['input_bg'],
                 font=("Segoe UI", int(self.font_size * 0.7)), wraplength=320, justify='left').pack(fill='x')

        def change_path():
            self.settings_win.attributes('-topmost', False)
            new_dir = filedialog.askdirectory()
            self.settings_win.attributes('-topmost', True)
            if new_dir:
                self.data_dir = new_dir
                self.save_config()
                self.tasks_data = self.load_tasks_data()
                self.render_tasks()
                self.settings_win.destroy()

        tk.Button(content, text="更改文件夹...", command=change_path,
                  bg=self.colors['bg'], fg=self.colors['accent'], bd=0,
                  font=self.font_ui_bold, cursor="hand2").pack(anchor='e', pady=5)

    # --- 日历弹窗 ---
    def open_calendar(self, event=None):
        """打开日历弹窗"""
        if self.calendar_win is not None:
            try:
                if self.calendar_win.winfo_exists():
                    self.calendar_win.lift()
                    self.calendar_win.focus_force()
                    return
            except tk.TclError:
                pass
            self.calendar_win = None

        self.calendar_win = tk.Toplevel(self.root)
        self.calendar_win.overrideredirect(True)
        self.calendar_win.configure(bg=self.colors['cal_bg'])
        self.calendar_win.attributes('-topmost', True)
        # 日历窗口也应用透明度
        self.calendar_win.attributes('-alpha', self.opacity)

        # 根据字号动态计算日历尺寸
        base_width = 280
        base_height = 300
        scale = self.font_size / 14.0
        cal_width = int(base_width * scale)
        cal_height = int(base_height * scale)

        x = self.root.winfo_x() + (self.root.winfo_width() - cal_width) // 2
        y = self.root.winfo_y() + 100
        self.calendar_win.geometry(f"{cal_width}x{cal_height}+{x}+{y}")

        border_frame = tk.Frame(self.calendar_win, bg=self.colors['border'])
        border_frame.pack(fill='both', expand=True, padx=1, pady=1)

        inner = tk.Frame(border_frame, bg=self.colors['cal_bg'])
        inner.pack(fill='both', expand=True)

        self.cal_view_date = self.current_date
        self._cal_inner = inner

        def render_cal_grid():
            for w in self._cal_inner.winfo_children():
                w.destroy()

            # 顶部导航栏
            header = tk.Frame(self._cal_inner, bg=self.colors['cal_bg'])
            header.pack(fill='x', pady=10, padx=10)

            prev_btn = tk.Button(header, text="◀", command=lambda: change_month(-1),
                                 bg=self.colors['cal_bg'], fg=self.colors['fg'],
                                 bd=0, cursor="hand2", font=self.font_cal_day)
            prev_btn.pack(side='left')

            month_label = tk.Label(header, text=self.cal_view_date.strftime("%Y年 %m月"),
                                   bg=self.colors['cal_bg'], fg=self.colors['fg'],
                                   font=self.font_cal_header)
            month_label.pack(side='left', expand=True)

            next_btn = tk.Button(header, text="▶", command=lambda: change_month(1),
                                 bg=self.colors['cal_bg'], fg=self.colors['fg'],
                                 bd=0, cursor="hand2", font=self.font_cal_day)
            next_btn.pack(side='right')

            # 星期头
            days_header = tk.Frame(self._cal_inner, bg=self.colors['cal_bg'])
            days_header.pack(pady=5)
            # 根据字号计算宽度
            day_width = max(3, int(4 * (14 / self.font_size)))
            for day in ["一", "二", "三", "四", "五", "六", "日"]:
                tk.Label(days_header, text=day, width=day_width, fg=self.colors['sub_text'],
                         bg=self.colors['cal_bg'], font=self.font_cal_weekday).pack(side='left')

            # 日历网格
            cal = calendar.monthcalendar(self.cal_view_date.year, self.cal_view_date.month)
            grid_frame = tk.Frame(self._cal_inner, bg=self.colors['cal_bg'])
            grid_frame.pack(padx=10, pady=(0, 10))

            today = datetime.date.today()

            for week in cal:
                row = tk.Frame(grid_frame, bg=self.colors['cal_bg'])
                row.pack()
                for day in week:
                    if day == 0:
                        tk.Label(row, text=" ", width=day_width, bg=self.colors['cal_bg'],
                                 font=self.font_cal_day).pack(side='left')
                    else:
                        is_today = (day == today.day and
                                    self.cal_view_date.month == today.month and
                                    self.cal_view_date.year == today.year)

                        is_selected = (day == self.current_date.day and
                                       self.cal_view_date.month == self.current_date.month and
                                       self.cal_view_date.year == self.current_date.year)

                        if is_today:
                            fg_c = '#FFFFFF'
                            bg_c = self.colors['cal_today']
                        elif is_selected:
                            fg_c = self.colors['accent']
                            bg_c = self.colors['cal_bg']
                        else:
                            fg_c = self.colors['fg']
                            bg_c = self.colors['cal_bg']

                        btn = tk.Button(row, text=str(day), width=day_width, bd=0,
                                        bg=bg_c, fg=fg_c,
                                        font=self.font_cal_day_bold if is_today else self.font_cal_day,
                                        command=lambda d=day: select_date(d),
                                        cursor="hand2",
                                        activebackground=self.colors['hover'],
                                        activeforeground=self.colors['fg'])
                        btn.pack(side='left')

                        if not is_today:
                            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors['hover']))
                            btn.bind("<Leave>", lambda e, b=btn, c=bg_c: b.config(bg=c))

        def change_month(step):
            y, m = self.cal_view_date.year, self.cal_view_date.month + step
            if m > 12:
                m, y = 1, y + 1
            elif m < 1:
                m, y = 12, y - 1
            self.cal_view_date = datetime.date(y, m, 1)
            render_cal_grid()

        def select_date(day):
            self.current_date = datetime.date(self.cal_view_date.year, self.cal_view_date.month, day)
            self.render_tasks()
            self._close_calendar()

        # 关闭按钮
        close_btn = tk.Label(self.calendar_win, text="×", bg=self.colors['cal_bg'],
                             fg=self.colors['sub_text'], font=("Arial", int(self.font_size * 0.9)), cursor="hand2")
        close_btn.place(relx=1.0, x=-10, y=5, anchor='ne')
        close_btn.bind("<Button-1>", lambda e: self._close_calendar())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=self.colors['fg']))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=self.colors['sub_text']))

        render_cal_grid()
        self.calendar_win.focus_force()

    def _close_calendar(self):
        """安全关闭日历窗口"""
        if self.calendar_win:
            try:
                self.calendar_win.destroy()
            except:
                pass
            self.calendar_win = None

    # --- 渲染逻辑 ---
    def render_tasks(self):
        self.update_date_display()
        bg_color = self.colors['bg']

        for w in self.scroll_frame.winfo_children(): w.destroy()

        date_key = self.current_date.strftime("%Y-%m-%d")
        tasks = self.tasks_data.get(date_key, [])

        if not tasks:
            f = tk.Frame(self.scroll_frame, bg=bg_color)
            f.pack(pady=40, fill='both', expand=True)
            tk.Label(f, text="☕", font=("Segoe UI", 30), bg=bg_color).pack(anchor='center')
            tk.Label(f, text="今日无事，保持专注", fg=self.colors['sub_text'], bg=bg_color, font=("Segoe UI", 11)).pack(
                pady=5, anchor='center')
            return

        # 计算复选框大小（根据字号）
        checkbox_size = max(18, int(self.font_size * 1.4))

        for i, task in enumerate(tasks):
            row = tk.Frame(self.scroll_frame, bg=bg_color)
            row.pack(fill='x', pady=6)

            # 使用自定义复选框
            checkbox = self.create_checkbox(
                row,
                checked=task['done'],
                size=checkbox_size,
                command=lambda idx=i: self.toggle_task(idx)
            )
            checkbox.pack(side='left', padx=(0, 10), pady=2)

            # 任务文本
            text_fg = self.colors['fg'] if not task['done'] else self.colors['sub_text']
            lbl = tk.Label(row, text=task['text'], fg=text_fg, bg=bg_color,
                           font=self.font_main, anchor='w', wraplength=260, justify='left')
            lbl.pack(side='left', fill='x', expand=True, pady=2)

            # 点击文本也可以切换状态
            lbl.bind("<Button-1>", lambda e, idx=i: self.toggle_task(idx))
            lbl.config(cursor="hand2")

            # 删除按钮
            d_btn = tk.Label(row, text="×", fg=bg_color, bg=bg_color,
                             font=("Arial", 16), cursor="hand2", width=2)
            d_btn.pack(side='right', anchor='n')
            d_btn.bind("<Button-1>", lambda e, idx=i: self.delete_task(idx))

            # 悬停效果
            def on_row_enter(e, b=d_btn, r=row, t=lbl, c=checkbox, bg=bg_color):
                hover_bg = self.colors['hover']
                r.config(bg=hover_bg)
                t.config(bg=hover_bg)
                c.config(bg=hover_bg)
                b.config(bg=hover_bg, fg=self.colors['sub_text'])

            def on_row_leave(e, b=d_btn, r=row, t=lbl, c=checkbox, bg=bg_color):
                r.config(bg=bg)
                t.config(bg=bg)
                c.config(bg=bg)
                b.config(bg=bg, fg=bg)

            for w in [row, lbl, d_btn]:
                w.bind("<Enter>", lambda e, b=d_btn, r=row, t=lbl, c=checkbox: on_row_enter(e, b, r, t, c))
                w.bind("<Leave>", lambda e, b=d_btn, r=row, t=lbl, c=checkbox: on_row_leave(e, b, r, t, c))

    def update_date_display(self):
        txt = self.current_date.strftime("%m / %d")
        week_day = ["周一", "周二", "周三", "周四", "周五", "周六", "周天"][self.current_date.weekday()]
        today = datetime.date.today()
        prefix = "今天" if self.current_date == today else (
            "明天" if self.current_date == today + datetime.timedelta(days=1) else "")
        final_txt = f"{prefix} · {txt}" if prefix else f"{week_day} · {txt}"
        self.lbl_date.config(text=final_txt)

    def change_date(self, offset):
        self.current_date += datetime.timedelta(days=offset)
        self.render_tasks()

    def add_task(self, event=None):
        text = self.entry.get().strip()
        if text and text != self.placeholder_text:
            k = self.current_date.strftime("%Y-%m-%d")
            if k not in self.tasks_data: self.tasks_data[k] = []
            self.tasks_data[k].append({"text": text, "done": False})
            self.entry.delete(0, tk.END)
            self.save_tasks_data()
            self.render_tasks()

    def toggle_task(self, idx):
        k = self.current_date.strftime("%Y-%m-%d")
        self.tasks_data[k][idx]['done'] = not self.tasks_data[k][idx]['done']
        self.save_tasks_data()
        self.render_tasks()

    def delete_task(self, idx):
        k = self.current_date.strftime("%Y-%m-%d")
        del self.tasks_data[k][idx]
        self.save_tasks_data()
        self.render_tasks()

    def on_entry_focus_in(self, e):
        if self.entry.get() == self.placeholder_text:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.colors['input_fg'])

    def on_entry_focus_out(self, e):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder_text)
            self.entry.config(fg=self.colors['sub_text'])

    def save_and_exit(self):
        self.save_config()
        self.root.destroy()

    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def do_move(self, event):
        self.root.geometry(f"+{self.root.winfo_x() + event.x - self.x}+{self.root.winfo_y() + event.y - self.y}")

    def start_resize(self, event):
        self.resize_start_x, self.resize_start_y, self.start_w, self.start_h = event.x_root, event.y_root, self.root.winfo_width(), self.root.winfo_height()

    def do_resize(self, event):
        new_w, new_h = self.start_w + event.x_root - self.resize_start_x, self.start_h + event.y_root - self.resize_start_y
        if new_w > MIN_WIDTH and new_h > MIN_HEIGHT:
            self.root.geometry(f"{new_w}x{new_h}")
            if self.canvas.find_all(): self.canvas.itemconfig(self.canvas_window, width=new_w - 45)

    def toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.save_config()
        self.setup_ui()
        self.render_tasks()

    def toggle_topmost(self, event=None):
        self.is_topmost = not self.is_topmost
        self.root.attributes('-topmost', self.is_topmost)
        self.btn_pin.config(fg=self.colors['accent'] if self.is_topmost else self.colors['sub_text'])
        self.save_config()

    def create_tooltip(self, widget, text):
        def enter(event):
            if hasattr(self, 'tooltip'): self.tooltip.destroy()
            self.tooltip = tk.Toplevel()
            self.tooltip.overrideredirect(True)
            self.tooltip.attributes('-topmost', True)
            self.tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tk.Label(self.tooltip, text=text, bg=self.colors['fg'], fg=self.colors['bg'], bd=0, padx=4,
                     font=("Segoe UI", 9)).pack()

        def leave(event):
            if hasattr(self, 'tooltip'): self.tooltip.destroy()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernTodoApp(root)
    root.mainloop()