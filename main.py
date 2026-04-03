# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
import time
from datetime import datetime
import io

# --- 1. Database Configuration ---
def get_connection():
    # ئەمە فایلێکی ناوخۆیی دروست دەکات بۆ پاشەکەوتکردنی زانیارییەکان
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
                  hours_absent INTEGER, status INTEGER, type TEXT, dept TEXT,
                  UNIQUE(student_id, course_id, date, type))''')
    
    # دروستکردنی ئەکاونتی سەرەکی ئەدمین
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
        if commit: 
            conn.commit()
            result = True
        if fetch_one: result = c.fetchone()
        if fetch_all: result = c.fetchall()
    finally: conn.close()
    return result

# --- 2. Professional UI Style ---
def apply_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
        html, body, [class*="st-"] {
            font-family: 'Noto Sans Arabic', sans-serif;
            direction: rtl; text-align: right;
        }
        .main-header {
            background: linear-gradient(135deg, #008B8B 0%, #20B2AA 100%);
            color: white; padding: 1.5rem; border-radius: 15px;
            text-align: center; margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .stButton>button {
            background-color: #008B8B; color: white !important;
            border-radius: 10px; border: none; height: 45px;
            font-weight: bold; width: 100%; transition: 0.3s;
        }
        .stButton>button:hover { background-color: #20B2AA; transform: translateY(-2px); }
        .card {
            background-color: #ffffff; padding: 20px;
            border-radius: 15px; border-right: 5px solid #008B8B;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. Functional Sections ---
def admin_panel():
    dept = st.session_state.dept
    st.sidebar.markdown(f"## بەشی {dept}")
    menu = st.sidebar.selectbox("مەنیو", ["🏠 سەرەتا", "👥 خوێندکاران", "👨‍🏫 مامۆستایان", "📊 ڕاپۆرتی ئامادەبوون"])

    if menu == "🏠 سەرەتا":
        st.markdown(f"### بەخێربێیت بۆ پانێڵی {dept}")
        c1, c2 = st.columns(2)
        s_count = execute_query("SELECT COUNT(*) FROM students WHERE dept=?", (dept,), fetch_one=True)[0]
        t_count = execute_query("SELECT COUNT(*) FROM teachers WHERE dept=?", (dept,), fetch_one=True)[0]
        c1.metric("کۆی خوێندکاران", s_count)
        c2.metric("کۆی مامۆستایان", t_count)

    elif menu == "👥 خوێندکاران":
        st.subheader("بەڕێوەبردنی خوێندکاران")
        with st.expander("➕ زیادکردنی خوێندکاری نوێ"):
            name = st.text_input("ناوی سیانی:")
            stage = st.selectbox("قۆناغ", ["1", "2", "3", "4"])
            grp = st.selectbox("گروپ", ["A", "B", "C", "D", "E"])
            if st.button("تۆمارکردن"):
                if name:
                    code = f"S{random.randint(1000, 9999)}"
                    execute_query("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)",
                                 (name, stage, grp, code, dept), commit=True)
                    st.success(f"خوێندکار {name} تۆمارکرا")
                else: st.warning("تکایە ناو بنووسە")

    elif menu == "👨‍🏫 مامۆستایان":
        with st.form("teacher_add"):
            t_name = st.text_input("ناوی مامۆستا:")
            c_name = st.text_input("ناوی وانە:")
            t_stage = st.selectbox("قۆناغ:", ["1", "2", "3", "4"])
            t_hours = st.number_input("کۆی سەعاتی وانە (ساڵانە):", 30, 150, 60)
            if st.form_submit_button("تۆمارکردن"):
                if t_name and c_name:
                    t_code = f"T{random.randint(1000, 9999)}"
                    execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)",
                                 (t_name, t_code, dept, t_stage), commit=True)
                    tid = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)[0]
                    execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,?,?)",
                                 (tid, c_name, t_hours, dept), commit=True)
                    st.success(f"تۆمارکرا! کۆدی چوونەژوورەوەی مامۆستا: {t_code}")

    elif menu == "📊 ڕاپۆرتی ئامادەبوون":
        st.subheader("ڕاپۆرتی غائیببوون")
        sel_stage = st.selectbox("قۆناغ:", ["1", "2", "3", "4"])
        st_list = execute_query("SELECT id, name, grp FROM students WHERE stage=? AND dept=?", (sel_stage, dept), fetch_all=True)
        co_list = execute_query("SELECT id, course_name, total_hours FROM courses WHERE dept=?", (dept,), fetch_all=True)
        
        if st_list and co_list:
            report = []
            for sid, sname, sgrp in st_list:
                row = {"ناو": sname, "گروپ": sgrp}
                for cid, cname, thours in co_list:
                    abs_sum = execute_query("SELECT SUM(hours_absent) FROM attendance WHERE student_id=? AND course_id=?", (sid, cid), fetch_one=True)[0] or 0
                    row[cname] = f"{(abs_sum/thours)*100:.1f}%"
                report.append(row)
            df = pd.DataFrame(report)
            st.dataframe(df, use_container_width=True)
            
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False)
            st.download_button("📥 دابەزاندنی ڕاپۆرت (Excel)", towrite, f"Report_{dept}.xlsx")

def teacher_panel():
    tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
    course = execute_query("SELECT id, course_name FROM courses WHERE teacher_id=?", (tid,), fetch_one=True)
    t_stage = execute_query("SELECT target_stage FROM teachers WHERE id=?", (tid,), fetch_one=True)[0]
    
    if not course: st.error("هیچ وانەیەک بۆ تۆ دابین نەکراوە"); return
    cid, cname = course[0], course[1]

    st.markdown(f"<div class='card'><h3>بەخێربێیت مامۆستا {tname}</h3><p>وانە: {cname} | قۆناغ: {t_stage}</p></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    l_type = c1.selectbox("جۆری وانە:", ["تیۆری", "پراکتیکی"])
    l_hours = c2.number_input("سەعات:", 1, 6, 2)
    
    students = execute_query("SELECT id, name FROM students WHERE dept=? AND stage=?", (dept, t_stage), fetch_all=True)
    
    if students:
        st.write("---")
        att_results = {}
        for sid, sname in students:
            col1, col2 = st.columns([3, 1])
            col1.write(sname)
            status = col2.radio("حاڵەت", ["ئامادەیە", "نەهاتووە"], key=sid, horizontal=True)
            att_results[sid] = l_hours if status == "نەهاتووە" else 0
        
        if st.button("💾 پاشەکەوتکردنی ئامادەبوون"):
            for sid, h in att_results.items():
                execute_query("INSERT OR REPLACE INTO attendance (student_id, course_id, date, hours_absent, type, dept) VALUES (?,?,?,?,?,?)",
                             (sid, cid, str(datetime.now().date()), h, l_type, dept), commit=True)
            st.success("بە سەرکەوتووی پاشەکەوت کرا")
            time.sleep(1); st.rerun()

# --- 4. Main Controller ---
def main():
    st.set_page_config(page_title="GPU Attendance System", layout="wide")
    init_db()
    apply_theme()

    if 'role' not in st.session_state: st.session_state.role = None

    st.markdown("<div class='main-header'><h1>زانکۆی پۆلیتەکنیکی گەرمیان</h1><p>سیستەمی پێشکەوتووی ئامادەبوونی خوێندکاران</p></div>", unsafe_allow_html=True)

    if st.session_state.role is None:
        col1, col2 = st.columns(2)
        if col1.button("🔑 چوونەژوورەوەی ئەدمین"): st.session_state.role = "admin_login"; st.rerun()
        if col2.button("👨‍🏫 چوونەژوورەوەی مامۆستا"): st.session_state.role = "teacher_login"; st.rerun()

    elif st.session_state.role == "admin_login":
        e = st.text_input("ئیمەیڵ:")
        p = st.text_input("پاسوۆرد:", type="password")
        if st.button("چوونەژوورەوە"):
            h = hashlib.sha256(p.encode()).hexdigest()
            res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (e, h), fetch_one=True)
            if res:
                st.session_state.dept, st.session_state.type = res[0], res[1]
                st.session_state.role = "admin_panel"; st.rerun()
            else: st.error("زانیارییەکان هەڵەن")
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
        if st.session_state.type == "زانکۆ":
            st.subheader("🏛️ پانێڵی ڕاگرایەتی")
            with st.form("new_dept"):
                e = st.text_input("ئیمەیڵ:")
                p = st.text_input("پاسوۆرد:", type="password")
                d = st.selectbox("بەش:", ["تەکنەلۆجیای زانیاری", "ئەندازیاری کارەبا", "شیکاری نەخۆشیەکان", "تەکنیکی پەرستاری", "کارگێڕی کار"])
                if st.form_submit_button("دروستکردنی ئەکاونت"):
                    hp = hashlib.sha256(p.encode()).hexdigest()
                    execute_query("INSERT INTO admins (email, password, dept, type) VALUES (?,?,?,?)", (e, hp, d, "بەش"), commit=True)
                    st.success(f"ئەکاونتی بەشی {d} دروستکرا")
        else: admin_panel()
        if st.sidebar.button("🚪 دەرچوون"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_panel":
        teacher_panel()
        if st.sidebar.button("🚪 دەرچوون"): st.session_state.role = None; st.rerun()

if __name__ == "__main__":
    main()
