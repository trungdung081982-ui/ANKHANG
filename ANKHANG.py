import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# ==========================================
# PHẦN 1: KẾT NỐI CƠ SỞ DỮ LIỆU SQLITE (CẬP NHẬT)
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    # Bảng Lớp học
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (class_id INTEGER PRIMARY KEY AUTOINCREMENT, class_name TEXT UNIQUE)''')
    
    # Bảng Users (Thêm class_name để quản lý)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT, class_name TEXT)''')
    
    # Bảng Kết quả
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, score REAL, 
                  correct_count INTEGER, wrong_count INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tài khoản mặc định
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin', 'Hệ thống')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('hs1', '123', 'student', '9A1')")
    c.execute("INSERT OR IGNORE INTO classes (class_name) VALUES ('9A1')")
    conn.commit()
    conn.close()

# --- Giữ nguyên PHẦN 2 (generate_histogram_base64) và PHẦN 3 (ExamGenerator) như cũ của bạn ---
# (Tôi lược bớt hiển thị ở đây cho gọn, bạn vẫn giữ nguyên trong file của mình nhé)
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

class ExamGenerator:
    def __init__(self): self.exam = []
    def build_q(self, q_id, text, correct, distractors, hint, img_b64=None):
        options = [correct] + distractors
        random.shuffle(options)
        self.exam.append({"id": q_id, "question": text, "options": options, "answer": correct, "hint": hint, "image": img_b64})
    
    def generate_all(self):
        # ... (Toàn bộ logic 40 câu hỏi giữ nguyên như đoạn code trước) ...
        # [Phần này bạn copy lại y hệt từ câu trả lời trước của tôi nhé]
        for i in range(1, 41): self.build_q(i, f"Câu hỏi mẫu {i}", "A", ["B", "C", "D"], "Gợi ý") # Ví dụ tạm
        return self.exam

# ==========================================
# PHẦN 4: GIAO DIỆN CHÍNH
# ==========================================
def main():
    st.set_page_config(page_title="Quản lý Lớp học - Tuyên Quang", layout="wide")
    init_db()

    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'role' not in st.session_state: st.session_state.role = None

    # --- MÀN HÌNH ĐĂNG NHẬP ---
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
                else: st.error("Sai tài khoản!")
        return

    # --- SIDEBAR ---
    st.sidebar.write(f"👤: **{st.session_state.current_user}**")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    # ==========================
    # GIAO DIỆN ADMIN (CẬP NHẬT)
    # ==========================
    if st.session_state.role == 'admin':
        st.title("⚙️ QUẢN TRỊ VIÊN")
        tab1, tab2, tab3 = st.tabs(["📊 Thống kê kết quả", "🏫 Quản lý Lớp học", "👨‍🎓 Quản lý Học sinh"])

        with tab1:
            st.subheader("Bảng điểm học sinh")
            conn = sqlite3.connect('exam_db.sqlite')
            df_res = pd.read_sql_query('''
                SELECT r.username, u.class_name, r.score, r.timestamp 
                FROM results r JOIN users u ON r.username = u.username
                ORDER BY r.timestamp DESC''', conn)
            conn.close()
            st.dataframe(df_res, use_container_width=True)

        with tab2:
            st.subheader("Tạo lớp học mới")
            new_class = st.text_input("Tên lớp (VD: 9A1, 9B2...)")
            if st.button("Thêm lớp học"):
                if new_class:
                    try:
                        conn = sqlite3.connect('exam_db.sqlite')
                        conn.execute("INSERT INTO classes (class_name) VALUES (?)", (new_class,))
                        conn.commit()
                        conn.close()
                        st.success(f"Đã tạo lớp {new_class}")
                        st.rerun()
                    except: st.error("Lớp này đã tồn tại!")
            
            st.divider()
            st.subheader("Danh sách lớp hiện có")
            conn = sqlite3.connect('exam_db.sqlite')
            classes = pd.read_sql_query("SELECT * FROM classes", conn)
            conn.close()
            st.table(classes)

        with tab3:
            st.subheader("Thêm học sinh vào lớp")
            with st.form("add_student"):
                new_u = st.text_input("Tên đăng nhập học sinh")
                new_p = st.text_input("Mật khẩu mặc định", value="123")
                conn = sqlite3.connect('exam_db.sqlite')
                class_list = [row[0] for row in conn.execute("SELECT class_name FROM classes").fetchall()]
                conn.close()
                sel_class = st.selectbox("Chọn lớp", class_list)
                
                if st.form_submit_button("Tạo tài khoản học sinh"):
                    conn = sqlite3.connect('exam_db.sqlite')
                    conn.execute("INSERT INTO users VALUES (?, ?, 'student', ?)", (new_u, new_p, sel_class))
                    conn.commit()
                    conn.close()
                    st.success(f"Đã thêm học sinh {new_u} vào lớp {sel_class}")

    # ==========================
    # GIAO DIỆN HỌC SINH (GIỮ NGUYÊN)
    # ==========================
    else:
        st.title("📝 PHẦN THI CỦA HỌC SINH")
        # ... (Toàn bộ logic làm bài thi giữ nguyên như code trước của bạn) ...
        if st.button("🆕 BẮT ĐẦU LÀM ĐỀ 40 CÂU"):
            gen = ExamGenerator()
            st.session_state.exam_data = gen.generate_all()
            st.rerun()
        # Hiển thị câu hỏi, nộp bài... (giống hệt code cũ)

if __name__ == "__main__":
    main()
