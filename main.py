# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
import io
from datetime import datetime

# --- 1. Database & Security (SHA-256) ---
def init_db():
    conn = sqlite3.connect('GPU_Attendance_Final.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, dept TEXT, type TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, dept TEXT, target_stage TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, stage TEXT, grp TEXT, code TEXT UNIQUE, dept TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, teacher_id INTEGER, course_name TEXT, total_hours INTEGER, dept TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY, student_id INTEGER, course_id INTEGER, date TEXT,
                  hours_absent INTEGER, type TEXT, dept TEXT,
                  UNIQUE(student_id, course_id, date, type))''')
    
    # Super Admin (ڕاگرایەتی)
    p = hashlib.sha256("Garmian@2026".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO admins (email, password, dept, type) VALUES (?, ?, ?, ?)",
              ('admin@gpu.edu.iq', p, 'ڕاگرایەتی', 'SuperAdmin'))
    conn.commit()
    conn.close()

def execute_query(query, params=(), fetch_all=False, fetch_one=False, commit=False):
    conn = sqlite3.connect('GPU_Attendance_Final.db')
    c = conn.cursor()
    res = None
    try:
        c.execute(query, params)
        if commit: conn.commit(); res = True
        elif fetch_one: res = c.fetchone()
        elif fetch_all: res = c.fetchall()
    finally: conn.close()
    return res

# --- 2. Professional UI/UX Design ---
def apply_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
        html, body, [class*="st-"] { font-family: 'Noto Sans Arabic', sans-serif; direction: rtl; text-align: right; }
        .stApp { background-color: #FFFFFF; }
        .main-card { background: #FFFFFF; padding: 20px; border-radius: 15px; border-top: 8px solid #0D9488; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 20px; text-align: center; }
        div.stButton > button { width: 100% !important; height: 55px; background: #0D9488 !important; color: white !important; border-radius: 12px; font-weight: bold; font-size: 18px; border: none; margin-top: 10px; }
        h1, h2, h3 { color: #0D9488 !important; }
        .stMetric { background: #F0FDFA; padding: 15px; border-radius: 10px; border: 1px solid #CCFBF1; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. Functional Logic ---

def super_admin_panel():
    st.markdown("<div class='main-card'><h2>پانێڵی ڕاگرایەتی (Super Admin)</h2></div>", unsafe_allow_html=True)
    with st.expander("➕ دروستکردنی ئەکاونتی بەش (IT, کارگێڕی...)", expanded=True):
        email = st.text_input("ئیمەیڵی بەش:")
        pw = st.text_input("پاسوۆردی بەش:", type="password")
        dept_name = st.selectbox("ناوی بەش:", ["تەکنەلۆجیای زانیاری", "کارگێڕی کار", "پەرستاری", "ئەندازیاری", "شیکاری نەخۆشییەکان"])
        if st.button("تۆمارکردنی ئەکاونتی بەش"):
            hp = hashlib.sha256(pw.encode()).hexdigest()
            execute_query("INSERT INTO admins (email, password, dept, type) VALUES (?,?,?,?)", (email, hp, dept_name, "DeptAdmin"), commit=True)
            st.success(f"ئەکاونتی بەشی {dept_name} دروستکرا")

def dept_admin_panel(dept):
    st.markdown(f"<div class='main-card'><h2>ئەدمینی بەشی {dept}</h2></div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["👥 خوێندکاران", "👨‍🏫 مامۆستایان", "📊 ڕاپۆرت"])
    
    with tab1:
        with st.form("student_form"):
            s_name = st.text_input("ناوی سیانی خوێندکار:")
            s_stage = st.selectbox("قۆناغ:", ["1", "2", "3", "4"])
            s_grp = st.selectbox("گروپ:", ["A", "B", "C", "D", "E", "F"])
            if st.form_submit_button("تۆمارکردنی خوێندکار"):
                s_code = f"S{random.randint(1000, 9999)}"
                execute_query("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)", (s_name, s_stage, s_grp, s_code, dept), commit=True)
                st.success(f"خوێندکار {s_name} تۆمارکرا. کۆد: {s_code}")

    with tab2:
        with st.form("teacher_form"):
            t_name = st.text_input("ناوی مامۆستا:")
            c_name = st.text_input("ناوی وانە:")
            t_stage = st.selectbox("بۆ چ قۆناغێک (Target Stage):", ["1", "2", "3", "4"])
            t_hours = st.number_input("کۆی سەعاتی وانە (بۆ حساباتی %):", 1, 200, 30)
            if st.form_submit_button("تۆمارکردنی مامۆستا"):
                t_code = f"T{random.randint(1000, 9999)}"
                execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)", (t_name, t_code, dept, t_stage), commit=True)
                tid = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)[0]
                execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,?,?)", (tid, c_name, t_hours, dept), commit=True)
                st.success(f"مامۆستا {t_name} تۆمارکرا. کۆدی چوونەژوورەوە: {t_code}")

    with tab3:
        st.write("### دابەزاندنی ڕاپۆرتی Excel")
        rep_stage = st.selectbox("ڕاپۆرتی قۆناغی چەند؟", ["1", "2", "3", "4"], key="rep_s")
        if st.button("ئامادەکردنی ڕاپۆرت"):
            st_list = execute_query("SELECT id, name, grp FROM students WHERE stage=? AND dept=?", (rep_stage, dept), fetch_all=True)
            co_list = execute_query("SELECT id, course_name, total_hours FROM courses WHERE dept=?", (dept,), fetch_all=True)
            if st_list and co_list:
                data = []
                for sid, sname, sgrp in st_list:
                    row = {"ناو": sname, "گروپ": sgrp}
                    for cid, cname, thours in co_list:
                        absent = execute_query("SELECT SUM(hours_absent) FROM attendance WHERE student_id=? AND course_id=?", (sid, cid), fetch_one=True)[0] or 0
                        row[cname] = f"{(absent/thours)*100:.1f}%"
                    data.append(row)
                df = pd.DataFrame(data)
                st.dataframe(df)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Attendance')
                st.download_button("📥 دابەزاندنی فایلەکە", output.getvalue(), f"Report_Stage_{rep_stage}.xlsx")

def teacher_panel():
    tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
    t_stage = execute_query("SELECT target_stage FROM teachers WHERE id=?", (tid,), fetch_one=True)[0]
    course = execute_query("SELECT id, course_name FROM courses WHERE teacher_id=?", (tid,), fetch_one=True)
    cid, cname = course[0], course[1]

    st.markdown(f"<div class='main-card'><h3>بەخێربێیت مامۆستا {tname}</h3><p>وانەی {cname} | قۆناغی {t_stage}</p></div>", unsafe_allow_html=True)
    
    l_type = st.radio("جۆری وانە:", ["تیۆری (هەموو قۆناغ)", "پراکتیکی (گروپ)"], horizontal=True)
    
    query = "SELECT id, name FROM students WHERE stage=? AND dept=?"
    params = (t_stage, dept)
    
    if "پراکتیکی" in l_type:
        target_grp = st.selectbox("گروپ هەڵبژێرە:", ["A", "B", "C", "D", "E", "F"])
        query += " AND grp=?"
        params = (t_stage, dept, target_grp)
    
    students = execute_query(query, params, fetch_all=True)
    
    if students:
        st.write("---")
        absent_list = []
        for sid, sname in students:
            col1, col2 = st.columns([3, 1])
            col1.write(f"👤 {sname}")
            if col2.checkbox("ئامادەنییە", key=f"s_{sid}"):
                absent_list.append(sid)
        
        hours = st.number_input("سەعاتی غائیب:", 1, 6, 2)
        if st.button("💾 پاشەکەوتکردنی غائیبات"):
            date_now = str(datetime.now().date())
            for sid in absent_list:
                execute_query("INSERT OR REPLACE INTO attendance (student_id, course_id, date, hours_absent, type, dept) VALUES (?,?,?,?,?,?)",
                             (sid, cid, date_now, hours, l_type, dept), commit=True)
            st.success("بە سەرکەوتووی تۆمارکرا")
    else:
        st.warning("هیچ خوێندکارێک لەم قۆناغە/گروپە نەدۆزرایەوە.")

# --- 4. Main App Navigation ---
def main():
    st.set_page_config(page_title="GPU Attendance System", layout="centered")
    init_db()
    apply_theme()

    if 'role' not in st.session_state: st.session_state.role = None

    if st.session_state.role is None:
        st.markdown("<div class='main-card'><h1>زانکۆی پۆلیتەکنیکی گەرمیان</h1><h3>سیستەمی ئامادەبوونی ئەلیکترۆنی</h3></div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        if col1.button("🔑 چوونەژوورەوەی ئەدمین"): st.session_state.role = "login_admin"; st.rerun()
        if col2.button("🌙 چوونەژوورەوەی مامۆستا"): st.session_state.role = "login_teacher"; st.rerun()

    elif st.session_state.role == "login_admin":
        email = st.text_input("ئیمەیڵ:")
        pw = st.text_input("پاسوۆرد:", type="password")
        if st.button("داخڵبوون"):
            h = hashlib.sha256(pw.encode()).hexdigest()
            res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (email, h), fetch_one=True)
            if res:
                st.session_state.role = res[1]
                st.session_state.dept = res[0]
                st.rerun()
            else: st.error("زانیارییەکان هەڵەن")
        if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "login_teacher":
        t_code = st.text_input("کۆدی تایبەتی مامۆستا:", type="password")
        if st.button("داخڵبوون"):
            res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (t_code,), fetch_one=True)
            if res:
                st.session_state.role = "teacher_panel"
                st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
                st.rerun()
            else: st.error("کۆدەکە هەڵەیە")
        if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "SuperAdmin":
        super_admin_panel()
        if st.sidebar.button("🚪 دەرچوون"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "DeptAdmin":
        dept_admin_panel(st.session_state.dept)
        if st.sidebar.button("🚪 دەرچوون"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_panel":
        teacher_panel()
        if st.sidebar.button("🚪 دەرچوون"): st.session_state.role = None; st.rerun()

if __name__ == "__main__":
    main()
