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
# PHẦN 1: KẾT NỐI CƠ SỞ DỮ LIỆU & TỰ SỬA LỖI
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (class_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  class_name TEXT UNIQUE, 
                  teacher_name TEXT DEFAULT 'Chưa phân công')''')
    
    c.execute("PRAGMA table_info(classes)")
    cols_classes = [col[1] for col in c.fetchall()]
    if 'teacher_name' not in cols_classes:
        c.execute("ALTER TABLE classes ADD COLUMN teacher_name TEXT DEFAULT 'Chưa phân công'")
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT, class_name TEXT DEFAULT 'Chưa phân lớp')''')
    
    c.execute("PRAGMA table_info(users)")
    cols_users = [col[1] for col in c.fetchall()]
    if 'class_name' not in cols_users:
        c.execute("ALTER TABLE users ADD COLUMN class_name TEXT DEFAULT 'Chưa phân lớp'")
    
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, score REAL, 
                  correct_count INTEGER, wrong_count INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute("INSERT OR REPLACE INTO users (username, password, role, class_name) VALUES ('admin', 'admin123', 'admin', 'Hệ thống')")
    conn.commit()
    conn.close()

# Hàm xử lý tên đăng nhập không dấu, viết liền
def remove_accents_and_spaces(input_str):
    if not input_str: return ""
    s = unicodedata.normalize('NFD', input_str)
    s = ''.join([c for c in s if unicodedata.category(c) != 'Mn'])
    s = s.replace('đ', 'd').replace('Đ', 'D')
    s = re.sub(r'[^a-zA-Z0-9]', '', s) # Loại bỏ ký tự đặc biệt và khoảng trắng
    return s.lower()

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
# PHẦN 3: TẠO 40 CÂU HỎI CHUẨN KÈM HƯỚNG DẪN
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
            self.build_q(i, rf"Giá trị của biểu thức $\sqrt{{{a**2}}}$ là:", rf"{a}", [rf"{-a}", rf"{a**2}", rf"{2*a}"], rf"Hướng dẫn: Áp dụng hằng đẳng thức $\sqrt{{A^2}} = |A|$. Kết quả là {a}.")
        self.build_q(6, r"Rút gọn biểu thức $P = \frac{x\sqrt{y} + y\sqrt{x}}{\sqrt{xy}}$ ($x,y > 0$):", r"$\sqrt{x} + \sqrt{y}$", [r"$\sqrt{x} - \sqrt{y}$", r"$x + y$", r"$\sqrt{xy}$"], "Hướng dẫn: Đặt nhân tử chung $\sqrt{xy}$ trên tử số để rút gọn.")

        # 2. HÀM SỐ (3 câu)
        self.build_q(7, r"Hàm số $y = -2x^2$ đồng biến khi:", r"$x < 0$", [r"$x > 0$", r"$x \in \mathbb{R}$", r"$x = 0$"], "Hướng dẫn: Với a < 0, hàm số đồng biến khi x < 0.")
        self.build_q(8, r"Tọa độ đỉnh của Parabol $y = x^2$ là:", r"$(0; 0)$", [r"$(1; 1)$", r"$(0; 1)$", r"$(1; 0)$"], "Hướng dẫn: Đỉnh Parabol cơ bản tại O(0;0).")
        self.build_q(9, r"Đồ thị hàm số $y = ax^2 (a \ne 0)$ là đường gì?", "Parabol", ["Đường thẳng", "Đường tròn", "Đường Elip"], "Hướng dẫn: Đây là kiến thức cơ bản về hàm bậc 2.")

        # 3. PHƯƠNG TRÌNH & HỆ (8 câu)
        self.build_q(10, r"Hệ $\begin{cases} x+y=3 \\ x-y=1 \end{cases}$ có nghiệm:", r"$(2; 1)$", [r"$(1; 2)$", r"$(2; 2)$", r"$(3; 0)$"], "Hướng dẫn: Sử dụng phương pháp cộng đại số tìm x=2, y=1.")
        for i in range(11, 18):
            self.build_q(i, rf"Biệt thức $\Delta$ của $x^2 - {i}x + 1 = 0$ là:", rf"${i**2 - 4}$", [rf"${i**2 + 4}$", rf"{i-4}", "0"], rf"Hướng dẫn: Tính theo công thức $\Delta = b^2 - 4ac$.")

        # 4. BẤT PHƯƠNG TRÌNH (3 câu)
        self.build_q(18, r"Nghiệm của $2x - 8 > 0$ là:", r"$x > 4$", [r"$x < 4$", r"$x > -4$", r"$x < -4$"], "Hướng dẫn: $2x > 8$ tương đương $x > 4$.")
        self.build_q(19, r"Số nguyên lớn nhất thỏa mãn $x < 3.5$ là:", "3", ["4", "2", "3.5"], "Hướng dẫn: Số nguyên lớn nhất bé hơn 3.5 là 3.")
        self.build_q(20, r"Điều kiện để $mx+1>0$ là BPT bậc nhất một ẩn:", r"$m \ne 0$", [r"$m = 0$", r"$m > 0$", r"$m < 0$"], "Hướng dẫn: Hệ số m phải khác 0.")

        # 5. HỆ THỨC LƯỢNG (5 câu)
        for i in range(21, 26):
            self.build_q(i, rf"Trong $\triangle$ vuông, tỉ số $\tan \alpha$ bằng:", r"$\frac{\text{Đối}}{\text{Kề}}$", [r"$\frac{\text{Kề}}{\text{Đối}}$", r"$\frac{\text{Đối}}{\text{Huyền}}$", r"$\frac{\text{Kề}}{\text{Huyền}}$"], "Hướng dẫn: Tan = Đối / Kề.")

        # 6. ĐƯỜNG TRÒN (6 câu)
        self.build_q(26, "Góc nội tiếp chắn nửa đường tròn bằng:", r"$90^\circ$", [r"$180^\circ$", r"$45^\circ$", r"$60^\circ$"], "Hướng dẫn: Góc nội tiếp chắn nửa đường tròn là góc vuông.")
        for i in range(27, 32):
            self.build_q(i, rf"Chu vi đường tròn bán kính $R = {i}$ là:", rf"${2*i}\pi$", [rf"${i}\pi$", rf"${i**2}\pi$", rf"{2*i}"], rf"Hướng dẫn: $C = 2\pi R$.")

        # 7. HÌNH KHỐI (3 câu)
        self.build_q(32, r"Thể tích hình cầu bán kính $R$:", r"$\frac{4}{3}\pi R^3$", [r"$4\pi R^2$", r"$\pi R^2 h$", r"$\frac{1}{3}\pi R^2 h$"], "Hướng dẫn: Công thức tính thể tích cầu.")
        self.build_q(33, r"Diện tích xung quanh hình trụ:", r"$2\pi rh$", [r"$\pi rh$", r"$\pi r^2 h$", r"$2\pi r$"], "Hướng dẫn: Chu vi đáy nhân chiều cao.")
        self.build_q(34, "Hình nón $r=3, h=4$, đường sinh $l$ bằng:", "5", ["7", "1", "25"], r"Hướng dẫn: $l = \sqrt{r^2 + h^2}$.")

        # 8. THỐNG KÊ (6 câu)
        img37 = generate_histogram_base64([10, 20, 40, 20, 10])
        self.build_q(35, "Xác suất của biến cố chắc chắn là:", "1", ["0", "0.5", "100"], "Hướng dẫn: Biến cố chắc chắn có xác suất bằng 1.")
        self.build_q(37, "Nhóm có tỉ lệ cao nhất (40%) trên biểu đồ là:", "160-170", ["140-150", "150-160", "170-180"], "Hướng dẫn: Nhìn cột cao nhất trên biểu đồ.", img_b64=img37)
        for i in range(38, 41):
            self.build_q(i, rf"Xác suất gieo xúc xắc được mặt {i%6 + 1} chấm là:", r"$\frac{1}{6}$", [r"$\frac{1}{2}$", r"$\frac{1}{3}$", "1"], "Hướng dẫn: Xúc xắc có 6 mặt bằng nhau.")

        return self.exam

# ==========================================
# PHẦN 4: GIAO DIỆN CHÍNH
# ==========================================
def main():
    st.set_page_config(page_title="Hệ thống thi thử 10", layout="wide")
    init_db()

    if 'current_user'
