import streamlit as st
import random
import math
import pandas as pd
import sqlite3
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# ==========================================
# PHẦN 1: KẾT NỐI CƠ SỞ DỮ LIỆU SQLITE
# ==========================================
def init_db():
    conn = sqlite3.connect('exam_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, score REAL, 
                  correct_count INTEGER, wrong_count INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'admin')")
    c.execute("INSERT OR IGNORE INTO users VALUES ('hs1', '123', 'student')")
    conn.commit()
    conn.close()

# ==========================================
# PHẦN 2: HELPER VẼ HÌNH ĐỘNG
# ==========================================
def generate_histogram_base64(freqs):
    fig, ax = plt.subplots(figsize=(6, 3))
    bins = ['[140;150)', '[150;160)', '[160;170)', '[170;180)', '[180;190)']
    percents = [f / sum(freqs) * 100 for f in freqs]
    ax.bar(bins, percents, color='#f28e2b', edgecolor='black')
    ax.set_ylabel('Tỉ lệ (%)')
    for i, v in enumerate(percents):
        ax.text(i, v + 1, f"{round(v)}%", ha='center', fontweight='bold')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# ==========================================
# PHẦN 3: THUẬT TOÁN TẠO 40 CÂU HỎI THEO MA TRẬN
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
                self.build_q(1, rf"Điều kiện xác định của biểu thức $\sqrt{{x-{a}}}$ là:", rf"$x \ge {a}$", [rf"$x > {a}$", rf"$x \le {a}$", rf"$x < {a}$"], "Biểu thức trong căn bậc hai phải không âm.")
            elif i == 6:
                self.build_q(6, r"Rút gọn biểu thức $P = \frac{x\sqrt{y} + y\sqrt{x}}{\sqrt{xy}} : \frac{1}{\sqrt{x}-\sqrt{y}}$ ($x,y>0, x \ne y$):", r"$x - y$", [r"$y - x$", r"$\sqrt{x}-\sqrt{y}$", r"$x+y$"], "Rút gọn tử số rồi nhân nghịch đảo.")
            else:
                self.build_q(i, rf"Giá trị của $\sqrt{{{a**2}}}$ là:", rf"{a}", [rf"{-a}", rf"{a**2}", rf"{2*a}"], r"Sử dụng hằng đẳng thức $\sqrt{A^2} = |A|$.")

        # 2. HÀM SỐ Y=AX^2 (3 câu)
        self.build_q(7, r"Hàm số $y = -3x^2$ đồng biến khi nào?", r"$x < 0$", [r"$x > 0$", r"$x \in \mathbb{R}$", r"$x = 0$"], "Với $a < 0$, hàm số đồng biến trên khoảng $(-\infty; 0)$.")
        self.build_q(8, r"Đồ thị hàm số $y = ax^2$ đi qua điểm $A(1; 2)$. Hệ số $a$ bằng:", "2", ["-2", "1", "4"], "Thay $x=1, y=2$ vào phương trình.")
        self.build_q(9, r"Tọa độ đỉnh của Parabol $y = x^2$ là:", r"$(0; 0)$", [r"$(1; 1)$", r"$(0; 1)$", r"$(1; 0)$"], "Dạng $y=ax^2$ luôn có đỉnh tại gốc tọa độ.")

        # 3. PHƯƠNG TRÌNH & HỆ (8 câu)
        self.build_q(10, r"Nghiệm của hệ phương trình $\begin{cases} x + y = 5 \\ x - y = 1 \end{cases}$ là:", r"$(3; 2)$", [r"$(2; 3)$", r"$(4; 1)$", r"$(3; -2)$"], "Cộng hai phương trình vế theo vế.")
        self.build_q(11, r"Phương trình $x^2 - 5x + 6 = 0$ có tập nghiệm là:", r"$\{2; 3\}$", [r"$\{1; 6\}$", r"$\{-2; -3\}$", r"$\{2; -3\}$"], "Sử dụng hệ thức Vi-ét hoặc Delta.")
        for i in range(12, 18):
            self.build_q(i, rf"Biệt thức $\Delta$ của phương trình $x^2 - {i}x + 2 = 0$ là:", rf"${i**2 - 8}$", [rf"${i**2 + 8}$", rf"${i - 8}$", "0"], r"$\Delta = b^2 - 4ac$.")

        # 4. BẤT PHƯƠNG TRÌNH (3 câu)
        self.build_q(18, r"Nghiệm của bất phương trình $3x - 6 > 0$ là:", r"$x > 2$", [r"$x < 2$", r"$x > -2$", r"$x < -6$"], "Chuyển vế và chia cả hai vế cho 3.")
        self.build_q(19, r"Giá trị nguyên lớn nhất của $x$ thỏa mãn $x + 5 < 10$ là:", "4", ["5", "6", "9"], "$x < 5$ nên số nguyên lớn nhất là 4.")
        self.build_q(20, r"Điều kiện của $m$ để $mx + 1 > 0$ là BPT bậc nhất một ẩn là:", r"$m \ne 0$", [r"$m > 0$", r"$m < 0$", r"$m = 1$"], "Hệ số $a$ của ẩn $x$ phải khác 0.")

        # 5. HỆ THỨC LƯỢNG (5 câu)
        self.build_q(21, r"Trong tam giác vuông, $\tan \alpha$ được tính bằng:", r"$\frac{\text{Đối}}{\text{Kề}}$", [r"$\frac{\text{Kề}}{\text{Đối}}$", r"$\frac{\text{Đối}}{\text{Huyền}}$", r"$\frac{\text{Kề}}{\text{Huyền}}$"], "Tan = Đối / Kề.")
        for i in range(22, 26):
            self.build_q(i, rf"Cho $\triangle ABC$ vuông tại $A$, có $\widehat{{B}} = 30^\circ$, $BC = {i*2}$. Độ dài $AC$ là:", rf"{i}", [rf"{i*2}", rf"{i}\sqrt{{3}}", rf"{i}/2"], r"$AC = BC \cdot \sin B$.")

        # 6. ĐƯỜNG TRÒN (6 câu)
        self.build_q(26, "Đường thẳng và đường tròn có tối đa bao nhiêu điểm chung?", "2", ["1", "0", "Vô số"], "Trường hợp đường thẳng cắt đường tròn.")
        self.build_q(27, r"Góc nội tiếp chắn nửa đường tròn có số đo là:", r"$90^\circ$", [r"$180^\circ$", r"$60^\circ$", r"$45^\circ$"], "Định lý về góc nội tiếp.")
        for i in range(28, 32):
            self.build_q(i, rf"Chu vi đường tròn có bán kính $R = {i}$ cm là:", rf"${2*i}\pi$ cm", [rf"${i}\pi$ cm", rf"${i**2}\pi$ cm", rf"{2*i} cm"], r"$C = 2\pi R$.")

        # 7. HÌNH KHỐI (3 câu)
        self.build_q(32, r"Thể tích hình cầu bán kính $R$ được tính theo công thức:", r"$V = \frac{4}{3}\pi R^3$", [r"$V = 4\pi R^2$", r"$V = \pi R^2 h$", r"$V = \frac{1}{3}\pi R^2 h$"], "Công thức SGK.")
        self.build_q(33, r"Diện tích xung quanh hình trụ có bán kính $r$, chiều cao $h$ là:", r"$S_{xq} = 2\pi rh$", [r"$S_{xq} = \pi rh$", r"$S_{xq} = \pi r^2 h$", r"$S_{xq} = 2\pi r^2$"], "Diện tích xung quanh hình trụ.")
        self.build_q(34, r"Thể tích hình nón có $r=3, h=4$ là:", r"$12\pi$", [r"$36\pi$", r"$4\pi$", r"$15\pi$"], r"$V = \frac{1}{3}\pi r^2 h$.")

        # 8. THỐNG KÊ & XÁC SUẤT (6 câu)
        img37 = generate_histogram_base64([10, 30, 35, 15, 10])
        self.build_q(37, "Dựa vào biểu đồ, nhóm chiều cao nào có tỉ lệ học sinh cao nhất?", "[160;170)", ["[140;150)", "[170;180)", "[180;190)"], "Nhìn vào cột cao nhất trên biểu đồ.", img_b64=img37)
        for i in range(35, 41):
            if i != 37:
                self.build_q(i, rf"Gieo một con xúc xắc cân đối. Xác suất xuất hiện mặt {i%6 + 1} chấm là:", r"$\frac{1}{6}$", [r"$\frac{1}{2}$", r"$\frac{1}{3}$", "1"], "Xác suất = 1 / tổng số mặt.")

        return self.exam

