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
   except sqlite3.IntegrityError:
       return False
   finally: conn.close()
 
# --- 2. Professional UI Style (ڕەنگی تۆخ و گونجاو بۆ مۆبایل) ---
def apply_theme():
   st.markdown("""
       <style>
       @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
       
       /* ڕەنگی گشتی نووسینەکان بۆ ئەوەی لەسەر سپی دیار بن */
       html, body, [class*="st-"], .stMarkdown p, label, .stSelectbox div, .stRadio div {
           font-family: 'Noto Sans Arabic', sans-serif !important;
           direction: rtl !important;
           text-align: right !important;
           color: #000000 !important; /* ڕەنگی ڕەشی تەواو بۆ پیتەکان */
       }
       
       .stApp { background-color: #FFFFFF; }
       
       /* ستایلی بەتنەکان */
       div.stButton > button {
           background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%) !important;
           color: white !important;
           border-radius: 12px !important;
           width: 100% !important;
           min-height: 50px !important;
           font-weight: bold !important;
           font-size: 18px !important;
           border: none !important;
           box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
       }

       /* ڕەنگی ناونیشانەکان */
       h1 { color: #0F766E !important; font-weight: 700 !important; text-align: center !important; }
       h2, h3 { color: #115E59 !important; font-weight: 600 !important; }
       
       /* دیاریکردنی ڕەنگی ناو نوسینەکان (Input fields) */
       input { color: #000000 !important; background-color: #f0f2f6 !important; }

       /* ڕێکخستنی Sidebar بۆ ئەوەی لە مۆبایلدا مێنۆکە جوان بێت */
       [data-testid="stSidebar"] {
           background-color: #F8FAFC !important;
           border-left: 2px solid #0D9488 !important;
       }
       </style>
   """, unsafe_allow_html=True)
 
# --- 3. Admin Panel Logic ---
def admin_panel():
   dept = st.session_state.get('dept', 'نادیار')
   
   # لێرەدا مێنۆکە (Sidebar) دروست دەکەین کە بە کلیک لە مۆبایلدا لادەچێت و دێتەوە
   with st.sidebar:
       st.markdown(f"<h2 style='color:#0D9488;'>🏢 بەشی {dept}</h2>", unsafe_allow_html=True)
       st.divider()
       menu = st.radio("دیاریکردنی بەش:", ["👤 خوێندکاران", "👨‍🏫 مامۆستایان", "📊 ڕاپۆرتی غائیبی"])
       st.divider()
       if st.button("🚪 دەرچوون"):
           st.session_state.role = None
           st.rerun()
 
   if "خوێندکاران" in menu:
       st.markdown("### 👤 بەڕێوەبردنی خوێندکاران")
       with st.expander("➕ زیادکردنی خوێندکاری نوێ", expanded=False):
           c_edu, c_grp = st.columns(2)
           edu_type = c_edu.radio("جۆری بەش:", ["کۆلێژ", "پەیمانگا"], horizontal=True)
           stages = ["1", "2", "3", "4"] if "کۆلێژ" in edu_type else ["1", "2"]
           grp = c_grp.selectbox("گروپ:", ["A", "B", "C", "D", "E", "F"])
           name = st.text_input("ناوی سیانی خوێندکار:")
           stage = st.selectbox("قۆناغ:", stages)
           if st.button("💾 پاشەکەوتکردن"):
               if name:
                   s_code = f"S{random.randint(1000, 9999)}"
                   execute_query("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)",
                                (name, stage, grp, s_code, dept), commit=True)
                   st.success(f"خوێندکار {name} تۆمارکرا")
                   st.rerun()
 
       st.markdown("---")
       search_query = st.text_input("🔍 گەڕان بەدوای ناو یان کۆد:")
       students = execute_query("SELECT id, name, stage, grp, code FROM students WHERE dept=? AND (name LIKE ? OR code LIKE ?)",
                                (dept, f"%{search_query}%", f"%{search_query}%"), fetch_all=True)
 
       if students:
           for sid, sname, sstage, sgrp, scode in students:
               c1, c2, c3, c4 = st.columns([3, 1, 1, 1.5])
               c1.write(f"**{sname}** \n(Code: {scode})")
               c2.info(f"ق {sstage}")
               c3.info(f"گ {sgrp}")
               with c4.popover("🗑️ سڕینەوە"):
                   if st.button("بەڵێ، بسڕەوە", key=f"del_s_{sid}"):
                       execute_query("DELETE FROM students WHERE id=?", (sid,), commit=True)
                       st.rerun()
               st.divider()
 
   elif "مامۆستایان" in menu:
       st.markdown("### 👨‍🏫 بەڕێوەبردنی مامۆستایان")
       with st.expander("➕ زیادکردنی مامۆستای نوێ", expanded=False):
           with st.form("teacher_form"):
               t_name = st.text_input("ناوی سیانی مامۆستا:")
               c_name = st.text_input("ناوی وانە:")
               t_stage = st.selectbox("قۆناغ:", ["1", "2", "3", "4"])
               t_hours = st.number_input("کۆی گشتی سەعات:", min_value=1, value=30)
               if st.form_submit_button("💾 تۆمارکردن"):
                   if t_name and c_name:
                       t_code = f"T{random.randint(1000, 9999)}"
                       execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)",
                                    (t_name, t_code, dept, t_stage), commit=True)
                       tid_res = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)
                       if tid_res:
                           execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,?,?)",
                                        (tid_res[0], c_name, t_hours, dept), commit=True)
                           st.success(f"تۆمارکرا. کۆدی چوونەژوورەوە: {t_code}")
                           st.rerun()

   elif "ڕاپۆرت" in menu:
       st.markdown("### 📊 ڕاپۆرتی گشتی غائیببوون")
       sel_stage = st.selectbox("قۆناغ هەڵبژێرە:", ["1", "2", "3", "4"])
       # لێرە کۆدی ڕاپۆرتەکە جێگیر دەکرێت
 
