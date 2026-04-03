# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
import time
from datetime import datetime

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

# --- 2. Professional UI Style (ڕێکخراو بۆ مۆبایل و ڕەنگی تۆخ) ---
def apply_theme():
   st.markdown("""
       <style>
       @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
       
       html, body, [class*="st-"], .stMarkdown p, label {
           font-family: 'Noto Sans Arabic', sans-serif !important;
           direction: rtl !important;
           text-align: right !important;
           color: #000000 !important;
       }
       
       .stApp { background-color: #FFFFFF; }
       
       [data-testid="stSidebar"] {
           min-width: 280px !important;
           background-color: #f8fafc !important;
           border-left: 3px solid #008080 !important;
       }
       
       [data-testid="stSidebar"] .stMarkdown p {
           white-space: nowrap !important;
       }

       div.stButton > button {
           background-color: #008080 !important;
           color: white !important;
           border-radius: 12px !important;
           padding: 10px 20px !important;
           width: 100% !important;
           font-weight: bold !important;
           font-size: 16px !important;
           box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
       }
       
       h1 { color: #004d4d !important; text-align: center; }
       h2, h3 { color: #006666 !important; }
       
       /* ستایلی خشتەکان */
       .stDataFrame, .stTable {
           background-color: white !important;
           border-radius: 10px !important;
           border: 1px solid #e6e6e6 !important;
       }
       </style>
   """, unsafe_allow_html=True)

# --- 3. Admin Panel Logic ---
def admin_panel():
   dept = st.session_state.get('dept', 'بەش')
   with st.sidebar:
       st.markdown(f"### 🏢 بەشی {dept}")
       st.divider()
       menu = st.radio("مەنیو:", ["👤 خوێندکاران", "👨‍🏫 مامۆستایان", "📊 ڕاپۆرتی گشتی"])
       st.divider()
       if st.button("🚪 دەرچوون"):
           st.session_state.role = None
           st.rerun()

   if "خوێندکاران" in menu:
       st.markdown("### 👤 بەڕێوەبردنی خوێندکاران")
       with st.expander("➕ زیادکردنی خوێندکار"):
           name = st.text_input("ناوی خوێندکار:")
           stage = st.selectbox("قۆناغ:", ["1", "2", "3", "4"])
           grp = st.selectbox("گروپ:", ["A", "B", "C", "D"])
           if st.button("تۆمارکردن"):
               if name:
                   s_code = f"S{random.randint(1000, 9999)}"
                   execute_query("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)",
                                (name, stage, grp, s_code, dept), commit=True)
                   st.success(f"خوێندکار {name} تۆمارکرا")
                   st.rerun()

   elif "مامۆستایان" in menu:
       st.markdown("### 👨‍🏫 بەڕێوەبردنی مامۆستایان")
       
       with st.expander("➕ زیادکردنی مامۆستای نوێ"):
           with st.form("teacher_reg"):
               t_name = st.text_input("ناوی مامۆستا:")
               c_name = st.text_input("ناوی وانە:")
               t_stage = st.selectbox("قۆناغ:", ["1", "2", "3", "4"])
               if st.form_submit_button("💾 پاشەکەوتکردن"):
                   if t_name and c_name:
                       t_code = f"T{random.randint(1000, 9999)}"
                       execute_query("INSERT INTO teachers (name, code, dept, target_stage) VALUES (?,?,?,?)",
                                    (t_name, t_code, dept, t_stage), commit=True)
                       tid = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)[0]
                       execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,?,?)",
                                    (tid, c_name, 30, dept), commit=True)
                       st.success(f"تۆمارکرا. کۆدی چوونەژوورەوە: {t_code}")
                       st.rerun()

       st.markdown("---")
       st.markdown("#### 📋 لیستی مامۆستایان و زانیارییەکان")
       
       query = """
           SELECT t.name, c.course_name, t.target_stage, t.code,
           (SELECT COUNT(*) FROM students s WHERE s.dept = t.dept AND s.stage = t.target_stage) as st_count
           FROM teachers t
           JOIN courses c ON t.id = c.teacher_id
           WHERE t.dept = ?
       """
       data = execute_query(query, (dept,), fetch_all=True)
       
       if data:
           df = pd.DataFrame(data, columns=["ناوی مامۆستا", "وانە", "قۆناغ", "کۆدی چوونەژوورەوە", "ژمارەی خوێندکار"])
           st.table(df)
       else:
           st.info("هیچ مامۆستایەک نییە.")

