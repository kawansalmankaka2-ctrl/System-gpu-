# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
from datetime import datetime
import io

# --- 1. Database Logic ---
def get_connection():
    return sqlite3.connect('GPU_Attendance_System.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, dept TEXT, type TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, dept TEXT, target_stage TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, stage TEXT, grp TEXT, code TEXT UNIQUE, dept TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, teacher_id INTEGER, course_name TEXT, total_hours INTEGER, dept TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY, student_id INTEGER, course_id INTEGER, date TEXT,
                  hours_absent INTEGER, type TEXT, dept TEXT,
                  UNIQUE(student_id, course_id, date, type))''')
    p = hashlib.sha256("Garmian@2026".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO admins (email, password, dept, type) VALUES (?, ?, ?, ?)",
              ('admin@gpu.edu.iq', p, 'ڕاگرایەتی', 'زانکۆ'))
    conn.commit()
    conn.close()

def execute_query(query, params=(), fetch_all=False, fetch_one=False, commit=False):
    conn = get_connection()
    c = conn.cursor()
    result = None
    try:
        c.execute(query, params)
        if commit: conn.commit(); result = True
        if fetch_one: result = c.fetchone()
        if fetch_all: result = c.fetchall()
    finally: conn.close()
    return result

# --- 2. Mobile-First Custom CSS ---
def apply_mobile_style():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
        
        /* General Setup */
        html, body, [class*="st-"] {
            font-family: 'Noto Sans Arabic', sans-serif;
            direction: rtl;
            text-align: right;
        }

        /* Main Header - Clean & Simple */
        .main-header {
            background-color: #008B8B;
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }

        /* Buttons Fix for Mobile */
        div.stButton > button {
            width: 100% !important;
            background-color: #008B8B !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 10px !important;
            font-size: 16px !important;
            margin-bottom: 10px !important;
            height: auto !important;
        }

        /* Card Style */
        .data-card {
            background-color: #f8f9fa;
            border-right: 5px solid #008B8B;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        /* Metric/Stats Alignment */
        [data-testid="stMetricValue"] {
            font-size: 25px !important;
            text-align: center !important;
        }
        
        /* Sidebar Fix */
        [data-testid="stSidebar"] {
            text-align: right !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. UI Modules ---
def admin_panel():
    dept = st.session_state.dept
    st.sidebar.markdown(f"### بەشی {dept}")
    menu = st.sidebar.selectbox("مەنیو", ["🏠 سەرەتا", "👥 خوێندکاران", "👨‍🏫 مامۆستایان", "📊 ڕاپۆرت"])

    if menu == "🏠 سەرەتا":
        st.markdown(f"<div class='data-card'>بەخێربێیت بۆ پانێڵی {dept}</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        s_count = execute_query("SELECT COUNT(*) FROM students WHERE dept=?", (dept,), fetch_one=True)[0]
        t_count = execute_query("SELECT COUNT(*) FROM teachers WHERE dept=?", (dept,), fetch_one=True)[0]
        col1.metric("خوێندکاران", s_count)
        col2.metric("مامۆستایان", t_count)

    elif menu == "👥 خوێندکاران":
        st.subheader("تۆمارکردنی خوێندکار")
        name = st.text_input("ناوی سیانی:")
        stage = st.selectbox("قۆناغ", ["1", "2", "3", "4"])
        grp = st.selectbox("گروپ", ["A", "B", "C", "D"])
        if st.button("تۆمارکردن"):
            code = f"S{random.randint(1000, 9999)}"
            execute_query("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)",
                         (name, stage, grp, code, dept), commit=True)
            st.success(f"تۆمارکرا بە کۆدی: {code}")

    elif menu == "👨‍🏫 مامۆستایان":
        st.subheader("زیادکردنی مامۆستا")
        t_name = st.text_input("ناوی مامۆستا:")
        c_name = st.text_input("ناوی وانە:")
        t_stage = st.selectbox("بۆ قۆناغی:", ["1", "2", "3", "4"])
        t_hours = st.number_input("سەعاتی ساڵانە:", 30, 150, 60)
        if st.button("تۆمارکردنی مامۆستا"):
            t_code = f"T{random.randint(1000, 9999)}"
            execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)", (t_name, t_code, dept, t_stage), commit=True)
            tid = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)[0]
            execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,?,?)", (tid, c_name, t_hours, dept), commit=True)
            st.info(f"کۆدی مامۆستا: {t_code}")

    elif menu == "📊 ڕاپۆرت":
        st.subheader("داگرتنی داتاکان")
        df = pd.read_sql(f"SELECT * FROM attendance WHERE dept='{dept}'", get_connection())
        st.dataframe(df)
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False)
        st.download_button("📥 دابەزاندنی Excel", towrite, "Report.xlsx")

def teacher_panel():
    tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
    course_info = execute_query("SELECT id, course_name FROM courses WHERE teacher_id=?", (tid,), fetch_one=True)
    t_stage = execute_query("SELECT target_stage FROM teachers WHERE id=?", (tid,), fetch_one=True)[0]
    
    if course_info:
        cid, cname = course_info
        st.markdown(f"<div class='data-card'>مامۆستا: {tname}<br>وانە: {cname}</div>", unsafe_allow_html=True)
        l_hours = st.selectbox("سەعاتی وانە:", [1, 2, 3, 4])
        
        students = execute_query("SELECT id, name FROM students WHERE dept=? AND stage=?", (dept, t_stage), fetch_all=True)
        
        att_data = {}
        for sid, sname in students:
            col1, col2 = st.columns([2, 1])
            col1.write(sname)
            absent = col2.checkbox("غائب", key=sid)
            att_data[sid] = l_hours if absent else 0
            
        if st.button("💾 پاشەکەوتکردن"):
            for sid, h in att_data.items():
                execute_query("INSERT OR REPLACE INTO attendance (student_id, course_id, date, hours_absent, type, dept) VALUES (?,?,?,?,?,?)",
                             (sid, cid, str(datetime.now().date()), h, "گشتی", dept), commit=True)
            st.success("تۆمارکرا!")

# --- 4. Main App ---
def main():
    init_db()
    apply_mobile_style()
    
    if 'role' not in st.session_state: st.session_state.role = None

    st.markdown("<div class='main-header'><h2>زانکۆی پۆلیتەکنیکی گەرمیان</h2><p>سیستەمی ئامادەبوونی خوێندکاران</p></div>", unsafe_allow_html=True)

    if st.session_state.role is None:
        if st.button("🔑 چوونەژوورەوەی ئەدمین"): st.session_state.role = "admin_login"; st.rerun()
        if st.button("👨‍🏫 چوونەژوورەوەی مامۆستا"): st.session_state.role = "teacher_login"; st.rerun()

    elif st.session_state.role == "admin_login":
        e = st.text_input("ئیمەیڵ:")
        p = st.text_input("پاسوۆرد:", type="password")
        if st.button("چوونەژوورەوە"):
            h = hashlib.sha256(p.encode()).hexdigest()
            res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (e, h), fetch_one=True)
            if res:
                st.session_state.dept, st.session_state.role = res[0], "admin_panel"; st.rerun()
            else: st.error("هەڵەیە")
        if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_login":
        code = st.text_input("کۆدی مامۆستا:", type="password")
        if st.button("چوونەژوورەوە"):
            res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (code,), fetch_one=True)
            if res:
                st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
                st.session_state.role = "teacher_panel"; st.rerun()
            else: st.error("کۆدەکە هەڵەیە")
        if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "admin_panel":
        admin_panel()
        if st.sidebar.button("🚪 دەرچوون"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_panel":
        teacher_panel()
        if st.sidebar.button("🚪 دەرچوون"): st.session_state.role = None; st.rerun()

if __name__ == "__main__":
    main()
