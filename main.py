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
   try:
       c.execute(query, params)
       if commit: conn.commit(); return True
       if fetch_one: return c.fetchone()
       if fetch_all: return c.fetchall()
   finally: conn.close()
 
# --- 2. Professional UI Style (ONLY MODIFIED FOR MOBILE BUTTONS) ---
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
       
       /* ڕێکخستنی بەتنەکان بۆ مۆبایل */
       .stButton>button {
           background: linear-gradient(135deg, #40E0D0 0%, #008B8B 100%) !important;
           color: white !important;
           border-radius: 12px !important;
           width: 100% !important;
           min-height: 50px !important;
           font-weight: bold !important;
           font-size: 18px !important;
           border: none !important;
           margin-top: 10px !important;
           box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
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
       
       /* جێگیرکردنی Sidebar لە مۆبایلدا */
       @media (max-width: 768px) {
           [data-testid="stSidebar"] {
               min-width: 100% !important;
           }
       }
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
               c1.write(f"**{sname}** (Code: {scode})")
               c2.info(f"قۆناغی {sstage}")
               c3.info(f"گروپی {sgrp}")
               with c4.popover("سڕینەوە"):
                   st.write("ئایا دڵنیای لە سڕینەوە؟")
                   if st.button("بەڵێ، بسڕەوە", key=f"del_s_{sid}"):
                       execute_query("DELETE FROM students WHERE id=?", (sid,), commit=True)
                       execute_query("DELETE FROM attendance WHERE student_id=?", (sid,), commit=True)
                       st.rerun()
               st.divider()
 
   elif menu == "مامۆستایان":
       st.markdown("### بەڕێوەبردنی مامۆستایان")
       with st.expander("زیادکردنی مامۆستای نوێ", expanded=False):
           with st.form("teacher_form"):
               col1, col2 = st.columns(2)
               with col1:
                   t_name = st.text_input("ناوی سیانی مامۆستا:")
                   c_name = st.text_input("ناوی وانە:")
               with col2:
                   t_stage = st.selectbox("بۆ چ قۆناغێک وانە دەڵێتەوە؟:", ["1", "2", "3", "4"])
                   t_hours = st.number_input("کۆی گشتی سەعاتی وانە:", min_value=1, value=30)
               
               if st.form_submit_button("تۆمارکردنی مامۆستا"):
                   if t_name and c_name:
                       t_code = f"T{random.randint(1000, 9999)}"
                       execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)",
                                    (t_name, t_code, dept, t_stage), commit=True)
                       tid = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)[0]
                       execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,?,?)",
                                    (tid, c_name, t_hours, dept), commit=True)
                       st.success(f"تۆمارکرا. کۆدی چوونەژوورەوە: {t_code}")
                       st.rerun()
 
       st.markdown("---")
       st.markdown("### لیستی مامۆستایان")
       t_data = execute_query("""SELECT t.id, t.code, t.name, c.course_name, t.target_stage
                                 FROM teachers t JOIN courses c ON t.id = c.teacher_id
                                 WHERE t.dept=?""", (dept,), fetch_all=True)
       if t_data:
           h1, h2, h3, h4, h5 = st.columns([1.5, 2.5, 2, 1, 1.5])
           h1.write("**کۆد**"); h2.write("**ناوی مامۆستا**"); h3.write("**وانە**"); h4.write("**قۆناغ**"); h5.write("**کردارەکان**")
           st.divider()
           for tid, tcode, tname, tcours, tstage in t_data:
               col1, col2, col3, col4, col5 = st.columns([1.5, 2.5, 2, 1, 1.5])
               col1.text(tcode); col2.text(tname); col3.text(tcours); col4.text(tstage)
               with col5.popover("سڕینەوە"):
                   st.warning("دڵنیای لە سڕینەوە؟")
                   if st.button("بەڵێ، بسڕەوە", key=f"del_t_{tid}"):
                       execute_query("DELETE FROM teachers WHERE id=?", (tid,), commit=True)
                       execute_query("DELETE FROM courses WHERE teacher_id=?", (tid,), commit=True)
                       st.rerun()
 
   elif menu == "ڕاپۆرت":
       st.markdown("### ڕاپۆرتی گشتی غائیببوون")
       sel_stage = st.selectbox("قۆناغ هەڵبژێرە:", ["1", "2", "3", "4"])
       st_list = execute_query("SELECT id, name, grp FROM students WHERE stage=? AND dept=?", (sel_stage, dept), fetch_all=True)
       co_list = execute_query("SELECT id, course_name, total_hours FROM courses WHERE dept=?", (dept,), fetch_all=True)
       
       if st_list and co_list:
           report_data = []
           for sid, sname, sgrp in st_list:
               row = {"ناو": sname, "گروپ": sgrp}
               for cid, cname, thours in co_list:
                   abs_sum = execute_query("SELECT SUM(hours_absent) FROM attendance WHERE student_id=? AND course_id=?", (sid, cid), fetch_one=True)[0] or 0
                   row[cname] = f"{(abs_sum/thours)*100:.1f}%"
               report_data.append(row)
           
           df = pd.DataFrame(report_data)
           st.dataframe(df, use_container_width=True)
           
           towrite = io.BytesIO()
           df.to_excel(towrite, index=False, engine='openpyxl')
           st.download_button(label="دابەزاندنی ڕاپۆرت (Excel)", data=towrite.getvalue(),
                              file_name=f"Report_Stage_{sel_stage}_{dept}.xlsx",
                              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
 
# --- 4. Teacher Panel Logic ---
def teacher_panel():
   tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
   t_info = execute_query("SELECT target_stage FROM teachers WHERE id=?", (tid,), fetch_one=True)
   course = execute_query("SELECT id, course_name FROM courses WHERE teacher_id=?", (tid,), fetch_one=True)
   if not course or not t_info: st.error("وانە دیارینەکراوە"); return
   cid, cname, target_stage = course[0], course[1], t_info[0]
 
   st.markdown(f"""<div class='stat-card'><h2>مامۆستا: {tname}</h2><p>وانە: {cname} | قۆناغ: {target_stage} | بەش: {dept}</p></div>""", unsafe_allow_html=True)
   c1, c2, c3 = st.columns(3)
   l_type = c1.selectbox("جۆری وانە:", ["تیۆری", "پراکتیکی"])
   l_date = c2.date_input("بەروار:", datetime.now())
   l_hours = c3.number_input("سەعات:", 1, 4, 2)
 
   if l_type == "پراکتیکی":
       grp = st.selectbox("گروپ:", ["A", "B", "C", "D", "E", "F"])
       students = execute_query("SELECT id, name FROM students WHERE dept=? AND stage=? AND grp=?", (dept, target_stage, grp), fetch_all=True)
   else:
       students = execute_query("SELECT id, name FROM students WHERE dept=? AND stage=?", (dept, target_stage), fetch_all=True)
 
   if students:
       res = {}
       for sid, sname in students:
           col_n, col_r = st.columns([3, 2])
           col_n.write(sname)
           status = col_r.radio("", ["ئامادەیە", "ئامادەنییە"], key=f"att_{sid}", horizontal=True)
           res[sid] = l_hours if status == "ئامادەنییە" else 0
       
       if st.button("پاشەکەوتکردن"):
           for sid, h in res.items():
               execute_query("INSERT OR REPLACE INTO attendance (student_id, course_id, date, hours_absent, type, dept) VALUES (?,?,?,?,?,?)",
                            (sid, cid, str(l_date), h, l_type, dept), commit=True)
           st.success("تۆمارکردن بەسەرکەوتووی ئەنجامدرا")
           time.sleep(1); st.rerun()
 
# --- 5. Main Entry ---
def main():
   st.set_page_config(page_title="Garmian Polytechnic University", layout="wide")
   init_db()
   apply_theme()
   
   col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
   with col_l2:
       try:
           st.image("https://garmian.edu.iq/wp-content/uploads/2019/10/gpu-logo.png", width=150)
       except: pass
 
   st.markdown("<h1 style='text-align:center;'>زانکۆی پۆلیتەکنیکی گەرمیان</h1>", unsafe_allow_html=True)
   st.markdown("<h2 style='text-align:center; font-size: 24px;'>سیستەمی ئامادەبوونی خوێندکاران</h2>", unsafe_allow_html=True)
   
   if 'role' not in st.session_state: st.session_state.role = None
 
   if st.session_state.role is None:
       col1, col2 = st.columns(2)
       if col1.button("چوونەژوورەوەی ئەدمین"): st.session_state.role = "admin_login"; st.rerun()
       if col2.button("چوونەژوورەوەی مامۆستا"): st.session_state.role = "teacher_login"; st.rerun()
       st.markdown("<br><p style='text-align:center; color:gray;'>گەشەپێدەر: ئەندازیار لەنیا حازم کەریم</p>", unsafe_allow_html=True)
 
   elif st.session_state.role == "admin_login":
       email = st.text_input("ئیمەیڵ:")
       pw = st.text_input("پاسوۆرد:", type="password")
       if st.button("داخڵبوون"):
           h = hashlib.sha256(pw.encode()).hexdigest()
           res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (email, h), fetch_one=True)
           if res:
               st.session_state.dept, st.session_state.type = res[0], res[1]
               st.session_state.role = "admin_panel"; st.rerun()
           else: st.error("ئیمەیڵ یان پاسوۆرد هەڵەیە")
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
       if st.session_state.type == "زانکۆ":
           st.markdown("### بەڕێوەبردنی بەشەکان (ڕاگرایەتی)")
           with st.form("new_dept"):
               e, p = st.text_input("ئیمەیڵ:"), st.text_input("پاسوۆرد:", type="password")
               d = st.selectbox("بەش:", ["ئەندازیاری کارەبا و کۆمپیوتەر", "شیکاری نەخۆشیەکان", "تەکنیکی پەرستاری", "تەکنەلۆجیای زانیاری", "کارگێڕی کار"])
               if st.form_submit_button("دروستکردنی ئەکاونتی بەش"):
                   hp = hashlib.sha256(p.encode()).hexdigest()
                   execute_query("INSERT INTO admins (email, password, dept, type) VALUES (?,?,?,?)", (e, hp, d, "بەش"), commit=True)
                   st.success("ئەکاونتی بەش بە سەرکەوتووی دروستکرا")
       else: admin_panel()
       if st.sidebar.button("دەرچوون"): st.session_state.role = None; st.rerun()
 
   elif st.session_state.role == "teacher_panel":
       teacher_panel()
       if st.sidebar.button("دەرچوون"): st.session_state.role = None; st.rerun()
 
if __name__ == "__main__":
   main()
