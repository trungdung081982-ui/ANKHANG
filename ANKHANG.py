import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# ==========================================
# PHẦN 1: KẾT NỐI CƠ SỞ DỮ LIỆU & SỬA LỖI
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    
    # 1. Tạo bảng Lớp học
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (class_id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT UNIQUE)''')
    
    # 2. Tạo bảng Users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # Tự động nâng cấp cột nếu thiếu (Tránh lỗi OperationalError)
    c.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in c.fetchall()]
    if 'class_name' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN class_name TEXT DEFAULT 'Chưa phân lớp'")
    
    # 3. Tạo bảng Kết quả
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, score REAL, 
                  correct_count INTEGER, wrong_count INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # 4. Tài khoản Admin mặc định
    c.execute("INSERT OR REPLACE INTO users (username, password, role, class_name) VALUES ('admin', 'admin123', 'admin', 'Hệ thống')")
    conn.commit()
    conn.close()

# ==========================================
# PHẦN 2: HELPER VẼ BIỂU ĐỒ (CHO CÂU 37)
# ==========================================
def generate_histogram_base64(freqs):
    fig, ax = plt.subplots(figsize=(6, 3))
    bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
    percents = [f / sum(freqs) * 100 for f in freqs]
    ax.bar(bins, percents, color='#f28e2b', edgecolor='black')
    ax.set_ylabel('Tỉ lệ (%)')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# ==========================================
# PHẦN 3: TẠO 40 CÂU HỎI THEO MA TRẬN TOÁN 10
# ==========================================
class ExamGenerator:
    def __init__(self):
        self.exam = []

    def build_q(self, q_id, text, correct, distractors, hint, img_b64=None):
        options = [correct] + distractors
        random.shuffle(options)
        self.exam.append({
            "id": q_id, "question": text, "options": options,
            "answer": correct, "hint": hint, "image": img_b64
        })

    def generate_all(self):
        # 1. CĂN THỨC (6 câu)
        for i in range(1, 6):
            a = random.randint(2, 10)
            self.build_q(i, rf"Giá trị của $\sqrt{{{a**2}}}$ là:", rf"{a}", [rf"{-a}", rf"{a**2}", rf"{2*a}"], r"Sử dụng $\sqrt{A^2} = |A|$.")
        self.build_q(6, r"Rút gọn $P = \frac{x\sqrt{y} + y\sqrt{x}}{\sqrt{xy}} : \frac{1}{\sqrt{x}-\sqrt{y}}$:", r"$x - y$", [r"$y - x$", r"$\sqrt{x}-\sqrt{y}$", r"$x+y$"], "Rút gọn rồi nhân nghịch đảo.")

        # 2. HÀM SỐ & PARABOL (3 câu)
        self.build_q(7, r"Hàm số $y = -2x^2$ đồng biến khi:", r"$x < 0$", [r"$x > 0$", r"$x \in \mathbb{R}$", "Khi x = 0"], "a < 0 đồng biến khi x < 0.")
        self.build_q(8, r"Tọa độ đỉnh của Parabol $y = x^2$ là:", r"$(0; 0)$", [r"$(1; 1)$", r"$(0; 1)$", r"$(1; 0)$"], "Đồ thị luôn đi qua gốc tọa độ.")
        self.build_q(9, r"Hàm số $y = (m-1)x^2$ là hàm bậc hai khi:", r"$m \ne 1$", [r"$m = 1$", r"$m > 1$", r"$m < 1$"], "Hệ số a phải khác 0.")

        # 3. PHƯƠNG TRÌNH & HỆ (8 câu)
        self.build_q(10, r"Hệ $\begin{cases} x+y=3 \\ x-y=1 \end{cases}$ có nghiệm $(x;y)$ là:", r"$(2; 1)$", [r"$(1; 2)$", r"$(3; 0)$", r"$(2; -1)$"], "Cộng đại số tìm x=2.")
        for i in range(11, 18):
            self.build_q(i, rf"Biệt thức $\Delta$ của phương trình $x^
