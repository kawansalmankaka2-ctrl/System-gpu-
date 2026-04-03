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
def init_db():
   conn = sqlite3.connect('GPU_Attendance_Final.db')
   c = conn.cursor()
   c.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, dept TEXT, type TEXT)')
   c.execute('CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, dept TEXT, target_stage TEXT)')
   c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, stage TEXT, grp TEXT, code TEXT UNIQUE, dept TEXT)')
   c.execute('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, teacher_id INTEGER, course_name TEXT, total_hours INTEGER, dept TEXT)')
   c.execute('''CREATE TABLE IF NOT EXISTS attendance
                (id INTEGER PRIMARY KEY, student_id INTEGER, course_id INTEGER, date TEXT,
                 hours_absent INTEGER, status INTEGER, type TEXT, dept TEXT,
                 UNIQUE(student_id, course_id, date, type))''')
   
   p = hashlib.sha256("Garmian@2026".encode()).hexdigest()
   c.execute("INSERT OR IGNORE INTO admins (email, password, dept, type) VALUES (?, ?, ?, ?)",
             ('admin@gpu.edu.iq', p, 'ڕاگرایەتی', 'زانکۆ'))
   conn.commit()
   conn.close()

def execute_query(query, params=(), fetch_all=False, fetch_one=False, commit=False):
   conn = sqlite3.connect('GPU_Attendance_Final.db')
   c = conn.cursor()
   result = None
   try:
       c.execute(query, params)
       if commit: 
           conn.commit()
           result = True
       elif fetch_one: 
           result = c.fetchone()
       elif fetch_all: 
           result = c.fetchall()
   finally: 
       conn.close()
   return result

# --- 2. Professional UI Style (Your Design Maintained) ---
def apply_theme():
   st.markdown("""
       <style>
       @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
       html, body, [class*="st-"] {
           font-family: 'Noto Sans Arabic', sans-serif;
           direction: rtl;
           text-align: right;
       }
       .stApp { background-color: #FFFFFF; }
       .stButton>button {
           background: linear-gradient(135deg, #40E0D0 0%, #008B8B 100%);
           color: white !important;
           border-radius: 10px;
           width: 100%;
           font-weight: bold;
           border: none;
       }
       .stat-card {
           background-color: #F7FCFC;
           padding: 20px;
           border-radius: 15px;
           border-right: 5px solid #40E0D0;
           margin-bottom: 20px;
           box-shadow: 0 2px 5px rgba(0,0,0,0.05);
       }
       h1 { color: #008B8B !important; margin-bottom: 5px; }
       h2 { color: #008B8B !important; margin-top: 0px; }
       </style>
   """, unsafe_allow_html=True)

# --- 3. Admin Panel Logic ---
def admin_panel():
   dept = st.session_state.dept
   st.sidebar.markdown(f"### بەشی {dept}")
   menu = st.sidebar.selectbox("مەنیو", ["خوێندکاران", "مامۆستایان", "ڕاپۆرت"])

   if menu == "خوێندکاران":
       st.markdown("### بەڕێوەبردنی خوێندکاران")
       with st.expander("زیادکردنی خوێندکاری نوێ", expanded=False):
           c_edu, c_grp = st.columns(2)
           edu_type = c_edu.radio("جۆری بەش:", ["کۆلێژ", "پەیمانگا"], horizontal=True)
           stages = ["1", "2", "3", "4"] if "کۆلێژ" in edu_type else ["1", "2"]
           grp = c_grp.selectbox("گروپ:", ["A", "B", "C", "D", "E", "F"])
           name = st.text_input("ناوی سیانی خوێندکار:")
           stage = st.selectbox("قۆناغ:", stages)
           if st.button("پاشەکەوتکردن"):
               if name:
                   s_code = f"S{random.randint(1000, 9999)}"
                   execute_query("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)",
                                (name, stage, grp, s_code, dept), commit=True)
                   st.success(f"خوێندکار {name} تۆمارکرا")
                   st.rerun()

       st.markdown("---")
       search_query = st.text_input("گەڕان بەدوای ناو یان کۆد:")
       students = execute_query("SELECT id, name, stage, grp, code FROM students WHERE dept=? AND (name LIKE ? OR code LIKE ?)",
                                (dept, f"%{search_query}%", f"%{search_query}%"), fetch_all=True)

       if students:
           for sid, sname, sstage, sgrp, scode in students:
               c1, c2, c3, c4 = st.columns([3, 1, 1, 1.5])
               c1.write(f"**{sname}** (کۆد: {scode})")
               c2.info(f"قۆناغی {sstage}")
               c3.info(f"گروپی {sgrp}")
               if c4.button("سڕینەوە", key=f"del_s_{sid}"):
                   execute_query("DELETE FROM students WHERE id=?", (sid,), commit=True)
                   st.rerun()
               st.divider()

   elif menu == "مامۆستایان":
       st.markdown("### بەڕێوەبردنی مامۆستایان")
       with st.form("teacher_form"):
           t_name = st.text_input("ناوی سیانی مامۆستا:")
           c_name = st.text_input("ناوی وانە:")
           t_stage = st.selectbox("بۆ چ قۆناغێک:", ["1", "2", "3", "4"])
           t_hours = st.number_input("سەعاتی وانە:", 1, 150, 30)
           if st.form_submit_button("تۆمارکردن"):
               t_code = f"T{random.randint(1000, 9999)}"
               execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)",
                            (t_name, t_code, dept, t_stage), commit=True)
               tid = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)[0]
               execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,?,?)",
                            (tid, c_name, t_hours, dept), commit=True)
               st.success(f"تۆمارکرا. کۆد: {t_code}")

   elif menu == "ڕاپۆرت":
       st.markdown("### ڕاپۆرتی گشتی")
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
           st.dataframe(pd.DataFrame(report))

