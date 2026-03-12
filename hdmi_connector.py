import tkinter as tk
from tkinter import messagebox
import subprocess
import ctypes
import ctypes.wintypes
import json, os

# ── Windows API ───────────────────────────────────────
SM_CMONITORS = 80
DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ── 색상 ─────────────────────────────────────────────
BG        = "#0f0f1a"
BG_CARD   = "#1a1a2e"
BG_CARD2  = "#16213e"
BG_HEADER = "#0d0d20"
C_RED     = "#ff4757"
C_GREEN   = "#2ed573"
C_YELLOW  = "#ffa502"
C_BLUE    = "#1e90ff"
C_CYAN    = "#4ecca3"
C_WHITE   = "#f0f0f0"
C_GRAY    = "#778ca3"
C_DIM     = "#3d3d5c"

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def load_settings():
    try:
        with open(SETTINGS_FILE) as f: return json.load(f)
    except Exception: return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f: json.dump(data, f)
    except Exception: pass

# ── 진단 ─────────────────────────────────────────────
def get_monitor_count():
    return ctypes.windll.user32.GetSystemMetrics(SM_CMONITORS)

def get_display_devices():
    class DISPLAY_DEVICEW(ctypes.Structure):
        _fields_ = [
            ("cb",           ctypes.wintypes.DWORD),
            ("DeviceName",   ctypes.c_wchar * 32),
            ("DeviceString", ctypes.c_wchar * 128),
            ("StateFlags",   ctypes.wintypes.DWORD),
            ("DeviceID",     ctypes.c_wchar * 128),
            ("DeviceKey",    ctypes.c_wchar * 128),
        ]
    devices, i = [], 0
    while True:
        dd = DISPLAY_DEVICEW()
        dd.cb = ctypes.sizeof(dd)
        if not ctypes.windll.user32.EnumDisplayDevicesW(None, i, ctypes.byref(dd), 0):
            break
        if dd.DeviceString:
            devices.append({
                "name": dd.DeviceName, "string": dd.DeviceString,
                "active": bool(dd.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP),
            })
        i += 1
    return devices

def get_resolution(device_name):
    class DEVMODEW(ctypes.Structure):
        _fields_ = [
            ("dmDeviceName",        ctypes.c_wchar * 32),
            ("dmSpecVersion",       ctypes.c_ushort),
            ("dmDriverVersion",     ctypes.c_ushort),
            ("dmSize",              ctypes.c_ushort),
            ("dmDriverExtra",       ctypes.c_ushort),
            ("dmFields",            ctypes.wintypes.DWORD),
            ("dmPositionX",         ctypes.c_int),
            ("dmPositionY",         ctypes.c_int),
            ("dmDisplayOrientation",ctypes.wintypes.DWORD),
            ("dmDisplayFixedOutput",ctypes.wintypes.DWORD),
            ("dmColor",             ctypes.c_short),
            ("dmDuplex",            ctypes.c_short),
            ("dmYResolution",       ctypes.c_short),
            ("dmTTOption",          ctypes.c_short),
            ("dmCollate",           ctypes.c_short),
            ("dmFormName",          ctypes.c_wchar * 32),
            ("dmLogPixels",         ctypes.c_ushort),
            ("dmBitsPerPel",        ctypes.wintypes.DWORD),
            ("dmPelsWidth",         ctypes.wintypes.DWORD),
            ("dmPelsHeight",        ctypes.wintypes.DWORD),
            ("dmDisplayFlags",      ctypes.wintypes.DWORD),
            ("dmDisplayFrequency",  ctypes.wintypes.DWORD),
        ]
    dm = DEVMODEW(); dm.dmSize = ctypes.sizeof(dm)
    if ctypes.windll.user32.EnumDisplaySettingsW(device_name, -1, ctypes.byref(dm)):
        return dm.dmPelsWidth, dm.dmPelsHeight, dm.dmDisplayFrequency
    return None

def diagnose():
    n = get_monitor_count()
    devices = get_display_devices()
    active = [d for d in devices if d["active"]]
    for d in active:
        res = get_resolution(d["name"])
        d["resolution"] = f"{res[0]}×{res[1]} @{res[2]}Hz" if res else ""
    if n <= 1:
        issues = ["외부 디스플레이(TV/모니터)가 감지되지 않습니다."]
        solutions = [
            "① HDMI 케이블이 노트북과 TV 양쪽에 단단히 꽂혀 있는지 확인하세요.",
            "② TV 리모컨으로 입력 소스를 'HDMI'로 변경하세요.",
            "③ HDMI 케이블을 뽑았다가 5초 후 다시 꽂아보세요.",
            "④ TV 전원을 껐다가 다시 켜보세요.",
            "⑤ 다른 HDMI 포트 또는 다른 케이블로 교체해보세요.",
            "⑥ '디스플레이 재검색' 버튼을 눌러보세요.",
        ]
    else:
        issues = [f"외부 디스플레이 {n - 1}개 연결됨."]
        solutions = ["아래 버튼으로 원하는 연결 모드를 선택하세요."]
    return {"count": n, "active": active,
            "issues": issues, "solutions": solutions, "connected": n > 1}

