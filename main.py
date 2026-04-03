# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
from datetime import datetime

# --- Database ---
def get_connection():
    return sqlite3.connect('GPU_Attendance_System.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, dept TEXT, type TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, dept TEXT, target_stage TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, stage TEXT, grp TEXT, code TEXT UNIQUE, dept TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, teacher_id INTEGER, course_name TEXT, total_hours INTEGER, dept TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY, student_id INTEGER, course_id INTEGER, date TEXT, hours_absent INTEGER, type TEXT, dept TEXT)')
    # Default Admin
    p = hashlib.sha256("Garmian@2026".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO admins (email, password, dept, type) VALUES (?, ?, ?, ?)",
              ('admin@gpu.edu.iq', p, 'IT', 'زانکۆ'))
    conn.commit()
    conn.close()

# --- Custom Original Design (Gray & Orange) ---
def apply_style():
    st.markdown("""
        <style>
        /* باکگراوندی خۆڵەمێشی وەک دیزاینەکەی خۆت */
        .stApp {
            background-color: #424242 !important;
            color: white !important;
        }
        
        /* ستایلی بەتنەکان (Orange) */
        div.stButton > button {
            background-color: #FF8C00 !important;
            color: white !important;
            border-radius: 10px !important;
            border: 1px solid #FF8C00 !important;
            font-size: 18px !important;
            font-weight: bold !important;
            width: 100% !important;
            height: 50px !important;
            margin-top: 10px !important;
        }
        
        /* نووسینی ناو باکسەکان */
        input {
            background-color: #f0f0f0 !important;
            color: black !important;
        }

        /* ستایلی تایتڵەکە لە سەرەوە */
        .main-title {
            background-color: #333333;
            color: #FF8C00;
            padding: 20px;
            text-align: center;
            border-bottom: 5px solid #FF8C00;
            margin-bottom: 30px;
            font-size: 30px;
            font-weight: bold;
        }
        
        h1, h2, h3, p, label {
            color: white !important;
            direction: rtl;
            text-align: right;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    init_db()
    apply_style()
    
    if 'role' not in st.session_state: st.session_state.role = None

    st.markdown("<div class='main-title'>Zankoy Polytechnic Garmian</div>", unsafe_allow_html=True)

    if st.session_state.role is None:
        st.write("### تکایە جۆری چوونەژوورەوە هەڵبژێرە:")
        if st.button("LOGIN AS ADMIN"): 
            st.session_state.role = "admin_login"; st.rerun()
        if st.button("LOGIN AS TEACHER"): 
            st.session_state.role = "teacher_login"; st.rerun()

    elif st.session_state.role == "admin_login":
        st.write("### Admin Login Panel")
        e = st.text_input("Email:")
        p = st.text_input("Password:", type="password")
        if st.button("LOGIN"):
            h = hashlib.sha256(p.encode()).hexdigest()
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT dept FROM admins WHERE email=? AND password=?", (e, h))
            res = c.fetchone()
            conn.close()
            if res:
                st.session_state.dept, st.session_state.role = res[0], "admin_panel"; st.rerun()
            else: st.error("Email or Password incorrect!")
        if st.button("BACK"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_login":
        st.write("### Teacher Login Panel")
        code = st.text_input("Enter Teacher Code:", type="password")
        if st.button("LOGIN"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT id, name, dept FROM teachers WHERE code=?", (code,))
            res = c.fetchone()
            conn.close()
            if res:
                st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
                st.session_state.role = "teacher_panel"; st.rerun()
            else: st.error("Code incorrect!")
        if st.button("BACK"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "admin_panel":
        st.sidebar.write(f"بەشی {st.session_state.dept}")
        menu = st.sidebar.selectbox("Menu", ["Students", "Teachers", "Reports"])
        
        if menu == "Students":
            st.write("### Add New Student")
            name = st.text_input("Student Name:")
            stage = st.selectbox("Stage:", ["1", "2", "3", "4"])
            if st.button("SAVE"):
                code = f"S{random.randint(100, 999)}"
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO students (name, stage, code, dept) VALUES (?,?,?,?)", (name, stage, code, st.session_state.dept))
                conn.commit()
                conn.close()
                st.success(f"Saved! Student Code: {code}")

        elif menu == "Teachers":
            st.write("### Add New Teacher")
            t_name = st.text_input("Teacher Name:")
            c_name = st.text_input("Course Name:")
            if st.button("GENERATE CODE"):
                t_code = f"T{random.randint(100, 999)}"
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,'IT','1')", (t_name, t_code))
                conn.commit()
                conn.close()
                st.info(f"Teacher Code: {t_code}")

        if st.sidebar.button("LOGOUT"): st.session_state.role = None; st.rerun()

    elif st.session_state.role == "teacher_panel":
        st.write(f"### بەخێربێیت مامۆستا {st.session_state.t_name}")
        # Logic to take attendance...
        if st.sidebar.button("LOGOUT"): st.session_state.role = None; st.rerun()

if __name__ == "__main__":
    main()
