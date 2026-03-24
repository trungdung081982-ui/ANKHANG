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

        # --- DÒNG 90: ĐÃ SỬA LỖI ---
        self.build_q(18, "Nghiệm của $2x - 8 > 0$ là:", "x > 4", ["x < 4", "x > -4", "x < -4"], "HD: 2x > 8 => x > 4.")
        
        self.build_q(19, "Số nguyên lớn nhất thỏa mãn $x < 3.5$ là:", "3", ["4", "2", "3.5"], "HD: Số nguyên liền trước 3.5 là 3.")
        self.build_q(20, "Bất phương trình $mx+1>0$ bậc nhất khi:", "m ≠ 0", ["m = 0", "m > 0", "m < 0"], "HD: Hệ số a khác 0.")
        for i in range(21, 26):
            self.build_q(i, "Tỉ số $\tan \alpha$ bằng:", "Đối / Kề", ["Kề / Đối", "Đối / Huyền", "Kề / Huyền"], "HD: Tan đoàn kết.")
        self.build_q(26, "Góc nội tiếp chắn nửa đường tròn bằng:", "90°", ["180°", "45°", "60°"], "HD: Là góc vuông.")
        for i in range(27, 32):
            self.build_q(i, rf"Chu vi đường tròn $R = {i}$ là:", rf"{2*i}π", [f"{i}π", f"{i**2}π", "20"], "HD: C = 2πR.")
        self.build_q(32, "Thể tích hình cầu bán kính R:", "4/3 π R³", ["4 π R²", "π R² h", "1/3 π R² h"], "HD: Công thức SGK.")
        self.build_q(33, "Diện tích xung quanh hình trụ:", "2πrh", ["πrh", "πr²h", "2πr"], "HD: Chu vi đáy x h.")
        self.build_q(34, "Hình nón r=3, h=4, đường sinh l:", "5", ["7", "1", "25"], "HD: l = √(r² + h²).")
        img37 = generate_histogram_base64([10, 20, 40, 20, 10])
        self.build_q(35, "Xác suất biến cố chắc chắn là:", "1", ["0", "0.5", "100"], "HD: Chắc chắn P=1.")
        self.build_q(37, "Nhóm có tỉ lệ cao nhất (40%) là:", "160-170", ["140-150", "150-160", "170-180"], "HD: Quan sát cột cao nhất.", img_b64=img37)
        for i in range(38, 41):
            self.build_q(i, f"Xác suất mặt {i%6+1} chấm xúc xắc:", "1/6", ["1/2", "1/3", "1"], "HD: 6 mặt đều nhau.")
        return self.exam