def run_displayswitch(mode):
    try:
        subprocess.Popen(["displayswitch.exe", mode]); return True
    except Exception: return False


# ── 메인 앱 ──────────────────────────────────────────
class HDMIApp(tk.Tk):
    W, H   = 720, 800
    _fs    = False
    _prev  = None
    _flash = None

    MODES = [
        ("화면 복제",  "내 화면 = TV 화면", "/clone",    C_CYAN,   "수업용 추천", "1"),
        ("화면 확장",  "두 화면 독립 사용",  "/extend",   C_BLUE,   "발표용",      "2"),
        ("TV만 표시", "노트북 화면 끄기",   "/external", C_YELLOW, "프레젠테이션","3"),
        ("노트북만",   "TV 연결 끊기",      "/internal", C_RED,    "연결 끊기",   "4"),
    ]

    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.title("HDMI 연결 도우미")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(480, 560)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{self.W}x{self.H}+{(sw-self.W)//2}+{(sh-self.H)//2}")
        self._build_ui()
        self._bind_keys()
        self.after(300, self._first_refresh)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bind_keys(self):
        self.bind("<F11>",    lambda e: self.toggle_fullscreen())
        self.bind("<Escape>", lambda e: self.exit_fullscreen())
        self.bind("<F5>",     lambda e: self.refresh())
        for _, _, mode, _, _, key in self.MODES:
            self.bind(key, lambda e, m=mode: self.connect(m))

    def _build_ui(self):
        self.frm_header = tk.Frame(self, bg=BG_HEADER, height=56)
        self.frm_header.pack(fill="x", side="top")
        self.frm_header.pack_propagate(False)

        self.lbl_title = tk.Label(
            self.frm_header, text="🖥  HDMI 연결 도우미",
            font=("맑은 고딕", 15, "bold"), bg=BG_HEADER, fg=C_WHITE)
        self.lbl_title.pack(side="left", padx=18)

        self.btn_fs = tk.Button(
            self.frm_header, text="⛶  전체화면  [F11]",
            font=("맑은 고딕", 9), bg=BG_HEADER, fg=C_DIM,
            relief="flat", bd=0, cursor="hand2",
            activebackground=BG_HEADER, activeforeground=C_CYAN,
            command=self.toggle_fullscreen)
        self.btn_fs.pack(side="right", padx=14)

        self.lbl_badge = tk.Label(
            self.frm_header, text="● 확인 중...",
            font=("맑은 고딕", 10), bg=BG_HEADER, fg=C_YELLOW)
        self.lbl_badge.pack(side="right")

        self.frm_footer = tk.Frame(self, bg=BG_HEADER, height=28)
        self.frm_footer.pack(fill="x", side="bottom")
        self.frm_footer.pack_propagate(False)
        tk.Label(self.frm_footer,
                 text="Win+P  |  F11 전체화면  |  F5 새로고침  |  1~4 빠른 연결",
                 font=("맑은 고딕", 8), bg=BG_HEADER, fg=C_DIM).pack(pady=5)

        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=BG)
        self._win_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._build_content()

    def _build_content(self):
        pad = dict(padx=18, pady=(10, 0))

        self.frm_status = tk.Frame(self.inner, bg=BG_CARD)
        self.frm_status.pack(fill="x", **pad)

        self.lbl_s_icon = tk.Label(
            self.frm_status, text="", font=("Segoe UI Emoji", 40), bg=BG_CARD)
        self.lbl_s_icon.pack(pady=(16, 2))

        self.lbl_s_title = tk.Label(
            self.frm_status, text="",
            font=("맑은 고딕", 14, "bold"), bg=BG_CARD, fg=C_WHITE)
        self.lbl_s_title.pack()

        self.lbl_s_sub = tk.Label(
            self.frm_status, text="",
            font=("맑은 고딕", 10), bg=BG_CARD, fg=C_GRAY,
            wraplength=640, justify="center")
        self.lbl_s_sub.pack(pady=(3, 14))

        self.lbl_devinfo = tk.Label(
            self.inner, text="",
            font=("맑은 고딕", 9), bg=BG, fg=C_GRAY)
        self.lbl_devinfo.pack(anchor="w", padx=20, pady=(6, 0))

        self.frm_diag = tk.Frame(self.inner, bg=BG_CARD)
        self.frm_diag.pack(fill="x", **pad)

        tk.Label(self.frm_diag, text="  진단 결과 및 해결 방법",
                 font=("맑은 고딕", 10, "bold"), bg=BG_CARD,
                 fg=C_YELLOW, anchor="w").pack(fill="x", pady=(10, 4))

        self.txt_diag = tk.Text(
            self.frm_diag, height=7, bg=BG_CARD, fg=C_WHITE,
            font=("맑은 고딕", 10), relief="flat", wrap="word",
            state="disabled", cursor="arrow",
            bd=0, highlightthickness=0, selectbackground=BG_CARD)
        self.txt_diag.pack(fill="x", padx=10, pady=(0, 10))

        frm_q = tk.Frame(self.inner, bg=BG)
        frm_q.pack(fill="x", padx=18, pady=(10, 0))
        for text, cmd, color in [
            ("⟳  새로고침  F5",     self.refresh,        C_GRAY),
            ("⎙  디스플레이 재검색", self.detect_display, C_BLUE),
            ("⚙  드라이버 새로고침", self.refresh_driver, C_DIM),
        ]:
            tk.Button(frm_q, text=text, command=cmd,
                      font=("맑은 고딕", 9), bg=BG_CARD2, fg=color,
                      relief="flat", bd=0, cursor="hand2", padx=12, pady=6,
                      activebackground=BG_CARD, activeforeground=color
                      ).pack(side="left", padx=(0, 8))

        frm_ml = tk.Frame(self.inner, bg=BG)
        frm_ml.pack(fill="x", padx=18, pady=(14, 0))
        tk.Label(frm_ml, text="연결 모드  (단축키: 1 ~ 4)",
                 font=("맑은 고딕", 10, "bold"), bg=BG, fg=C_WHITE
                 ).pack(anchor="w", pady=(0, 6))

        self.frm_modes = tk.Frame(frm_ml, bg=BG)
        self.frm_modes.pack(fill="x")
        self.frm_modes.columnconfigure(0, weight=1)
        self.frm_modes.columnconfigure(1, weight=1)

        for i, (title, sub, mode, color, tag, key) in enumerate(self.MODES):
            self._mode_btn(self.frm_modes, title, sub, mode, color, tag, key,
                           row=i // 2, col=i % 2)

        tk.Frame(self.inner, bg=BG, height=14).pack()

    def _mode_btn(self, parent, title, sub, mode, color, tag, key, row, col):
        px = (0, 8) if col == 0 else (0, 0)
        outer = tk.Frame(parent, bg=C_DIM)
        outer.grid(row=row, column=col, padx=px, pady=5, sticky="ew")
        inner = tk.Frame(outer, bg=BG_CARD2)
        inner.pack(fill="both", padx=1, pady=1)
        bar = tk.Frame(inner, bg=color, height=4)
        bar.pack(fill="x"); bar.pack_propagate(False)
        body = tk.Frame(inner, bg=BG_CARD2)
        body.pack(fill="x", padx=12, pady=10)
        top = tk.Frame(body, bg=BG_CARD2)
        top.pack(fill="x")
        tk.Label(top, text=title, font=("맑은 고딕", 12, "bold"),
                 bg=BG_CARD2, fg=color, anchor="w").pack(side="left")
        tk.Label(top, text=f"[{key}]", font=("맑은 고딕", 8),
                 bg=BG_CARD2, fg=C_DIM).pack(side="right")
        tk.Label(body, text=sub, font=("맑은 고딕", 9),
                 bg=BG_CARD2, fg=C_GRAY, anchor="w").pack(fill="x")
        tk.Label(body, text=tag, font=("맑은 고딕", 8),
                 bg=color, fg="#000", padx=6, pady=1
                 ).pack(anchor="w", pady=(4, 0))

        def do_click(e=None, m=mode): self.connect(m)
        def on_enter(e, o=outer, c=color): o.configure(bg=c)
        def on_leave(e, o=outer): o.configure(bg=C_DIM)

        all_w = [outer, inner, body, bar, top] + list(body.winfo_children()) + list(top.winfo_children())
        for w in all_w:
            w.bind("<Button-1>", do_click)
            w.bind("<Enter>",    on_enter)
            w.bind("<Leave>",    on_leave)

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self._win_id, width=event.width)
        self.lbl_s_sub.config(wraplength=max(event.width - 80, 300))

    def toggle_fullscreen(self):
        self._fs = not self._fs
        self.attributes("-fullscreen", self._fs)
        if self._fs:
            self.btn_fs.config(text="✕  전체화면 해제  [Esc]", fg=C_CYAN)
            self._scale_fonts(1.35)
        else:
            self.btn_fs.config(text="⛶  전체화면  [F11]", fg=C_DIM)
            self._scale_fonts(1.0)

    def exit_fullscreen(self):
        if self._fs: self.toggle_fullscreen()

    def _scale_fonts(self, s):
        specs = {
            self.lbl_title:   ("맑은 고딕", int(15*s), "bold"),
            self.lbl_badge:   ("맑은 고딕", int(10*s)),
            self.lbl_s_icon:  ("Segoe UI Emoji", int(40*s)),
            self.lbl_s_title: ("맑은 고딕", int(14*s), "bold"),
            self.lbl_s_sub:   ("맑은 고딕", int(10*s)),
            self.lbl_devinfo: ("맑은 고딕", int(9*s)),
            self.txt_diag:    ("맑은 고딕", int(10*s)),
        }
        for w, f in specs.items():
            try: w.config(font=f)
            except Exception: pass
        self.frm_header.config(height=int(56*s))
        self.frm_footer.config(height=int(28*s))

    def _first_refresh(self):
        self.refresh(); self._schedule()

    def _schedule(self):
        self.after(5000, lambda: (self.refresh(), self._schedule()))

    def refresh(self):
        data = diagnose()
        if self._prev is not None and self._prev != data["connected"]:
            self._flash_badge(C_CYAN if data["connected"] else C_RED)
        self._prev = data["connected"]
        self._update_status(data)
        self._update_diag(data)
        self._update_devinfo(data)

    def _update_status(self, data):
        if data["connected"]:
            self.lbl_badge.config(text="● 연결됨", fg=C_GREEN)
            self.lbl_s_icon.config(text="✅")
            self.lbl_s_title.config(text="외부 디스플레이 연결됨", fg=C_GREEN)
            self.lbl_s_sub.config(text=f"디스플레이 {data['count']}개 감지. 아래에서 연결 모드를 선택하세요.")
            bg = BG_CARD
        else:
            self.lbl_badge.config(text="● 연결 안됨", fg=C_RED)
            self.lbl_s_icon.config(text="❌")
            self.lbl_s_title.config(text="외부 디스플레이 감지 안됨", fg=C_RED)
            self.lbl_s_sub.config(text="TV/모니터가 연결되지 않았습니다. 아래 해결 방법을 따라 진행하세요.")
            bg = "#1e0f12"
        self.frm_status.config(bg=bg)
        for w in (self.lbl_s_icon, self.lbl_s_title, self.lbl_s_sub):
            w.config(bg=bg)

    def _update_diag(self, data):
        self.txt_diag.config(state="normal")
        self.txt_diag.delete("1.0", "end")
        for issue in data["issues"]:
            self.txt_diag.insert("end", f"  ⚠  {issue}\n\n")
        for sol in data["solutions"]:
            self.txt_diag.insert("end", f"     {sol}\n")
        self.txt_diag.config(state="disabled")

    def _update_devinfo(self, data):
        parts = []
        for d in data["active"]:
            info = d["string"]
            if d.get("resolution"): info += f"  ({d['resolution']})"
            parts.append(info)
        self.lbl_devinfo.config(
            text="감지:  " + "   |   ".join(parts[:3]) if parts else "감지된 디스플레이 없음")

    def _flash_badge(self, color):
        if self._flash: self.after_cancel(self._flash)
        orig = self.lbl_badge.cget("fg")
        self.lbl_badge.config(fg=color)
        self._flash = self.after(800, lambda: self.lbl_badge.config(fg=orig))

    def connect(self, mode):
        labels = {"/clone":"화면 복제","/extend":"화면 확장",
                  "/external":"TV만 표시","/internal":"노트북만"}
        if run_displayswitch(mode):
            self.lbl_badge.config(text=f"● {labels[mode]} 적용 중...", fg=C_YELLOW)
            self.settings["last_mode"] = mode
            save_settings(self.settings)
            self.after(2000, self.refresh)
        else:
            messagebox.showerror("오류", "displayswitch.exe 실행에 실패했습니다.\nWin+P 를 눌러 수동으로 변경하세요.")

    def refresh_driver(self):
        try:
            subprocess.Popen(["pnputil", "/scan-devices"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            self.lbl_badge.config(text="● 드라이버 새로고침 중...", fg=C_YELLOW)
            self.after(3000, self.refresh)
        except Exception:
            messagebox.showinfo("안내", "드라이버 새로고침에는 관리자 권한이 필요합니다.\n프로그램을 '관리자로 실행'해 주세요.")

    def detect_display(self):
        try:
            subprocess.Popen(
                ["powershell", "-Command",
                 "Get-PnpDevice -Class Monitor | Enable-PnpDevice -Confirm:$false -EA SilentlyContinue"],
                creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception: pass
        self.lbl_badge.config(text="● 디스플레이 재검색 중...", fg=C_YELLOW)
        self.after(2500, self.refresh)

    def _on_close(self):
        save_settings(self.settings); self.destroy()


if __name__ == "__main__":
    app = HDMIApp()
    app.mainloop()
