import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
import re
import unicodedata
from io import BytesIO
import matplotlib.pyplot as plt

# ==========================================
# PHẦN 1: KẾT NỐI & TỰ ĐỘNG VÁ LỖI DATABASE
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    
    # Tạo bảng classes
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (class_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  class_name TEXT UNIQUE, 
                  teacher_name TEXT DEFAULT 'Chưa phân công')''')
    
    # Kiểm tra cột cho bảng classes
    c.execute("PRAGMA table_info(classes)")
    cols_classes = [col[1] for col in c.fetchall()]
    if 'teacher_name' not in cols_classes:
        c.execute("ALTER TABLE classes ADD COLUMN teacher_name TEXT DEFAULT 'Chưa phân công'")

    # Tạo bảng users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                  class_name TEXT DEFAULT 'Chưa phân lớp',
                  full_name TEXT DEFAULT '')''')
    
    # Kiểm tra cột cho bảng users
    c.execute("PRAGMA table_info(users)")
    cols_users = [col[1] for col in c.fetchall()]
    if 'class_name' not in cols_users:
        c.execute("ALTER TABLE users ADD COLUMN class_name TEXT DEFAULT 'Chưa phân lớp'")
    if 'full_name' not in cols_users:
        c.execute("ALTER TABLE users ADD COLUMN full_name TEXT DEFAULT ''")

    # Tạo bảng kết quả
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, score REAL, 
                  correct_count INTEGER, wrong_count INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # Tài khoản Admin mặc định
    c.execute("INSERT OR REPLACE INTO users (username, password, role, class_name, full_name) VALUES ('admin', 'admin123', 'admin', 'Hệ thống', 'Quản trị viên')")
    conn.commit()
    conn.close()

def clean_username(input_str):
    if not input_str: return ""
    s = unicodedata.normalize('NFD', input_str)
    s = ''.join([c for c in s if unicodedata.category(c) != 'Mn'])
    s = s.replace('đ', 'd').replace('Đ', 'D')
    s = re.sub(r'[^a-zA-Z0-9]', '', s) 
    return s.lower()

# ==========================================
# PHẦN 2: TẠO ĐỀ THI (40 CÂU)
# ==========================================
def generate_histogram_base64(freqs):
    fig, ax = plt.subplots(figsize=(6, 3))
    bins = ['140-150', '150-160', '160-170', '170-180', '180-190']
    percents = [f / sum(freqs) * 100 for f in freqs]
    ax.bar(bins, percents, color='#3498db', edgecolor='black')
    ax.set_ylabel('Tỉ lệ (%)')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

class ExamGenerator:
    def __init__(self):
        self.exam = []

    def build_q(self, q_id, text, correct, distractors, hint, img_b64=None):
        options = [correct] + distractors
        random.shuffle(options)
        self.exam.append({"id": q_id, "question": text, "options": options, "answer": correct, "hint": hint, "image": img_b64})

    def generate_all(self):
        # 1. CĂN THỨC (6 câu)
        for i in range(1, 6):
            a = random.randint(2, 10)
            self.build_q(i, rf"Giá trị của $\sqrt{{{a**2}}}$ là:", rf"{a}", [rf"{-a}", rf"{a**2}", rf"{2*a}"], f"HD: $\sqrt{{A^2}} = |A|$.")
        self.build_q(6, r"Rút gọn $\frac{x\sqrt{y} + y\sqrt{x}}{\sqrt{xy}}$ ($x,y > 0$):", r"$\sqrt{x} + \sqrt{y}$", [r"$\sqrt{x} - \sqrt{y}$", r"$x + y$", r"$\sqrt{xy}$"], "HD: Đặt $\sqrt{xy}$ làm nhân tử chung.")
        # 2. HÀM SỐ (3 câu)
        self.build_q(7, r"Hàm số $y = -2x^2$ đồng biến khi:", r"$x < 0$", [r"$x > 0$", r"$x \in \mathbb{R}$", r"$x = 0$"], "HD: a < 0 nên đồng biến khi x < 0.")
        self.build_q(8, "Đỉnh Parabol $y = x^2$ là:", "(0; 0)", ["(1; 1)", "(0; 1)", "(1; 0)"], "HD: Đỉnh tại gốc tọa độ.")
        self.build_q(9, "Đồ thị hàm số $y = ax^2$ là đường gì?", "Parabol", ["Thẳng", "Tròn", "Elip"], "HD: Kiến thức cơ bản.")
        # 3. PHƯƠNG TRÌNH (8 câu)
        self.build_q(10, r"Hệ $\begin{cases} x+y=3 \\ x-y=1 \end{cases}$ có nghiệm:", "(2; 1)", ["(1; 2)", "(2; 2)", "(3; 0)"], "HD: Cộng đại số tìm x=2, y=1.")
        for i in range(11, 18):
            self.build_q(i, rf"Biệt thức $\Delta$ của $x^2 - {i}x + 1 = 0$:", rf"${i**2 - 4}$", [rf"${i**2 + 4}$", "0", "4"], "HD: $\Delta = b^2 - 4ac$.")
        # 4. BẤT PHƯƠNG TRÌNH (3 câu)
        self.build_q(18, "Nghiệm của $2x - 8 > 0$ là:", "x > 4", ["x < 4", "x > -4", "x < -4"], "HD: 2x > 8 => x > 4.")
        self.build_q(19, "Số nguyên lớn nhất thỏa mãn $x < 3.5$ là:", "3", ["4", "2", "3.5"], "HD: Số nguyên liền trước 3.5 là 3.")
        self.build_q(20, "Bất phương trình $mx+1>0$ bậc nhất khi:", "m ≠ 0", ["m = 0", "m > 0", "m < 0"], "HD: Hệ số a khác 0.")
        # 5. HỆ THỨC LƯỢNG (5 câu)
        for i in range(21, 26):
            self.build_q