# ==========================================
# PHẦN 3: GIAO DIỆN CHÍNH
# ==========================================
def main():
    st.set_page_config(page_title="Hệ thống Thi Toán 10", layout="wide")
    init_db()

    if 'user' not in st.session_state: st.session_state.user = None
    if 'role' not in st.session_state: st.session_state.role = None
    if 'exam' not in st.session_state: st.session_state.exam = None
    if 'sub' not in st.session_state: st.session_state.sub = False

    if not st.session_state.user:
        st.title("🔑 ĐĂNG NHẬP")
        u_in = st.text_input("Tên đăng nhập")
        p_in = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập"):
            u_cl = clean_username(u_in)
            conn = sqlite3.connect('exam_db.sqlite')
            res = conn.execute("SELECT role FROM users WHERE username=? AND password=?", (u_cl, p_in)).fetchone()
            conn.close()
            if res:
                st.session_state.user, st.session_state.role = u_cl, res[0]
                st.rerun()
            else: st.error("Sai tài khoản hoặc mật khẩu!")
        return

    st.sidebar.write(f"Chào: **{st.session_state.user}**")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == 'admin':
        st.title("⚙️ QUẢN TRỊ VIÊN")
        t1, t2, t3 = st.tabs(["📊 Kết quả thi", "🏫 Lớp & Giáo viên", "👤 Tài khoản Học sinh"])
        
        with t2:
            st.subheader("Quản lý danh sách Lớp")
            with st.form("f_class"):
                c_n = st.text_input("Tên lớp")
                g_n = st.text_input("Tên giáo viên")
                if st.form_submit_button("Lưu lớp"):
                    if c_n and g_n:
                        conn = sqlite3.connect('exam_db.sqlite')
                        try:
                            conn.execute("INSERT INTO classes (class_name, teacher_name) VALUES (?,?)", (c_n, g_n))
                            conn.commit()
                            st.success(f"Đã tạo lớp {c_n}")
                            st.rerun()
                        except: st.error("Lớp đã tồn tại!")
                        conn.close()

            st.write("---")
            st.write("🗑️ **Xóa lớp học**")
            conn = sqlite3.connect('exam_db.sqlite')
            df_cls = pd.read_sql_query("SELECT class_name FROM classes", conn)
            conn.close()
            if not df_cls.empty:
                del_cls = st.selectbox("Chọn lớp muốn xóa", df_cls['class_name'])
                if st.button("Xác nhận xóa lớp", type="secondary"):
                    conn = sqlite3.connect('exam_db.sqlite')
                    conn.execute("DELETE FROM classes WHERE class_name=?", (del_cls,))
                    conn.commit()
                    conn.close()
                    st.warning(f"Đã xóa lớp {del_cls}")
                    st.rerun()

        with t3:
            st.subheader("Quản lý Học sinh")
            col_a, col_b = st.columns(2)
            with col_a:
                with st.form("f_student"):
                    h_t = st.text_input("Họ và tên học sinh")
                    h_p = st.text_input("Mật khẩu", "123")
                    conn = sqlite3.connect('exam_db.sqlite')
                    l_l = [r[0] for r in conn.execute("SELECT class_name FROM classes").fetchall()]
                    conn.close()
                    h_l = st.selectbox("Lớp", l_l if l_l else ["Trống"])
                    if st.form_submit_button("Tạo tài khoản"):
                        u_gen = clean_username(h_t)
                        if u_gen:
                            conn = sqlite3.connect('exam_db.sqlite')
                            try:
                                conn.execute("INSERT INTO users (username, password, role, class_name) VALUES (?,?,'student',?)", (u_gen, h_p, h_l))
                                conn.commit()
                                st.success(f"Đã tạo: {u_gen}")
                                st.rerun()
                            except: st.error("Tên đăng nhập đã tồn tại!")
                            conn.close()

            with col_b:
                st.markdown("**📂 Xuất dữ liệu & Xóa học sinh**")
                conn = sqlite3.connect('exam_db.sqlite')
                df_hs = pd.read_sql_query("SELECT username as 'Tên đăng nhập', password as 'Mật khẩu', class_name as 'Lớp' FROM users WHERE role='student'", conn)
                conn.close()
                if not df_hs.empty:
                    try:
                        out_ex = BytesIO()
                        with pd.ExcelWriter(out_ex, engine='xlsxwriter') as writer:
                            df_hs.to_excel(writer, index=False, sheet_name='TaiKhoan')
                        st.download_button("📥 Tải File Excel (.xlsx)", out_ex.getvalue(), "ds_taikhoan.xlsx", "application/vnd.ms-excel")
                    except:
                        csv = df_hs.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 Tải File CSV", csv, "ds_taikhoan.csv", "text/csv")
                    
                    st.write("---")
                    del_user = st.selectbox("Chọn tài khoản xóa", df_hs['Tên đăng nhập'])
                    if st.button("Xóa tài khoản này", type="secondary"):
                        conn = sqlite3.connect('exam_db.sqlite')
                        conn.execute("DELETE FROM users WHERE username=?", (del_user,))
                        conn.commit()
                        conn.close()
                        st.warning(f"Đã xóa tài khoản {del_user}")
                        st.rerun()

        with t1:
            conn = sqlite3.connect('exam_db.sqlite')
            st.dataframe(pd.read_sql_query("SELECT r.username as 'Tên HS', u.class_name as 'Lớp', r.score as 'Điểm', r.timestamp as 'Thời gian' FROM results r JOIN users u ON r.username = u.username ORDER BY r.timestamp DESC", conn), use_container_width=True)
            conn.close()

    else:
        st.title("📝 LUYỆN THI VÀO 10")
        if st.button("🆕 LÀM ĐỀ THI MỚI (40 CÂU)", type="primary"):
            st.session_state.exam = ExamGenerator().generate_all()
            st.session_state.sub = False
            st.rerun()
        if st.session_state.exam:
            for i, q in enumerate(st.session_state.exam):
                st.write(f"**Câu {i+1}:** {q['question']}")
                if q['image']: st.image(f"data:image/png;base64,{q['image']}")
                ans = st.radio("Chọn:", q['options'], key=f"q{i}", disabled=st.session_state.sub)
                if st.session_state.sub:
                    if ans == q['answer']: st.success("Đúng ✅")
                    else:
                        st.error(f"Sai ❌. Đáp án: {q['answer']}")
                        st.info(f"💡 {q['hint']}")
                st.divider()
            if not st.session_state.sub and st.button("🎯 NỘP BÀI"):
                corr = sum(1 for i, q in enumerate(st.session_state.exam) if st.session_state[f"q{i}"] == q['answer'])
                score = round((corr/40)*10, 2)
                conn = sqlite3.connect('exam_db.sqlite')
                conn.execute("INSERT INTO results (username, score, correct_count, wrong_count) VALUES (?,?,?,?)", (st.session_state.user, score, corr, 40-corr))
                conn.commit()
                conn.close()
                st.session_state.sub = True
                st.balloons()
                st.rerun()

if __name__ == "__main__":
    main()