# --- 4. Teacher Panel Logic ---
def teacher_panel():
   tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
   course = execute_query("SELECT id, course_name FROM courses WHERE teacher_id=?", (tid,), fetch_one=True)
   t_info = execute_query("SELECT target_stage FROM teachers WHERE id=?", (tid,), fetch_one=True)
   
   if not course: st.error("وانە دیاری نەکراوە"); return
   cid, cname, target_stage = course[0], course[1], t_info[0]
 
   st.markdown(f"### 👨‍🏫 مامۆستا {tname}")
   st.info(f"وانە: {cname} | قۆناغ: {target_stage}")
   
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
       
       if st.button("💾 پاشەکەوتکردن"):
           for sid, h in res.items():
               execute_query("INSERT OR REPLACE INTO attendance (student_id, course_id, date, hours_absent, type, dept) VALUES (?,?,?,?,?,?)",
                            (sid, cid, str(l_date), h, l_type, dept), commit=True)
           st.success("تۆمارکرا")
           time.sleep(1); st.rerun()

# --- 5. Main Entry ---
def main():
   st.set_page_config(page_title="GPU System", layout="wide")
   init_db()
   apply_theme()
   
   if 'role' not in st.session_state: st.session_state.role = None
 
   if st.session_state.role is None:
       st.markdown("<h1>زانکۆی پۆلیتەکنیکی گەرمیان</h1>", unsafe_allow_html=True)
       col1, col2 = st.columns(2)
       if col1.button("🔑 چوونەژوورەوەی ئەدمین"): st.session_state.role = "admin_login"; st.rerun()
       if col2.button("👨‍🏫 چوونەژوورەوەی مامۆستا"): st.session_state.role = "teacher_login"; st.rerun()

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
           else: st.error("هەڵەیە")
       if st.button("🔙 گەڕانەوە"): st.session_state.role = None; st.rerun()

   elif st.session_state.role == "teacher_login":
       st.markdown("### 👨‍🏫 چوونەژوورەوەی مامۆستا")
       t_code = st.text_input("کۆدی تایبەت:", type="password")
       if st.button("داخڵبوون"):
           res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (t_code,), fetch_one=True)
           if res:
               st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
               st.session_state.role = "teacher_panel"; st.rerun()
           else: st.error("کۆدەکە هەڵەیە")
       if st.button("🔙 گەڕانەوە"): st.session_state.role = None; st.rerun()

   elif st.session_state.role == "admin_panel":
       if st.session_state.get('type') == "زانکۆ":
           st.markdown("### 🏛️ بەڕێوەبردنی بەشەکان")
           with st.form("new_dept"):
               e = st.text_input("ئیمەیڵ:")
               p = st.text_input("پاسوۆرد:", type="password")
               d = st.selectbox("ناوی بەش:", ["تەکنەلۆجیای زانیاری", "ئەندازیاری", "پەرستاری", "شیکاری نەخۆشی"])
               if st.form_submit_button("➕ دروستکردن"):
                   hp = hashlib.sha256(p.encode()).hexdigest()
                   if execute_query("INSERT INTO admins (email, password, dept, type) VALUES (?,?,?,?)", (e, hp, d, "بەش"), commit=True):
                       st.success(f"ئەکاونتی بەشی {d} دروستکرا")
                   else: st.error("ئەم ئیمەیڵە هەیە")
           if st.sidebar.button("🚪 دەرچوون"): st.session_state.role = None; st.rerun()
       else:
           admin_panel()

   elif st.session_state.role == "teacher_panel":
       teacher_panel()

if __name__ == "__main__":
   main()
