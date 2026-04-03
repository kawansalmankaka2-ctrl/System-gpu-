# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import hashlib
import random
import time
from datetime import datetime
import io
from shillelagh.backends.apsw.db import connect

# --- 1. UI & Theme Configuration ---
def apply_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
        html, body, [class*="st-"] {
            font-family: 'Noto Sans Arabic', sans-serif;
            direction: rtl; text-align: right;
        }
        .stApp { background-color: #ffffff; }
        .main-header {
            background: linear-gradient(90deg, #008B8B 0%, #20B2AA 100%);
            color: white; padding: 2rem; border-radius: 15px;
            text-align: center; margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .card {
            background: #f9f9f9; padding: 20px; border-radius: 15px;
            border-right: 6px solid #008B8B; margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .stButton>button {
            background: #008B8B; color: white !important;
            border-radius: 8px; width: 100%; border: none;
            font-weight: bold; height: 45px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. Database Logic (SQLite as local, but for Online use Cloud DB) ---
# تێبینی: بۆ ئەوەی داتاکانت نەفەوتێت، پێشنیار ئەکەم هەفتانە Excel دابەزێنیت
def get_connection():
    return sqlite3.connect('GPU_DATA.db', check_same_thread=False)

import sqlite3
conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, dept TEXT, type TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, dept TEXT, target_stage TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, stage TEXT, grp TEXT, code TEXT UNIQUE, dept TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, teacher_id INTEGER, course_name TEXT, total_hours INTEGER, dept TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS attendance
             (id INTEGER PRIMARY KEY, student_id INTEGER, course_id INTEGER, date TEXT,
              hours_absent INTEGER, status INTEGER, type TEXT, dept TEXT,
              UNIQUE(student_id, course_id, date, type))''')
# ئەکاونتی سەرەکی ئەدمین
p = hashlib.sha256("Garmian@2026".encode()).hexdigest()
c.execute("INSERT OR IGNORE INTO admins (email, password, dept, type) VALUES (?, ?, ?, ?)",
          ('admin@gpu.edu.iq', p, 'ڕاگرایەتی', 'زانکۆ'))
conn.commit()

# --- 3. Admin & Teacher Modules ---
def admin_panel():
    dept = st.session_state.dept
    st.sidebar.markdown(f"### 🛡️ پانێڵی {dept}")
    task = st.sidebar.selectbox("مەنیو", ["📊 داتاکان", "👥 خوێندکاران", "👨‍🏫 مامۆستایان", "📜 ڕاپۆرتی کۆتایی"])

    if task == "📊 داتاکان":
        st.subheader("ئاماری گشتی بەش")
        col1, col2 = st.columns(2)
        s_num = pd.read_sql(f"SELECT COUNT(*) FROM students WHERE dept='{dept}'", conn).iloc[0,0]
        t_num = pd.read_sql(f"SELECT COUNT(*) FROM teachers WHERE dept='{dept}'", conn).iloc[0,0]
        col1.metric("خوێندکاران", s_num)
        col2.metric("مامۆستایان", t_num)

    elif task == "👥 خوێندکاران":
        with st.expander("➕ زیادکردنی خوێندکار"):
            name = st.text_input("ناوی سیانی:")
            stage = st.selectbox("قۆناغ", ["1", "2", "3", "4"])
            grp = st.selectbox("گروپ", ["A", "B", "C", "D"])
            if st.button("تۆمارکردن"):
                code = f"S{random.randint(1000, 9999)}"
                c.execute("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)",
                          (name, stage, grp, code, dept))
                conn.commit()
                st.success(f"خوێندکار {name} بە کۆدی {code} تۆمارکرا")

    elif task == "👨‍🏫 مامۆستایان":
        with st.form("t_form"):
            t_name = st.text_input("ناوی مامۆستا:")
            c_name = st.text_input("ناوی وانە:")
            t_stage = st.selectbox("قۆناغ:", ["1", "2", "3", "4"])
            t_hours = st.number_input("سەعاتی ساڵانە:", 30, 150)
            if st.form_submit_button("زیادکردن"):
                t_code = f"T{random.randint(1000, 9999)}"
                c.execute("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)", (t_name, t_code, dept, t_stage))
                tid = c.lastrowid
                c.execute("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,?,?)", (tid, c_name, t_hours, dept))
                conn.commit()
                st.success(f"مامۆستا تۆمارکرا. کۆدی چوونەژوورەوە: {t_code}")

    elif task == "📜 ڕاپۆرتی کۆتایی":
        st.markdown("### ڕاپۆرتی غائیببوون")
        df_att = pd.read_sql(f"SELECT * FROM attendance WHERE dept='{dept}'", conn)
        st.dataframe(df_att)
        # دوگمەی دابەزاندن بۆ ئەوەی داتاکەت نەفەوتێت
        towrite = io.BytesIO()
        df_att.to_excel(towrite, index=False)
        st.download_button("📥 دابەزاندنی داتا (Excel)", towrite, "GPU_Report.xlsx")

def teacher_panel():
    tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
    t_info = pd.read_sql(f"SELECT target_stage FROM teachers WHERE id={tid}", conn).iloc[0,0]
    course = pd.read_sql(f"SELECT id, course_name FROM courses WHERE teacher_id={tid}", conn).iloc[0]
    
    st.markdown(f"<div class='card'><h3>مامۆستا: {tname}</h3><p>وانە: {course['course_name']} | قۆناغ: {t_info}</p></div>", unsafe_allow_html=True)
    
    l_type = st.radio("جۆری وانە:", ["تیۆری", "پراکتیکی"], horizontal=True)
    l_hours = st.slider("سەعاتی وانە:", 1, 4, 2)
    
    students = pd.read_sql(f"SELECT id, name FROM students WHERE dept='{dept}' AND stage='{t_info}'", conn)
    
    st.write("---")
    res = {}
    for _, s in students.iterrows():
        col1, col2 = st.columns([3, 1])
        col1.write(s['name'])
        status = col2.toggle("ئامادەنەبوو", key=s['id'])
        res[s['id']] = l_hours if status else 0
        
    if st.button("💾 پاشەکەوتکردن"):
        for sid, h in res.items():
            c.execute("INSERT OR REPLACE INTO attendance (student_id, course_id, date, hours_absent, type, dept) VALUES (?,?,?,?,?,?)",
                      (sid, course['id'], str(datetime.now().date()), h, l_type, dept))
        conn.commit()
        st.success("تۆمارکرا!")

# --- 4. Main Controller ---
def main():
    apply_theme()
    if 'role' not in st.session_state: st.session_state.role = None

    st.markdown("<div class='main-header'><h1>زانکۆی پۆلیتەکنیکی گەرمیان</h1><p>سیستەمی پێشکەوتووی ئامادەبوونی خوێندکاران</p></div>", unsafe_allow_html=True)

    if st.session_state.role is None:
        col1, col2 = st.columns(2)
        if col1.button("🔑 ئەدمین"): st.session_state.role = "admin_login"; st.rerun()
        if col2.button("👨‍🏫 مامۆستا"): st.session_state.role = "teacher_login"; st.rerun()
        st.info("گەشەپێدەر: ئەندازیار لەنیا حازم کەریم")

    elif st.session_state.role == "admin_login":
        e = st.text_input("ئیمەیڵ:")
        p = st.text_input("پاسوۆرد:", type="password")
        if st.button("چوونەژوورەوە"):
            h = hashlib.sha256(p.encode()).hexdigest()
            user = pd.read_sql(f"SELECT dept, type FROM admins WHERE email='{e}' AND password='{h}'", conn)
            if not user.empty:
                st.session_state.dept, st.session_state.type = user.iloc[0]['dept'], user.iloc[0]['type']
                st.session_state.role = "admin_panel"; st.rerun()
            else: st.error("زانیارییەکان هەڵەن")
        if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_login":
        code = st.text_input("کۆدی مامۆستا:", type="password")
        if st.button("چوونەژوورەوە"):
            t = pd.read_sql(f"SELECT id, name, dept FROM teachers WHERE code='{code}'", conn)
            if not t.empty:
                st.session_state.t_id, st.session_state.t_name, st.session_state.dept = t.iloc[0]['id'], t.iloc[0]['name'], t.iloc[0]['dept']
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
