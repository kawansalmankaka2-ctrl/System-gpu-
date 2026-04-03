# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import hashlib
import random

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

# --- 2. High-Contrast Mobile UI ---
def apply_high_contrast_theme():
   st.markdown("""
       <style>
       @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&display=swap');
       
       /* پاشبنەمایەکی زۆر کاڵ بۆ ئەوەی نووسینەکان دیار بن */
       .stApp {
           background-color: #F8FAFC !important;
           font-family: 'Noto Sans Arabic', sans-serif !important;
           direction: rtl;
       }

       /* چاککردنی Sidebar */
       [data-testid="stSidebar"] {
           background-color: #FFFFFF !important;
           border-left: 2px solid #0D9488;
       }

       /* کارتەکان بە ڕەنگی سپی تەواو */
       .custom-card {
           background-color: #FFFFFF;
           padding: 25px;
           border-radius: 15px;
           box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
           margin-bottom: 20px;
           border-top: 6px solid #0D9488;
           text-align: center;
           border: 1px solid #E2E8F0;
       }

       /* تۆخکردنەوەی ڕەنگی هەموو نووسینەکان بۆ ئەوەی بە جوانی دیار بن */
       h1, h2, h3, .stMarkdown, p, label, .stSelectbox label {
           color: #0F172A !important; /* ڕەشی تۆخ */
           text-align: right;
           font-weight: 700 !important;
       }

       /* ڕەنگی ناو سندووقەکانی نووسین */
       .stTextInput input {
           color: #000000 !important;
           background-color: #FFFFFF !important;
           border: 1px solid #CBD5E1 !important;
       }

       /* بەتنەکان بە ڕەنگی تۆخ و ڕوون */
       div.stButton > button {
           width: 100% !important;
           min-height: 55px !important;
           background-color: #0D9488 !important;
           color: #FFFFFF !important;
           border-radius: 12px !important;
           font-size: 18px !important;
           font-weight: bold !important;
           border: none !important;
           box-shadow: 0 4px 6px rgba(13, 148, 136, 0.2) !important;
       }
       </style>
   """, unsafe_allow_html=True)

def main():
   st.set_page_config(page_title="GPU Attendance", layout="centered")
   apply_high_contrast_theme()
   
   if 'role' not in st.session_state: st.session_state.role = None

   # Header
   st.markdown("""
       <div class='custom-card'>
           <h1 style='font-size: 26px;'>زانکۆی پۆلیتەکنیکی گەرمیان</h1>
           <p style='color: #334155 !important;'>سیستەمی پێشکەوتووی ئامادەبوونی خوێندکاران</p>
       </div>
   """, unsafe_allow_html=True)

   if st.session_state.role is None:
       st.write("### تکایە جۆری چوونەژوورەوە هەڵبژێرە:")
       if st.button("🔑 چوونەژوورەوەی ئەدمین"): 
           st.session_state.role = "admin_login"; st.rerun()
       if st.button("🌙 چوونەژوورەوەی مامۆستا"): 
           st.session_state.role = "teacher_login"; st.rerun()

   elif st.session_state.role == "admin_login":
       st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
       st.write("## چوونەژوورەوەی ئەدمین")
       email = st.text_input("ئیمەیڵ:")
       pw = st.text_input("پاسوۆرد:", type="password")
       if st.button("چوونەژوورەوە"):
           h = hashlib.sha256(pw.encode()).hexdigest()
           res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (email, h), fetch_one=True)
           if res:
               st.session_state.dept, st.session_state.type, st.session_state.role = res[0], res[1], "admin_panel"
               st.rerun()
           else: st.error("زانیارییەکان هەڵەن")
       if st.button("🔙 گەڕانەوە"): st.session_state.role = None; st.rerun()
       st.markdown("</div>", unsafe_allow_html=True)

   elif st.session_state.role == "admin_panel":
       st.sidebar.write(f"## بەشی {st.session_state.dept}")
       menu = st.sidebar.radio("مەنیو", ["سەرەتا", "خوێندکاران", "مامۆستایان"])
       st.markdown(f"<div class='custom-card'><h2>بەخێربێیت بۆ بەشی {menu}</h2></div>", unsafe_allow_html=True)
       if st.sidebar.button("🚪 دەرچوون"):
           st.session_state.role = None; st.rerun()

if __name__ == "__main__":
   main()
