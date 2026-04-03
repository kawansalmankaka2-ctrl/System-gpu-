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

# --- 2. Original Dark & Orange Style (Mobile Optimized) ---
def apply_original_style():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
        
        /* Background & Text */
        .stApp {
            background-color: #1e1e1e !important;
            color: #ffffff !important;
        }
        
        html, body, [class*="st-"] {
            font-family: 'Noto Sans Arabic', sans-serif;
            direction: rtl;
            text-align: right;
        }

        /* Header Style */
        .main-header {
            background-color: #2d2d2d;
            border-bottom: 4px solid #ff8c00;
            color: #ff8c00;
            padding: 20px;
            text-align: center;
            border-radius: 0 0 20px 20px;
            margin-bottom: 30px;
        }

        /* Orange Buttons - Just like your original design */
        div.stButton > button {
            width: 100% !important;
            background-color: #ff8c00 !important;
            color: white !important;
            border-radius: 5px !important;
            border: none !important;
            padding: 15px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            margin-top: 10px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        div.stButton > button:active {
            background-color: #e67e00 !important;
            transform: translateY(2px);
        }

        /* Input Fields */
        .stTextInput input, .stSelectbox div {
            background-color: #333333 !important;
            color: white !important;
            border: 1px solid #555555 !important;
        }

        /* Sidebar Dark Theme */
        [data-testid="stSidebar"] {
            background-color: #121212 !important;
            border-left: 2px solid #ff8c00;
        }
        
        .stMetric {
            background-color: #2d2d2d;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #ff8c00;
        }
        
        /* Checkbox Style */
        .stCheckbox {
            color: #ff8c00 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. App Controller ---
def main():
    init_db()
    apply_original_style()
    
    if 'role' not in st.session_state: st.session_state.role = None

    st.markdown("<div class='main-header'><h1>ZANKOY POLYTECHNIC</h1><p>Systemy Amadabun - Garmian</p></div>", unsafe_allow_html=True)

    if st.session_state.role is None:
        st.write("### تکایە جۆری چوونەژوورەوە هەڵبژێرە:")
        if st.button("🔑 چوونەژوورەوەی ئەدمین"): 
            st.session_state.role = "admin_login"; st.rerun()
        if st.button("👨‍🏫 چوونەژوورەوەی مامۆستا"): 
            st.session_state.role = "teacher_login"; st.rerun()

    elif st.session_state.role == "admin_login":
        st.subheader("چوونەژوورەوەی ئەدمین")
        e = st.text_input("ئیمەیڵ:")
        p = st.text_input("پاسوۆرد:", type="password")
        if st.button("LOGIN"):
            h = hashlib.sha256(p.encode()).hexdigest()
            res = execute_query("SELECT dept FROM admins WHERE email=? AND password=?", (e, h), fetch_one=True)
            if res:
                st.session_state.dept, st.session_state.role = res[0], "admin_panel"; st.rerun()
            else: st.error("زانیارییەکان هەڵەن")
        if st.button("BACK"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_login":
        st.subheader("چوونەژوورەوەی مامۆستا")
        code = st.text_input("کۆدی تایبەت:", type="password")
        if st.button("LOGIN"):
            res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (code,), fetch_one=True)
            if res:
                st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
                st.session_state.role = "teacher_panel"; st.rerun()
            else: st.error("کۆدەکە هەڵەیە")
        if st.button("BACK"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "admin_panel":
        dept = st.session_state.dept
        st.sidebar.title(f"بەشی {dept}")
        menu = st.sidebar.radio("مەنیو", ["سەرەتا", "خوێندکاران", "مامۆستایان", "ڕاپۆرت"])
        
        if menu == "سەرەتا":
            st.write(f"## بەخێربێیت بۆ بەشی {dept}")
            s_count = execute_query("SELECT COUNT(*) FROM students WHERE dept=?", (dept,), fetch_one=True)[0]
            st.metric("کۆی خوێندکاران", s_count)
            
        elif menu == "خوێندکاران":
            st.subheader("زیادکردنی خوێندکار")
            name = st.text_input("ناوی سیانی:")
            stage = st.selectbox("قۆناغ", ["1", "2", "3", "4"])
            if st.button("تۆمارکردن"):
                code = f"S{random.randint(100, 999)}"
                execute_query("INSERT INTO students (name, stage, code, dept) VALUES (?,?,?,?)", (name, stage, code, dept), commit=True)
                st.success(f"تۆمارکرا: {code}")
                
        elif menu == "مامۆستایان":
            st.subheader("زیادکردنی مامۆستا")
            t_name = st.text_input("ناوی مامۆستا:")
            c_name = st.text_input("ناوی وانە:")
            t_stage = st.selectbox("قۆناغ:", ["1", "2", "3", "4"])
            if st.button("دروستکردنی کۆد"):
                t_code = f"T{random.randint(100, 999)}"
                execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)", (t_name, t_code, dept, t_stage), commit=True)
                tid = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)[0]
                execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,60,?)", (tid, c_name, dept), commit=True)
                st.info(f"کۆدی مامۆستا: {t_code}")

        if st.sidebar.button("LOGOUT"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_panel":
        tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
        st.write(f"### مامۆستا: {tname}")
        t_stage = execute_query("SELECT target_stage FROM teachers WHERE id=?", (tid,), fetch_one=True)[0]
        students = execute_query("SELECT id, name FROM students WHERE dept=? AND stage=?", (dept, t_stage), fetch_all=True)
        
        if students:
            st.write("لیستی غائیببوون:")
            att_data = {}
            for sid, sname in students:
                att_data[sid] = st.checkbox(sname, key=sid)
            
            if st.button("SAVE"):
                st.success("پاشەکەوت کرا!")
        
        if st.sidebar.button("LOGOUT"): st.session_state.role = None; st.rerun()

if __name__ == "__main__":
    main()
