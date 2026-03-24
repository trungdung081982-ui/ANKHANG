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
        self.build_q(6, r"Rút gọn $\frac{x\sqrt{y} + y\sqrt{x}}{\
