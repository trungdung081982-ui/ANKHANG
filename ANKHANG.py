import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# ==========================================
# PHẦN 1: KẾT NỐI CƠ SỞ DỮ LIỆU (SỬA LỖI CỘT)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    
    # 1. Tạo bảng Lớp học
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (class_id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT UNIQUE)''')
    
    # 2. Tạo bảng Users (Khởi tạo ban đầu)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # --- CƠ CHẾ TỰ SỬA LỖI: Kiểm tra và thêm cột class_name nếu chưa có ---
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
    
    # 4. Chèn dữ liệu mặc định (Dùng INSERT OR REPLACE để tránh lỗi trùng khóa)
    c.execute("INSERT OR REPLACE INTO users (username, password, role, class_name) VALUES ('admin', 'admin123', 'admin', 'Hệ thống')")
    c.execute("INSERT OR IGNORE INTO classes (class_name) VALUES ('9A1')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role, class_name) VALUES ('hs1', '123', 'student', '9A1')")
    
    conn.commit()
    conn.close()

# ==========================================
# PHẦN 2: HELPER VẼ BIỂU ĐỒ
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
# PHẦN 3: TẠO 40 CÂU HỎI THEO MA TRẬN
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
        for i in range(1, 7):
            a = random.randint(2, 10)
            if i == 1:
                self.build_q(1, rf"Điều kiện xác định của biểu thức $\sqrt{{x-{a}}}$ là:", rf"$x \ge {a}$", [rf"$x > {a}$", rf"$x \le {a}$", rf"$x < {a}$"], "Biểu thức trong căn không âm.")
            elif i == 6:
                self.build_q(6, r"Rút gọn $P = \frac{x\sqrt{y} + y\sqrt{x}}{\sqrt{xy}} : \frac{1}{\sqrt{x}-\sqrt{y}}$:", r"$x - y$", [r"$y - x$", r"$\sqrt{x}-\sqrt{y}$", r"$x+y$"], "Rút gọn rồi nhân nghịch đảo.")
            else:
                self.build_q(i, rf"Giá trị của $\sqrt{{{a**2}}}$ là:", rf"{a}", [rf"{-a}", rf"{a**2}", rf"{2*a}"], r"$\sqrt{A^2} = |A|$.")

        # 2. HÀM SỐ Y=AX^2 (3 câu)
        self.build_q(7, r"Hàm số $y = -2x^2$ đồng biến khi:", r"$x < 0$", [r"$x > 0$", r"$x \in \mathbb{R}$", r"$x = 0$"], "a < 0 đồng biến khi x < 0.")
        self.build_q(8, r"Điểm nào thuộc đồ thị $y = x^2$?", r"$(2; 4)$", [r"$(2; 2)$", r"$(1; 2)$", r"$(4; 2)$"], "Thay x vào tìm y.")
        self.build_q(9, r"Đồ thị $y = ax^2 (a \ne 0)$ là một đường:", "Parabol", ["Thẳng", "Tròn", "Cung"], "Hình dạng đồ thị hàm bậc 2.")

        # 3. PHƯƠNG TRÌNH & HỆ (8 câu)
        self.build_q(10, r"Hệ $\begin{cases} x+y=3 \\ x-y=1 \end{cases}$ có nghiệm:", r"$(2; 1)$", [r"$(1; 2)$", r"$(2; 2)$", r"$(0; 3)$"], "Giải bằng phương pháp cộng.")
        for i in range(11, 18):
            self.build_q(i, rf"Biệt thức $\Delta$ của $x^2 - {i}x + 1 = 0$ là:", rf"${i**2 - 4}$", [rf"${i**2 + 4}$", rf"{i-4}", "0"], r"$\Delta = b^2 - 4ac$.")

        # 4. BẤT PHƯƠNG TRÌNH (3 câu)
        self.build_q(18, r"Nghiệm của $2x - 4 > 0$ là:", r"$x > 2$", [r"$x < 2$", r"$x > -2$", r"$x < -2$"], "Chuyển vế đổi dấu.")
        self.build_q(19, r"Số nguyên lớn nhất thỏa mãn $x < 5.5$ là:", "5", ["6", "4", "5.5"], "Số nguyên đứng ngay trước 5.5.")
        self.build_q(20, "BPT bậc nhất một ẩn có dạng:", r"$ax + b > 0 (a \ne 0)$", ["$ax^2 + b = 0$", "$x + y = 0$", "$1/x > 0$"], "Định nghĩa BPT bậc nhất.")

        # 5. HỆ THỨC LƯỢNG (5 câu)
        for i in range(21, 26):
            self.build_q(i, rf"Trong $\triangle$ vuông, nếu cạnh huyền là {i*2} và góc kề là $60^\circ$, cạnh kề đó là:", rf"{i}", [rf"{i*2}", rf"{i}\sqrt{{3}}", rf"{i}/2"], r"Cạnh kề = Huyền $\cdot \cos 60^\circ$.")

        # 6. ĐƯỜNG TRÒN (6 câu)
        self.build_q(26, "Góc nội tiếp chắn nửa đường tròn bằng:", r"$90^\circ$", [r"$180^\circ$", r"$60^\circ$", r"$45^\circ$"], "Tính chất góc nội tiếp.")
        for i in range(27, 32):
            self.build_q(i, rf"Diện tích hình tròn có $R = {i}$ là:", rf"${i**2}\pi$", [rf"${2*i}\pi$", rf"${i}\pi$", rf"{i**2}"], r"$S = \pi R^2$.")

        # 7. HÌNH KHỐI (3 câu)
        self.build_q(32, r"Thể tích hình cầu bán kính $R$:", r"$\frac{4}{3}\pi R^3$", [r"$4\pi R^2$", r"$\pi R^2 h$", r"$\frac{1}{3}\pi R^2 h$"], "Công thức SGK.")
        self.build_q(33, r"Diện tích xung quanh hình trụ:", r"$2\pi rh$", [r"$\pi rh$", r"$\pi r^2 h$", r"$2\pi r$"], "Chu vi đáy nhân chiều cao.")
        self.build_q(34, "Hình nón có $r=3, h=4$, đường sinh $l$ bằng:", "5", ["7", "1", "25"], r"$l = \sqrt{r^2 + h^2}$.")

        # 8. THỐNG KÊ & XÁC SUẤT (6 câu)
        img37 = generate_histogram_base64([10, 20, 40, 20, 10])
        self.build_q(35, "Biến cố không thể có xác suất bằng:", "0", ["1", "0.5", "-1"], "Xác suất luôn từ 0 đến 1.")
        self.build_q(37, "Dựa vào biểu đồ, nhóm chiếm tỉ lệ 40% là:", "[160;170)", ["[140;150)", "[170;180)", "[180;190)"], "Xem cột cao nhất.", img_b64=img37)
        for i in range(38, 41):
            self.build_q(i, rf"Xác suất lấy được thẻ số chẵn từ bộ 1 đến {i*2} là:", r"$\frac{1}{2}$", [r"$\frac{1}{3}$", r"$\frac{1}{4}$", "1"], "Số lượng số chẵn bằng số lượng số lẻ.")

        return self.exam

# ==========================================
# PHẦN 4: GIAO DIỆN CHÍNH
# ==========================================
def main():
    st.set_page_config(page_title="Hệ thống Ôn thi 10", layout="wide")
    init_db()

    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None
    if 'exam_data' not in st.session_state: st.session_state.exam_data = None
    if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

    # --- ĐĂNG NHẬP ---
    if st.session_state.current_user is None:
        st.title("🚀 HỆ THỐNG ÔN THI VÀO 10")
        with st.form("login_form"):
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Đăng nhập"):
                conn = sqlite3.connect('exam_db.sqlite')
                res = conn.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p)).fetchone()
                conn.close()
                if res:
                    st.session_state.current_user = u
                    st.session_state.role = res[0]
                    st.rerun()
                else: st.error("Sai tài khoản hoặc mật khẩu!")
        return

    # --- SIDEBAR ---
    st.sidebar.title(f"Xin chào, {st.session_state.current_user}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    # --- GIAO DIỆN ADMIN ---
    if st.session_state.role == 'admin':
        st.title("💎 QUẢN TRỊ VIÊN")
        t1, t2, t3 = st.tabs(["📊 Kết quả thi", "🏫 Lớp học", "👤 Học sinh"])
        
        with t1:
            conn = sqlite3.connect('exam_db.sqlite')
            df = pd.read_sql_query("SELECT r.username, u.class_name, r.score, r.timestamp FROM results r JOIN users u ON r.username = u.username", conn)
            conn.close()
            st.dataframe(df, use_container_width=True)
            
        with t2:
            new_c = st.text_input("Tên lớp mới")
            if st.button("Lưu lớp"):
                conn = sqlite3.connect('exam_db.sqlite')
                try:
                    conn.execute("INSERT INTO classes (class_name) VALUES (?)", (new_c,))
                    conn.commit()
                    st.success("Đã thêm lớp!")
                except: st.warning("Lớp đã tồn tại")
                conn.close()
                st.rerun()
                
        with t3:
            with st.form("add_hs"):
                nu = st.text_input("Tên HS")
                np = st.text_input("Mật khẩu", "123")
                conn = sqlite3.connect('exam_db.sqlite')
                c_list = [r[0] for r in conn.execute("SELECT class_name FROM classes").fetchall()]
                conn.close()
                nc = st.selectbox("Chọn lớp", c_list if c_list else ["Chưa có lớp"])
                if st.form_submit_button("Tạo HS"):
                    conn = sqlite3.connect('exam_db.sqlite')
                    conn.execute("INSERT INTO users (username, password, role, class_name) VALUES (?, ?, 'student', ?)", (nu, np, nc))
                    conn.commit()
                    conn.close()
                    st.success("Xong!")

    # --- GIAO DIỆN HỌC SINH ---
    else:
        st.title("✍️ BÀI THI TOÁN (40 CÂU)")
        if st.button("🆕 BẮT ĐẦU LÀM ĐỀ MỚI", type="primary"):
            st.session_state.exam_data = ExamGenerator().generate_all()
            st.session_state.is_submitted = False
            st.rerun()

        if st.session_state.exam_data:
            for idx, q in enumerate(st.session_state.exam_data):
                st.write(f"**Câu {idx+1}:** {q['question']}")
                if q['image']: st.image(f"data:image/png;base64,{q['image']}")
                key = f"q_{idx}"
                st.radio("Chọn đáp án:", q['options'], key=key, disabled=st.session_state.is_submitted)
                if st.session_state.is_submitted:
                    if st.session_state[key] == q['answer']: st.success("Đúng")
                    else: st.error(f"Sai. Đáp án: {q['answer']}")
                st.divider()

            if not st.session_state.is_submitted:
                if st.button("🎯 NỘP BÀI"):
                    correct = sum(1 for idx, q in enumerate(st.session_state.exam_data) if st.session_state[f"q_{idx}"] == q['answer'])
                    score = (correct/40)*10
                    conn = sqlite3.connect('exam_db.sqlite')
                    conn.execute("INSERT INTO results (username, score, correct_count, wrong_count) VALUES (?, ?, ?, ?)", 
                                 (st.session_user, score, correct, 40-correct))
                    conn.commit()
                    conn.close()
                    st.session_state.is_submitted = True
                    st.rerun()

if __name__ == "__main__":
    main()