# --- 4. Teacher Panel Logic ---
def teacher_panel():
   tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
   t_info = execute_query("SELECT target_stage FROM teachers WHERE id=?", (tid,), fetch_one=True)
   course = execute_query("SELECT id, course_name FROM courses WHERE teacher_id=?", (tid,), fetch_one=True)
   if not course or not t_info: st.error("زانیاری مامۆستا نەدۆزرایەوە"); return
   cid, cname, target_stage = course[0], course[1], t_info[0]

   st.markdown(f"<div class='stat-card'><h2>{tname}</h2><p>وانە: {cname} | قۆناغ: {target_stage}</p></div>", unsafe_allow_html=True)
   l_hours = st.number_input("سەعات:", 1, 4, 2)
   
   students = execute_query("SELECT id, name FROM students WHERE dept=? AND stage=?", (dept, target_stage), fetch_all=True)
   if students:
       res = {}
       for sid, sname in students:
           col_n, col_r = st.columns([3, 2])
           col_n.write(sname)
           status = col_r.radio("", ["ئامادەیە", "نەهاتووە"], key=f"att_{sid}", horizontal=True)
           res[sid] = l_hours if status == "نەهاتووە" else 0
       
       if st.button("پاشەکەوتکردن"):
           for sid, h in res.items():
               execute_query("INSERT OR REPLACE INTO attendance (student_id, course_id, date, hours_absent, type, dept) VALUES (?,?,?,?,?,?)",
                            (sid, cid, str(datetime.now().date()), h, "گشتی", dept), commit=True)
           st.success("بە سەرکەوتووی تۆمارکرا")

# --- 5. Main Entry ---
def main():
   st.set_page_config(page_title="Garmian Polytechnic University", layout="wide")
   init_db()
   apply_theme()
   
   if 'role' not in st.session_state: st.session_state.role = None
 
   st.markdown("<h1 style='text-align:center;'>زانکۆی پۆلیتەکنیکی گەرمیان</h1>", unsafe_allow_html=True)
   
   if st.session_state.role is None:
       col1, col2 = st.columns(2)
       if col1.button("چوونەژوورەوەی ئەدمین"): st.session_state.role = "admin_login"; st.rerun()
       if col2.button("چوونەژوورەوەی مامۆستا"): st.session_state.role = "teacher_login"; st.rerun()
 
   elif st.session_state.role == "admin_login":
       email = st.text_input("ئیمەیڵ:")
       pw = st.text_input("پاسوۆرد:", type="password")
       if st.button("داخڵبوون"):
           h = hashlib.sha256(pw.encode()).hexdigest()
           res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (email, h), fetch_one=True)
           if res:
               st.session_state.dept, st.session_state.type = res[0], res[1]
               st.session_state.role = "admin_panel"; st.rerun()
           else: st.error("هەڵەیە")
       if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()
 
   elif st.session_state.role == "teacher_login":
       t_code = st.text_input("کۆدی مامۆستا:", type="password")
       if st.button("داخڵبوون"):
           res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (t_code,), fetch_one=True)
           if res:
               st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
               st.session_state.role = "teacher_panel"; st.rerun()
           else: st.error("کۆدەکە هەڵەیە")
       if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()
 
   elif st.session_state.role == "admin_panel":
       admin_panel()
       if st.sidebar.button("دەرچوون"): st.session_state.role = None; st.rerun()
 
   elif st.session_state.role == "teacher_panel":
       teacher_panel()
       if st.sidebar.button("دەرچوون"): st.session_state.role = None; st.rerun()
 
if __name__ == "__main__":
   main()