# ==========================================
# PHẦN 4: GIAO DIỆN STREAMLIT
# ==========================
def main():
    st.set_page_config(page_title="Ôn Thi Vào 10 - Tuyên Quang", layout="wide")
    init_db()

    if 'current_user' not in st.session_state: st.session_state.current_user = None
    if 'exam_data' not in st.session_state: st.session_state.exam_data = None
    if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
    if 'is_submitted' not in st.session_state: st.session_state.is_submitted = False

    if st.session_state.current_user is None:
        st.header("🔑 ĐĂNG NHẬP HỆ THỐNG")
        with st.form("login"):
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Vào thi"):
                if (u == 'admin' and p == 'admin123') or (u == 'hs1' and p == '123'):
                    st.session_state.current_user = u
                    st.rerun()
                else: st.error("Sai tài khoản!")
        return

    # Sidebar & Header
    st.sidebar.title(f"Chào, {st.session_state.current_user}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    st.title("📝 ĐỀ THI MINH HỌA VÀO 10 - MÔN TOÁN")
    
    if st.button("🆕 SINH ĐỀ THI MỚI (40 CÂU)", type="primary"):
        gen = ExamGenerator()
        st.session_state.exam_data = gen.generate_all()
        st.session_state.user_answers = {}
        st.session_state.is_submitted = False
        st.rerun()

    if st.session_state.exam_data:
        for idx, q in enumerate(st.session_state.exam_data):
            st.subheader(f"Câu {idx+1}:")
            st.markdown(q['question'])
            if q['image']:
                st.image(f"data:image/png;base64,{q['image']}")
            
            # Radio selection
            key = f"q_{q['id']}_{idx}"
            st.radio("Chọn đáp án:", q['options'], key=key, disabled=st.session_state.is_submitted)
            st.session_state.user_answers[q['id']] = st.session_state[key]

            if st.session_state.is_submitted:
                if st.session_state[key] == q['answer']:
                    st.success("Đúng!")
                else:
                    st.error(f"Sai! Đáp án đúng: {q['answer']}")
                with st.expander("Xem giải thích"):
                    st.write(q['hint'])
            st.divider()

        if not st.session_state.is_submitted:
            if st.button("✅ NỘP BÀI CHẤM ĐIỂM", use_container_width=True):
                st.session_state.is_submitted = True
                st.rerun()
        else:
            correct = sum(1 for q in st.session_state.exam_data if st.session_state.user_answers[q['id']] == q['answer'])
            score = (correct / 40) * 10
            st.balloons()
            st.metric("KẾT QUẢ CỦA BẠN", f"{score:.2f} điểm", f"Đúng {correct}/40 câu")

if __name__ == "__main__":
    main()
