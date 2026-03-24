import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# ==========================================
# PHẦN 1: KẾT NỐI CƠ SỞ DỮ LIỆU & TỰ SỬA LỖI
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    
    # Tạo bảng Lớp học
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (class_id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT UNIQUE)''')
    
    # Tạo bảng Users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # CƠ CHẾ CHỐNG LỖI: Tự động thêm cột class_name nếu bản cũ chưa có
    c.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in c.fetchall()]
    if 'class_name' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN class_name TEXT DEFAULT 'Chưa phân lớp'")
    
    # Tạo bảng Kết quả
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, score REAL, 
                  correct_count INTEGER, wrong_count INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Chèn Admin mặc định (Dùng REPLACE để cập nhật nếu đã có)
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
            self.build_q(i, rf"Chu vi đường tròn có $R = {i}$ là:", rf"${2*i}\pi$", [rf"${i}\pi$", rf"${i**2}\pi$", rf"{2*i}"], r"$C = 2\pi R$.")

        # 7. HÌNH KHỐI (3 câu)
        self.build_q(32, r"Thể tích hình cầu bán kính $R$:", r"$\frac{4}{3}\pi R^3$", [r"$4\pi R^2$", r"$\pi R^2 h$", r"$\frac{1}{3}\pi R^2 h$"], "Công thức SGK.")
        self.build_q(33, r"Diện tích xung quanh hình trụ $r, h$:", r"$2\pi rh$", [r"$\pi rh$", r"$\pi r^2 h$", r"$2\pi r$"], "Chu vi đáy nhân chiều cao.")
        self.build_q(34, "Hình nón có $r=3, h=4$, đường sinh $l$ bằng:", "5", ["7", "1", "25"], r"$l = \sqrt{r^2 + h^2}$.")

        # 8. THỐNG KÊ (6 câu)
        img37 = generate_histogram_base64([10, 20, 40, 20, 10])
        self.build_q(35, "Xác suất của biến cố chắc chắn là:", "1", ["0", "0.5", "100"], "Biến cố chắc chắn có xác suất bằng 1.")
        self.build_q(37, "Dựa vào biểu đồ, nhóm nào có tỉ lệ cao nhất (40%)?", "160-170", ["140-150", "150-160", "170-180"], "Nhìn vào cột cao nhất.", img_b64=img37)
        for i in range(38, 41):
            self.build_q(i, rf"Gieo một con xúc xắc, xác suất xuất hiện mặt {i%6 + 1} chấm là:", r"$\frac{1}{6}$", [r"$\frac{1}{2}$", r"$\frac{1}{3}$", "1"], "Xúc xắc có 6 mặt bằng nhau.")

        return self.exam

# ==========================================
# PHẦN 4: GIAO DIỆN CHÍNH
# ==========================================
def main():
    st.set_page_config(page_title="Hệ thống Ôn thi vào 10", layout="wide")
    init_db()

    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'exam_data' not in st.session_state: st.session_state.exam_data = None
    if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

    # --- ĐĂNG NHẬP ---
    if st.session_state.current_user is None:
        st.title("🔑 ĐĂNG NHẬP")
        with st.form("login"):
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Vào hệ thống"):
                conn = sqlite3.connect('exam_db.sqlite')
                res = conn.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p)).fetchone()
                conn.close()
                if res:
                    st.session_state.current_user = u
                    st.session_state.role = res[0]
                    st.rerun()
                else: st.error("Sai tài khoản hoặc mật khẩu!")
        return

    # Sidebar
    st.sidebar.title(f"Chào, {st.session_state.current_user}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    # --- GIAO DIỆN ADMIN ---
    if st.session_state.role == 'admin':
        st.title("⚙️ QUẢN TRỊ VIÊN")
        t1, t2, t3 = st.tabs(["📊 Kết quả thi", "🏫 Quản lý Lớp", "👤 Quản lý Học sinh"])
        
        with t1:
            conn = sqlite3.connect('exam_db.sqlite')
            df = pd.read_sql_query('''SELECT r.username, u.class_name, r.score, r.timestamp 
                                      FROM results r JOIN users u ON r.username = u.username''', conn)
            conn.close()
            st.dataframe(df, use_container_width=True)

        with t2:
            st.subheader("Tạo lớp mới")
            nc = st.text_input("Nhập tên lớp")
            if st.button("Lưu lớp"):
                conn = sqlite3.connect('exam_db.sqlite')
                try:
                    conn.execute("INSERT INTO classes (class_name) VALUES (?)", (nc,))
                    conn.commit()
                    st.success("Đã thêm thành công!")
                except: st.error("Lớp đã tồn tại")
                conn.close()
                st.rerun()

        with t3:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("➕ Thêm học sinh")
                with st.form("add_hs"):
                    nu = st.text_input("Tên đăng nhập")
                    np = st.text_input("Mật khẩu", "123")
                    conn = sqlite3.connect('exam_db.sqlite')
                    c_list = [r[0] for r in conn.execute("SELECT class_name FROM classes").fetchall()]
                    conn.close()
                    ncl = st.selectbox("Chọn lớp", c_list if c_list else ["Chưa có lớp"])
                    if st.form_submit_button("Tạo tài khoản"):
                        conn = sqlite3.connect('exam_db.sqlite')
                        try:
                            conn.execute("INSERT INTO users (username, password, role, class_name) VALUES (?, ?, 'student', ?)", (nu, np, ncl))
                            conn.commit()
                            st.success("Đã tạo!")
                        except: st.error("Tên đã tồn tại")
                        conn.close()

            with col2:
                st.subheader("🔑 Đổi mật khẩu học sinh")
                with st.form("change_p"):
                    conn = sqlite3.connect('exam_db.sqlite')
                    list_hs = [r[0] for r in conn.execute("SELECT username FROM users WHERE role='student'").fetchall()]
                    conn.close()
                    target = st.selectbox("Chọn học sinh", list_hs)
                    new_p = st.text_input("Mật khẩu mới", type="password")
                    if st.form_submit_button("Cập nhật mật khẩu"):
                        conn = sqlite3.connect('exam_db.sqlite')
                        conn.execute("UPDATE users SET password=? WHERE username=?", (new_p, target))
                        conn.commit()
                        conn.close()
                        st.success(f"Đã đổi mật khẩu cho {target}!")

    # --- GIAO DIỆN HỌC SINH ---
    else:
        st.title("📝 BÀI THI TOÁN VÀO 10")
        if st.button("🆕 BẮT ĐẦU LÀM ĐỀ 40 CÂU", type="primary"):
            st.session_state.exam_data = ExamGenerator().generate_all()
            st.session_state.is_submitted = False
            st.rerun()

        if st.session_state.exam_data:
            for idx, q in enumerate(st.session_state.exam_data):
                st.markdown(f"**Câu {idx+1}:** {q['question']}")
                if q['image']: st.image(f"data:image/png;base64,{q['image']}")
                key = f"q_{idx}"
                st.radio("Chọn đáp án:", q['options'], key=key, disabled=st.session_state.is_submitted)
                if st.session_state.is_submitted:
                    if st.session_state[key] == q['answer']: st.success("Đúng ✅")
                    else: st.error(f"Sai ❌. Đáp án đúng: {q['answer']}")
                st.divider()

            if not st.session_state.is_submitted:
                if st.button("🎯 NỘP BÀI"):
                    correct = sum(1 for i, q in enumerate(st.session_state.exam_data) if st.session_state[f"q_{i}"] == q['answer'])
                    score = (correct/40)*10
                    conn = sqlite3.connect('exam_db.sqlite')
                    conn.execute("INSERT INTO results (username, score, correct_count, wrong_count) VALUES (?, ?, ?, ?)", 
                                 (st.session_state.current_user, score, correct, 40-correct))
                    conn.commit()
                    conn.close()
                    st.session_state.is_submitted = True
                    st.balloons()
                    st.rerun()

if __name__ == "__main__":
    main()
