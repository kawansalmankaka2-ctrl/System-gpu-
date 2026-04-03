# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import hashlib

# --- 1. Database Logic ---
def execute_query(query, params=(), fetch_all=False, fetch_one=False, commit=False):
   conn = sqlite3.connect('GPU_Attendance_Final.db')
   c = conn.cursor()
   result = None
   try:
       c.execute(query, params)
       if commit: 
           conn.commit()
           result = True
       elif fetch_one: result = c.fetchone()
       elif fetch_all: result = c.fetchall()
   finally: 
       conn.close()
   return result

# --- 2. Ultra-Modern Mobile UI (No Sidebar Overlap) ---
def apply_final_theme():
   st.markdown("""
       <style>
       @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
       
       .stApp {
           background-color: #F0F2F6 !important;
           font-family: 'Noto Sans Arabic', sans-serif !important;
           direction: rtl;
       }

       /* شاردنەوەی Sidebar بۆ ڕێگری لە تێکەڵبوون */
       [data-testid="stSidebar"] {
           display: none !important;
       }

       /* کارتی سەرەکی */
       .main-card {
           background-color: #FFFFFF;
           padding: 20px;
           border-radius: 20px;
           box-shadow: 0 10px 25px rgba(0,0,0,0.1);
           margin-bottom: 20px;
           text-align: center;
           border-top: 8px solid #0D9488;
       }

       /* بەتنی پێشکەوتوو - قەبارەی مۆبایل */
       div.stButton > button {
           width: 100% !important;
           height: 65px !important;
           background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%) !important;
           color: white !important;
           border-radius: 15px !important;
           font-size: 20px !important;
           font-weight: bold !important;
           border: none !important;
           margin-bottom: 15px !important;
           box-shadow: 0 4px 15px rgba(13, 148, 136, 0.3) !important;
       }

       h1, h2, h3, p {
           color: #1E293B !important;
           font-weight: 700 !important;
       }
       </style>
   """, unsafe_allow_html=True)

def main():
   st.set_page_config(page_title="GPU System", layout="centered")
   apply_final_theme()
   
   if 'role' not in st.session_state: st.session_state.role = None
   if 'page' not in st.session_state: st.session_state.page = "home"

   # Top Branding
   st.markdown("<div class='main-card'><h1>زانکۆی پۆلیتەکنیکی گەرمیان</h1><p>سیستەمی ئامادەبوونی خوێندکاران</p></div>", unsafe_allow_html=True)

   # Login Screen
   if st.session_state.role is None:
       st.markdown("<div class='main-card'><h3>چوونەژوورەوە</h3>", unsafe_allow_html=True)
       if st.button("🔑 چوونەژوورەوەی ئەدمین"):
           st.session_state.role = "admin_login"; st.rerun()
       if st.button("🌙 چوونەژوورەوەی مامۆستا"):
           st.session_state.role = "teacher_login"; st.rerun()
       st.markdown("</div>", unsafe_allow_html=True)

   # Admin Panels (No Sidebar)
   elif st.session_state.role == "admin_panel":
       st.markdown(f"<div class='main-card'><h2>بەشی {st.session_state.dept}</h2></div>", unsafe_allow_html=True)
       
       # Menu as Buttons
       col1, col2 = st.columns(2)
       if col1.button("👥 خوێندکاران"): st.session_state.page = "students"
       if col2.button("👨‍🏫 مامۆستایان"): st.session_state.page = "teachers"
       
       if st.session_state.page == "students":
           st.info("بەشی خوێندکاران لێرەدا دەکرێتەوە")
       
       if st.button("🚪 دەرچوون"):
           st.session_state.role = None; st.rerun()

   # Teacher Login View
   elif st.session_state.role == "teacher_login":
       st.markdown("<div class='main-card'>", unsafe_allow_html=True)
       t_code = st.text_input("کۆدی مامۆستا:", type="password")
       if st.button("داخڵبوون"):
           res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (t_code,), fetch_one=True)
           if res:
               st.session_state.role = "teacher_panel"; st.rerun()
       if st.button("🔙 گەڕانەوە"): st.session_state.role = None; st.rerun()
       st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
   main()
