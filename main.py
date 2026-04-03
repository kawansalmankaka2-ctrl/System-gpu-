# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
from datetime import datetime
import io

# --- ١. بنکەی زانیاری (Database) ---
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
    
    # ئەکاونتی سەرەکی
    p = hashlib.sha256("Garmian@2026".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO admins (email, password, dept, type) VALUES (?, ?, ?, ?)",
              ('admin@gpu.edu.iq', p, 'تەکنەلۆجیای زانیاری', 'زانکۆ'))
    conn.commit()
    conn.close()

def execute_query(query, params=(), fetch_all=False, fetch_one=False, commit=False):
    conn = get_connection()
    c = conn.cursor()
    result = None
    try:
        c.execute(query, params)
        if commit: conn.commit()
        if fetch_one: result = c.fetchone()
        if fetch_all: result = c.fetchall()
    finally: conn.close()
    return result

# --- ٢. دیزاینە ڕەسەنەکەی خۆت (خۆڵەمێشی و پرتەقاڵی) ---
def apply_custom_style():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
        
        /* پاشبنەمای خۆڵەمێشی تۆخ */
        .stApp {
            background-color: #333333 !important;
        }
        
        /* فۆنت و ئاراستەی کوردی */
        * {
            font-family: 'Noto Sans Arabic', sans-serif;
            direction: rtl;
            text-align: right;
            color: white !important;
        }

        /* تایتڵی سەرەکی */
        .main-header {
            background-color: #222222;
            color: #FF8C00 !important;
            padding: 20px;
            text-align: center;
            border-bottom: 4px solid #FF8C00;
            margin-bottom: 25px;
            font-size: 24px;
            font-weight: bold;
        }

        /* بەتنە پرتەقاڵییەکان ڕێک وەک دیزاینەکەی خۆت */
        div.stButton > button {
            width: 100% !important;
            background-color: #FF8C00 !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 12px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            margin-top: 10px !important;
        }

        /* شوێنی داخڵکردنی زانیاری */
        input, select, textarea {
            background-color: #444444 !important;
            color: white !important;
            border: 1px solid #FF8C00 !important;
        }

        /* سایدی تەنیشت */
        [data-testid="stSidebar"] {
            background-color: #222222 !important;
            border-left: 2px solid #FF8C00;
        }
        </style>
    """, unsafe_allow_html=True)

# --- ٣. بەشەکانی سیستەم ---
def main():
    init_db()
    apply_custom_style()
    
    if 'role' not in st.session_state: st.session_state.role = None

    st.markdown("<div class='main-header'>زانکۆی پۆلیتەکنیکی گەرمیان<br><small>سیستەمی ئامادەبوونی خوێندکاران</small></div>", unsafe_allow_html=True)

    if st.session_state.role is None:
        if st.button("چوونەژوورەوەی ئەدمین"): 
            st.session_state.role = "admin_login"; st.rerun()
        if st.button("چوونەژوورەوەی مامۆستا"): 
            st.session_state.role = "teacher_login"; st.rerun()

    elif st.session_state.role == "admin_login":
        st.write("### چوونەژوورەوەی ئەدمین")
        e = st.text_input("ئیمەیڵ:")
        p = st.text_input("پاسوۆرد:", type="password")
        if st.button("چوونەژوورەوە"):
            h = hashlib.sha256(p.encode()).hexdigest()
            res = execute_query("SELECT dept FROM admins WHERE email=? AND password=?", (e, h), fetch_one=True)
            if res:
                st.session_state.dept, st.session_state.role = res[0], "admin_panel"; st.rerun()
            else: st.error("ئیمەیڵ یان پاسوۆرد هەڵەیە!")
        if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_login":
        st.write("### چوونەژوورەوەی مامۆستا")
        code = st.text_input("کۆدی مامۆستا:", type="password")
        if st.button("چوونەژوورەوە"):
            res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (code,), fetch_one=True)
            if res:
                st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
                st.session_state.role = "teacher_panel"; st.rerun()
            else: st.error("کۆدەکە هەڵەیە!")
        if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "admin_panel":
        dept = st.session_state.dept
        st.sidebar.write(f"بەشی: {dept}")
        menu = st.sidebar.radio("مەنیو", ["سەرەتا", "خوێندکاران", "مامۆستایان", "ڕاپۆرت"])

        if menu == "سەرەتا":
            st.write(f"## بەخێربێیت بۆ بەشی {dept}")
            s_count = execute_query("SELECT COUNT(*) FROM students WHERE dept=?", (dept,), fetch_one=True)[0]
            st.write(f"کۆی خوێندکارانی تۆمارکراو: {s_count}")

        elif menu == "خوێندکاران":
            st.subheader("زیادکردنی خوێندکار")
            name = st.text_input("ناوی سیانی:")
            stage = st.selectbox("قۆناغ", ["1", "2", "3", "4"])
            grp = st.selectbox("گروپ", ["A", "B", "C", "D"])
            if st.button("پاشەکەوتکردن"):
                code = f"S{random.randint(100, 999)}"
                execute_query("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)", (name, stage, grp, code, dept), commit=True)
                st.success(f"خوێندکار تۆمارکرا! کۆدەکەی: {code}")

        elif menu == "مامۆستایان":
            st.subheader("تۆمارکردنی مامۆستا")
            t_name = st.text_input("ناوی مامۆستا:")
            c_name = st.text_input("ناوی وانە:")
            t_stage = st.selectbox("بۆ قۆناغی:", ["1", "2", "3", "4"])
            if st.button("دروستکردنی کۆد"):
                t_code = f"T{random.randint(100, 999)}"
                execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)", (t_name, t_code, dept, t_stage), commit=True)
                tid = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)[0]
                execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,60,?)", (tid, c_name, dept), commit=True)
                st.info(f"کۆدی مامۆستا: {t_code}")

        if st.sidebar.button("دەرچوون"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_panel":
        tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
        st.write(f"### مامۆستا: {tname}")
        t_stage = execute_query("SELECT target_stage FROM teachers WHERE id=?", (tid,), fetch_one=True)[0]
        
        students = execute_query("SELECT id, name FROM students WHERE dept=? AND stage=?", (dept, t_stage), fetch_all=True)
        if students:
            st.write("لیستی خوێندکاران (نیشانەی غائب دابنێ):")
            for sid, sname in students:
                st.checkbox(sname, key=sid)
            if st.button("پاشەکەوتکردنی ئامادەبوون"):
                st.success("بە سەرکەوتووی تۆمارکرا")
        
        if st.sidebar.button("دەرچوون"): st.session_state.role = None; st.rerun()

if __name__ == "__main__":
    main()
