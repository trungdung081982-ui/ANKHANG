import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# ==========================================
# PHẦS 1: KẾT NỐI CƠ SỞ DỮ LIỆU & TỰ SỬA LỖI
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    
    # Tạo bảng Lớp học (Cập nhật thêm cột teacher_name)
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (class_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  class_name TEXT UNIQUE, 
                  teacher_name TEXT DEFAULT 'Chưa phân công')''')
    
    # Kiểm tra và nâng cấp bảng classes nếu thiếu cột teacher_name
    c.execute("PRAGMA table_info(classes)")
    cols_classes = [col[1] for col in c.fetchall()]
    if 'teacher_name' not in cols_classes:
        c.execute("ALTER TABLE classes ADD COLUMN teacher_name TEXT DEFAULT 'Chưa phân công'")
    
    # Tạo bảng Users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # CƠ CHẾ CHỐNG LỖI: Tự động thêm cột class_name cho users nếu thiếu
    c.execute("PRAGMA table_info(users)")
    cols_users = [col[1] for col in c.fetchall()]
    if 'class_name' not in cols_users:
        c.execute("ALTER TABLE users ADD COLUMN class_name TEXT DEFAULT 'Chưa phân lớp'")
    
    # Tạo bảng Kết quả
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, score REAL, 
                  correct_count INTEGER, wrong_count INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Chèn Admin mặc định
    c.execute("INSERT OR REPLACE INTO users (username, password, role, class_name) VALUES ('admin', 'admin123', 'admin', 'Hệ thống')")
    conn.commit()
    conn.close()

# ==========================================
# PHẦN 2: HELPER VẼ BIỂU ĐỒ (CÂU 37)
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

# ==========================================
# PHẦN 3: TẠO 40 CÂU HỎI CHUẨN (LATEX)
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
            self.build_q(i, rf"Giá trị của biểu thức $\sqrt{{{a**2}}}$ là:", rf"{a}", [rf"{-a}", rf"{a**2}", rf"{2*a}"], rf"Áp dụng $\sqrt{{A^2}} = |A|$.")
        self.build_q(6, r"Rút gọn biểu thức $P = \frac{x\sqrt{y} + y\sqrt{x}}{\sqrt{xy}}$ với $x,y > 0$:", r"$\sqrt{x} + \sqrt{y}$", [r"$\sqrt{x} - \sqrt{y}$", r"$x + y$", r"$\sqrt{xy}$"], "Đặt nhân tử chung trên tử số.")

        # 2. HÀM SỐ Y=AX^2 (3 câu)
        self.build_q(7, r"Hàm số $y = -2x^2$ đồng biến khi:", r"$x < 0$", [r"$x > 0$", r"$x \in \mathbb{R}$", r"$x = 0$"], "Với a < 0, hàm số đồng biến khi x < 0.")
        self.build_q(8, r"Tọa độ đỉnh của Parabol $y = x^2$ là:", r"$(0; 0)$", [r"$(1; 1)$", r"$(0; 1)$", r"$(1; 0)$"], "Đồ thị luôn đi qua gốc tọa độ.")
        self.build_q(9, r"Hình dạng đồ thị hàm số $y = ax^2 (a \ne 0)$ là:", "Đường Parabol", ["Đường thẳng", "Đường tròn", "Đường Elip"], "Hàm bậc hai đồ thị là Parabol.")

        # 3. PHƯƠNG TRÌNH & HỆ (8 câu)
        self.build_q(10, r"Hệ phương trình $\begin{cases} x + y = 3 \\ x - y = 1 \end{cases}$ có nghiệm là:", r"$(2; 1)$", [r"$(1; 2)$", r"$(2; 2)$", r"$(3; 0)$"], "Sử dụng phương pháp cộng đại số.")
        for i in range(11, 18):
            self.build_q(i, rf"Biệt thức $\Delta$ của phương trình $x^2 - {i}x + 1 = 0$ là:", rf"${i**2 - 4}$", [rf"${i**2 + 4}$", rf"{i-4}", "0"], r"$\Delta = b^2 - 4ac$.")

        # 4. BẤT PHƯƠNG TRÌNH (3 câu)
        self.build_q(18, r"Nghiệm của $2x - 8 > 0$ là:", r"$x > 4$", [r"$x < 4$", r"$x > -4$", r"$x < -4$"], "Chuyển vế đổi dấu.")
        self.build_q(19, r"Giá trị nguyên lớn nhất thỏa mãn $x < 3.5$ là:", "3", ["4", "2", "3.5"], "Số nguyên đứng ngay trước 3.5.")
        self.build_q(20, "BPT $mx + 1 > 0$ là bậc nhất một ẩn khi:", r"$m \ne 0$", [r"$m = 0$", r"$m > 0$", r"$m < 0$"], "Hệ số a phải khác 0.")

        # 5. HỆ THỨC LƯỢNG (5 câu)
        for i in range(21, 26):
            self.build_q(i, rf"Trong $\triangle$ vuông, $\tan \alpha$ bằng:", r"$\frac{\text{Đối}}{\text{Kề}}$", [r"$\frac{\text{Kề}}{\text{Đối}}$", r"$\frac{\text{Đối}}{\text{Huyền}}$", r"$\frac{\text{Kề}}{\text{Huyền}}$"], "Tan = Đối / Kề.")

        # 6. ĐƯỜNG TRÒN (6 câu)
        self.build_q(26, "Góc nội tiếp chắn nửa đường tròn bằng:", r"$90^\circ$", [r"$180^\circ$", r"$45^\circ$", r"$60^\circ$"], "Góc nội tiếp chắn nửa đường tròn là góc vuông.")
        for i in range(27, 32):
            self.build_q(i, rf"Chu vi đường tròn có $R = {i}$ là:",
