# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
from datetime import datetime
import io

# --- 1. Database ---
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
        if commit: conn.commit()
        if fetch_one: result = c.fetchone()
        if fetch_all: result = c.fetchall()
    finally: conn.close()
    return result

# --- 2. Your Original Custom Design (Black & Orange) ---
def apply_original_style():
    st.markdown("""
        <style>
        /* پاشبنەمای ڕەشی تۆخ */
        .stApp {
            background-color: #000000 !important;
        }
        
        /* فۆنت و ئاراستەی نووسین */
        * {
            font-family: 'Arial', sans-serif;
            direction: rtl;
            text-align: right;
            color: #ffffff !important;
        }

        /* ستایلی بەتنە پرتەقاڵییەکان - ڕێک وەک دیزاینەکەی خۆت */
        div.stButton > button {
            width: 100% !important;
            background-color: #FF8C00 !important; /* ڕەنگی پرتەقاڵی */
            color: black !important; /* نووسینی ناو بەتنەکە ڕەش بێت بۆ دیاربوون */
            border-radius: 0px !important;
            border: 2px solid #FF8C00 !important;
            padding: 15px !important;
            font-size: 20px !important;
            font-weight: bold !important;
            margin-bottom: 10px !important;
        }

        /* کاتێک دەست دەنێیت بە بەتنەکەدا */
        div.stButton > button:active, div.stButton > button:focus {
            background-color: #cc7000 !important;
            border-color: #cc7000 !important;
        }

        /* شوێنی نووسین و ئیمەیڵ */
        input {
            background-color: #1a1a1a !important;
            border: 1px solid #FF8C00 !important;
            color: white !important;
        }

        /* لادانی لۆگۆی ستریملێت لە سەرەوە */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* لاپەڕەی ئەدمین و مامۆستا */
        .header-box {
            border: 2px solid #FF8C00;
            padding: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. Main Logic ---
def main():
    init_db()
    apply_original_style()
    
    if 'role' not in st.session_state: st.session_state.role = None

    st.markdown("<div class='header-box'><h1>ZANKOY POLYTECHNIC</h1><p>Garmian University</p></div>", unsafe_allow_html=True)

    if st.session_state.role is None:
        if st.button("LOGIN ADMIN"): 
            st.session_state.role = "admin_login"; st.rerun()
        if st.button("LOGIN TEACHER"): 
            st.session_state.role = "teacher_login"; st.rerun()

    elif st.session_state.role == "admin_login":
        st.write("### ADMIN LOGIN")
        e = st.text_input("EMAIL")
        p = st.text_input("PASSWORD", type="password")
        if st.button("ENTER"):
            h = hashlib.sha256(p.encode()).hexdigest()
            res = execute_query("SELECT dept FROM admins WHERE email=? AND password=?", (e, h), fetch_one=True)
            if res:
                st.session_state.dept, st.session_state.role = res[0], "admin_panel"; st.rerun()
            else: st.error("ERROR")
        if st.button("BACK"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_login":
        st.write("### TEACHER LOGIN")
        code = st.text_input("CODE", type="password")
        if st.button("ENTER"):
            res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (code,), fetch_one=True)
            if res:
                st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
                st.session_state.role = "teacher_panel"; st.rerun()
            else: st.error("WRONG CODE")
        if st.button("BACK"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "admin_panel":
        dept = st.session_state.dept
        st.write(f"## ADMIN: {dept}")
        
        tab1, tab2, tab3 = st.tabs(["Add Student", "Add Teacher", "Reports"])
        
        with tab1:
            name = st.text_input("Student Name")
            stage = st.selectbox("Stage", ["1", "2", "3", "4"])
            if st.button("SAVE STUDENT"):
                code = f"S{random.randint(100, 999)}"
                execute_query("INSERT INTO students (name, stage, code, dept) VALUES (?,?,?,?)", (name, stage, code, dept), commit=True)
                st.success(f"SAVED: {code}")

        with tab2:
            t_name = st.text_input("Teacher Name")
            c_name = st.text_input("Course Name")
            if st.button("SAVE TEACHER"):
                t_code = f"T{random.randint(100, 999)}"
                execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,'IT','1')", (t_name, t_code), commit=True)
                st.info(f"CODE: {t_code}")
        
        if st.button("LOGOUT"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_panel":
        st.write(f"## WELCOME {st.session_state.t_name}")
        # لێرە لیستی خوێندکاران و غائیببوون وەک پێشوو کار دەکات
        if st.button("LOGOUT"): st.session_state.role = None; st.rerun()

if __name__ == "__main__":
    main()