# --- 4. Teacher Panel Logic ---
def teacher_panel():
   tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
   t_info = execute_query("SELECT target_stage FROM teachers WHERE id=?", (tid,), fetch_one=True)
   course = execute_query("SELECT id, course_name FROM courses WHERE teacher_id=?", (tid,), fetch_one=True)
   
   if not course or not t_info: st.error("وانە دیارینەکراوە"); return
   cid, cname, target_stage = course[0], course[1], t_info[0]
 
   st.markdown(f"<div style='background-color:#f0f2f6; padding:15px; border-radius:10px; border-right:5px solid #0D9488;'><h2>بەخێربێیت مامۆستا {tname}</h2><p>وانە: {cname} | قۆناغ: {target_stage}</p></div>", unsafe_allow_html=True)
   
   # دوگمەی دەرچوون بۆ مامۆستا لە ناو Sidebar
   with st.sidebar:
       if st.button("🚪 دەرچوون"):
           st.session_state.role = None
           st.rerun()

   c1, c2, c3 = st.columns(3)
   l_type = c1.selectbox("جۆری وانە:", ["تیۆری", "پراکتیکی"])
   l_date = c2.date_input("بەروار:", datetime.now())
   l_hours = c3.number_input("سەعات:", 1, 4, 2)
 
   students = execute_query("SELECT id, name FROM students WHERE dept=? AND stage=?", (dept, target_stage), fetch_all=True)
 
   if students:
       res = {}
       for sid, sname in students:
           col_n, col_r = st.columns([3, 2])
           col_n.write(f"**{sname}**")
           status = col_r.radio("", ["ئامادەیە", "ئامادەنییە"], key=f"att_{sid}", horizontal=True)
           res[sid] = l_hours if status == "ئامادەنییە" else 0
       
       if st.button("💾 پاشەکەوتکردنی ئامادەبوون"):
           for sid, h in res.items():
               execute_query("INSERT OR REPLACE INTO attendance (student_id, course_id, date, hours_absent, type, dept) VALUES (?,?,?,?,?,?)",
                            (sid, cid, str(l_date), h, l_type, dept), commit=True)
           st.success("بە سەرکەوتووی پاشەکەوتکرا")
           time.sleep(1); st.rerun()
 
