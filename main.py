# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

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

# --- 2. Ultra-Stable Mobile UI ---
def apply_stable_theme():
   st.markdown("""
       <style>
       @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
       
       /* ڕێکخستنی لاپەڕە */
       .stApp {
           background-color: #FFFFFF !important;
           font-family: 'Noto Sans Arabic', sans-serif !important;
           direction: rtl;
       }

       /* چاککردنی Sidebar بۆ ئەوەی نەچێتە سەر بەتنەکان */
       [data-testid="stSidebar"] {
           background-color: #F8FAFC !important;
           border-left: 3px solid #0D9488 !important;
           z-index: 1000000 !important;
       }

       /* چاککردنی بەتنەکان - قەبارەی جێگیر بۆ مۆبایل */
       div.stButton > button {
           width: 100% !important;
           height: 60px !important; /* قەبارەی جێگیر */
           background-color: #0D9488 !important;
           color: #FFFFFF !important;
           border-radius: 12px !important;
           font-size: 20px !important;
           font-weight: 800 !important;
           border: 2px solid #08665E !important;
           margin-top: 15px !important;
           display: block !important;
       }

       /* کارتەکان بۆ ئەوەی نووسینەکان تێکەڵ نەبن */
       .custom-card {
           background-color: #FFFFFF;
           padding: 20px;
           border-radius: 15px;
           border: 2px solid #E2E8F0;
           margin-bottom: 20px;
           text-align: center;
       }

       /* نووسینەکان بە ڕەشی زۆر تۆخ */
       h1, h2, h3, p, label, .stMarkdown {
           color: #000000 !important;
           text-align: right !important;
           font-weight: 700 !important;
       }

       /* چاککردنی Input بۆ مۆبایل */
       .stTextInput input {
           height: 50px !important;
           font-size: 18px !important;
           color: #000000 !important;
           border: 2px solid #0D9488 !important;
       }
       </style>
   """, unsafe_allow_html=True)

def main():
   st.set_page_config(page_title="GPU System", layout="centered")
   apply_stable_theme()
   
   if 'role' not in st.session_state: st.session_state.role = None

   # Header
   st.markdown("<div class='custom-card'><h1>زانکۆی پۆلیتەکنیکی گەرمیان</h1><p>سیستەمی ئامادەبوون</p></div>", unsafe_allow_html=True)

   if st.session_state.role is None:
       st.markdown("<h3 style='text-align: center;'>بچۆ ژوورەوە:</h3>", unsafe_allow_html=True)
       if st.button("🔑 چوونەژوورەوەی ئەدمین"): 
           st.session_state.role = "admin_login"; st.rerun()
       if st.button("🌙 چوونەژوورەوەی مامۆستا"): 
           st.session_state.role = "teacher_login"; st.rerun()

   elif st.session_state.role == "admin_login":
       st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
       st.write("### داخڵکردنی زانیاری")
       email = st.text_input("ئیمەیڵ:")
       pw = st.text_input("پاسوۆرد:", type="password")
       if st.button("داخڵبوون"):
           h = hashlib.sha256(pw.encode()).hexdigest()
           res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (email, h), fetch_one=True)
           if res:
               st.session_state.dept, st.session_state.type, st.session_state.role = res[0], res[1], "admin_panel"
               st.rerun()
           else: st.error("هەڵەیە!")
       if st.button("🔙 گەڕانەوە"): st.session_state.role = None; st.rerun()
       st.markdown("</div>", unsafe_allow_html=True)

   elif st.session_state.role == "admin_panel":
       st.sidebar.markdown(f"## بەشی {st.session_state.dept}")
       menu = st.sidebar.radio("مەنیو", ["سەرەتا", "خوێندکاران", "مامۆستایان"])
       st.markdown(f"<div class='custom-card'><h2>بەشی {menu}</h2></div>", unsafe_allow_html=True)
       if st.sidebar.button("🚪 دەرچوون"):
           st.session_state.role = None; st.rerun()

if __name__ == "__main__":
   main()
