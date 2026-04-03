# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
import io
from datetime import datetime

# --- 1. Database Logic ---
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

# --- 2. Ultra-Stable Mobile UI ---
def apply_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
        html, body, [class*="st-"] { font-family: 'Noto Sans Arabic', sans-serif; direction: rtl; text-align: right; }
        
        /* لابردنی Sidebar بۆ ئەوەی شاشەکە تێک نەچێت */
        [data-testid="stSidebar"] { display: none !important; }
        
        .stApp { background-color: #F8FAFC; }
        
        .main-card { 
            background: #FFFFFF; 
            padding: 25px; 
            border-radius: 20px; 
            border-top: 8px solid #0D9488; 
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); 
            margin-bottom: 20px; 
            text-align: center; 
        }

        div.stButton > button { 
            width: 100% !important; 
            height: 60px; 
            background: #0D9488 !important; 
            color: white !important; 
            border-radius: 15px; 
            font-weight: bold; 
            font-size: 18px; 
            border: none; 
            margin-top: 10px;
            box-shadow: 0 4px 6px rgba(13, 148, 136, 0.2);
        }
        
        .logout-btn > div > button { background: #EF4444 !important; }

        h1, h2, h3 { color: #0F172A !important; font-weight: 700 !important; }
        label { color: #334155 !important; font-weight: 600 !important; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. UI Sections ---

def show_header():
    st.markdown("<div class='main-card'><h1>زانکۆی پۆلیتەکنیکی گەرمیان</h1><p>سیستەمی پێشکەوتووی ئامادەبوونی خوێندکاران</p></div>", unsafe_allow_html=True)

def login_screen():
    show_header()
    st.markdown("<div class='main-card'><h3>بەخێربێیت، تکایە جۆری چوونەژوورەوە هەڵبژێرە</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    if col1.button("🔑 ئەدمین"): 
        st.session_state.page = "login_admin"; st.rerun()
    if col2.button("🌙 مامۆستا"): 
        st.session_state.page = "login_teacher"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def super_admin_panel():
    show_header()
    st.markdown("<div class='main-card'><h2>پانێڵی ڕاگرایەتی</h2><p>بەڕێوەبردنی بەشەکان</p></div>", unsafe_allow_html=True)
    with st.expander("➕ زیادکردنی بەشی نوێ", expanded=True):
        dept_name = st.selectbox("ناو:", ["تەکنەلۆجیای زانیاری", "کارگێڕی کار", "پەرستاری", "ئەندازیاری"])
        email = st.text_input("ئیمەیڵ:")
        pw = st.text_input("پاسوۆرد:", type="password")
        if st.button("تۆمارکردن"):
            hp = hashlib.sha256(pw.encode()).hexdigest()
            execute_query("INSERT INTO admins (email, password, dept, type) VALUES (?,?,?,?)", (email, hp, dept_name, "DeptAdmin"), commit=True)
            st.success(f"بەشی {dept_name} بە سەرکەوتووی تۆمارکرا")
    
    st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
    if st.button("🚪 دەرچوون"): st.session_state.clear(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def dept_admin_panel():
    show_header()
    dept = st.session_state.dept
    st.markdown(f"<div class='main-card'><h2>بەشی {dept}</h2></div>", unsafe_allow_html=True)
    
    choice = st.selectbox("کارێک هەڵبژێرە:", ["سەرەتا", "تۆمارکردنی خوێندکار", "تۆمارکردنی مامۆستا", "ڕاپۆرتی گشتی"])
    
    if choice == "تۆمارکردنی خوێندکار":
        with st.form("s_form"):
            name = st.text_input("ناوی خوێندکار:")
            stage = st.selectbox("قۆناغ:", ["1","2","3","4"])
            grp = st.selectbox("گروپ:", ["A","B","C","D"])
            if st.form_submit_button("پاشەکەوت"):
                code = f"S{random.randint(1000,9999)}"
                execute_query("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)", (name, stage, grp, code, dept), commit=True)
                st.success(f"تۆمارکرا. کۆد: {code}")

    elif choice == "تۆمارکردنی مامۆستا":
        with st.form("t_form"):
            name = st.text_input("ناوی مامۆستا:")
            c_name = st.text_input("ناوی وانە:")
            stage = st.selectbox("قۆناغی وانە:", ["1","2","3","4"])
            if st.form_submit_button("پاشەکەوت"):
                code = f"T{random.randint(1000,9999)}"
                execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)", (name, code, dept, stage), commit=True)
                st.success(f"تۆمارکرا. کۆدی مامۆستا: {code}")

    if st.button("🚪 دەرچوون", key="logout"): st.session_state.clear(); st.rerun()

# --- Main App Logic ---
def main():
    init_db()
    apply_theme()
    
    if 'page' not in st.session_state: st.session_state.page = "home"
    if 'role' not in st.session_state: st.session_state.role = None

    if st.session_state.page == "home":
        login_screen()
    
    elif st.session_state.page == "login_admin":
        show_header()
        st.markdown("<div class='main-card'><h3>چوونەژوورەوەی ئەدمین</h3>", unsafe_allow_html=True)
        email = st.text_input("ئیمەیڵ:")
        pw = st.text_input("پاسوۆرد:", type="password")
        if st.button("داخڵبوون"):
            h = hashlib.sha256(pw.encode()).hexdigest()
            res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (email, h), fetch_one=True)
            if res:
                st.session_state.role = res[1]
                st.session_state.dept = res[0]
                st.session_state.page = "panel"
                st.rerun()
            else: st.error("هەڵەیە")
        if st.button("🔙 گەڕانەوە"): st.session_state.page = "home"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "panel":
        if st.session_state.role == "SuperAdmin":
            super_admin_panel()
        elif st.session_state.role == "DeptAdmin":
            dept_admin_panel()

if __name__ == "__main__":
    main()