# --- 5. Main Entry ---
def main():
   st.set_page_config(page_title="GPU Attendance System", layout="wide", initial_sidebar_state="expanded")
   init_db()
   apply_theme()
   
   if 'role' not in st.session_state: st.session_state.role = None
 
   if st.session_state.role is None:
       st.markdown("<h1>زانکۆی پۆلیتەکنیکی گەرمیان</h1>", unsafe_allow_html=True)
       st.markdown("<p style='text-align:center; font-size:20px; color:#115E59;'>سیستەمی پێشکەوتووی ئامادەبوونی خوێندکاران</p>", unsafe_allow_html=True)
       
       col1, col2 = st.columns(2)
       if col1.button("🔑 چوونەژوورەوەی ئەدمین"): 
           st.session_state.role = "admin_login"; st.rerun()
       if col2.button("👨‍🏫 چوونەژوورەوەی مامۆستا"): 
           st.session_state.role = "teacher_login"; st.rerun()
       st.markdown("<br><p style='text-align:center; color:gray;'>گەشەپێدەر: ئەندازیار لەنیا حازم کەریم</p>", unsafe_allow_html=True)
 
   elif st.session_state.role == "admin_login":
       st.markdown("### 🔑 چوونەژوورەوەی ئەدمین")
       email = st.text_input("ئیمەیڵ:")
       pw = st.text_input("پاسوۆرد:", type="password")
       if st.button("داخڵبوون"):
           h = hashlib.sha256(pw.encode()).hexdigest()
           res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (email, h), fetch_one=True)
           if res:
               st.session_state.dept, st.session_state.type = res[0], res[1]
               st.session_state.role = "admin_panel"; st.rerun()
           else: st.error("ئیمەیڵ یان پاسوۆرد هەڵەیە")
       if st.button("🔙 گەڕانەوە"): st.session_state.role = None; st.rerun()
 
   elif st.session_state.role == "teacher_login":
       st.markdown("### 👨‍🏫 چوونەژوورەوەی مامۆستا")
       t_code = st.text_input("کۆدی تایبەتی مامۆستا:", type="password")
       if st.button("داخڵبوون"):
           res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (t_code,), fetch_one=True)
           if res:
               st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
               st.session_state.role = "teacher_panel"; st.rerun()
           else: st.error("کۆدەکە هەڵەیە")
       if st.button("🔙 گەڕانەوە"): st.session_state.role = None; st.rerun()
 
   elif st.session_state.role == "admin_panel":
       if st.session_state.get('type') == "زانکۆ":
           st.markdown("### 🏛️ بەڕێوەبردنی بەشەکانی زانکۆ")
           with st.form("new_dept"):
               e = st.text_input("ئیمەیڵ بۆ بەش:")
               p = st.text_input("پاسوۆرد بۆ بەش:", type="password")
               d = st.selectbox("ناوی بەشەکە:", ["ئەندازیاری کارەبا و کۆمپیوتەر", "شیکاری نەخۆشیەکان", "تەکنیکی پەرستاری", "تەکنەلۆجیای زانیاری", "کارگێڕی کار"])
               if st.form_submit_button("➕ دروستکردنی ئەکاونت"):
                   hp = hashlib.sha256(p.encode()).hexdigest()
                   if execute_query("INSERT INTO admins (email, password, dept, type) VALUES (?,?,?,?)", (e, hp, d, "بەش"), commit=True):
                       st.success(f"ئەکاونتی بەشی {d} بە سەرکەوتووی دروستکرا")
                   else: st.error("ئەم ئیمەیڵە پێشتر بەکارهاتووە")
           if st.sidebar.button("🚪 دەرچوون"): st.session_state.role = None; st.rerun()
       else:
           admin_panel()
 
   elif st.session_state.role == "teacher_panel":
       teacher_panel()
 
if __name__ == "__main__":
   main()
