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

# --- 2. Mobile-First Professional UI ---
def apply_mobile_optimized_theme():
   st.markdown("""
       <style>
       @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;600&display=swap');
       
       /* ڕێکخستنی بنەڕەتی بۆ مۆبایل */
       .stApp {
           background-color: #f1f5f9 !important;
           font-family: 'Noto Sans Arabic', sans-serif !important;
           direction: rtl;
       }

       /* چاککردنی Sidebar کە لە وێنەکەدا کێشەی هەبوو */
       [data-testid="stSidebar"] {
           min-width: 250px !important;
           max-width: 300px !important;
           background-color: #ffffff !important;
           border-left: 2px solid #0d9488;
           z-index: 9999;
       }

       /* ستایلی بەتنەکان - گەورە و جیاواز بۆ مۆبایل */
       div.stButton > button {
           width: 100% !important;
           min-height: 55px !important;
           background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%) !important;
           color: white !important;
           border-radius: 12px !important;
           border: none !important;
           font-size: 18px !important;
           font-weight: 600 !important;
           margin: 10px 0px !important;
           box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
       }

       /* کارتەکان بۆ جیاکردنەوەی بەشەکان */
       .custom-card {
           background-color: #ffffff;
           padding: 25px;
           border-radius: 18px;
           box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
           margin-bottom: 20px;
           border-top: 6px solid #0d9488;
           text-align: center;
       }

       /* تایتڵەکان */
       h1 { color: #0f172a !important; font-size: 24px !important; font-weight: 700 !important; }
       h2 { color: #334155 !important; font-size: 20px !important; }
       
       /* لابردنی تێکەڵبوونی نووسین لە شاشەی بچووک */
       @media (max-width: 768px) {
           .main-header { font-size: 18px !important; }
           .stMarkdown p { font-size: 16px !important; line-height: 1.6; }
       }
       </style>
   """, unsafe_allow_html=True)

def main():
   st.set_page_config(page_title="GPU System", layout="centered")
   apply_mobile_optimized_theme()
   
   if 'role' not in st.session_state: st.session_state.role = None

   # Header Section
   st.markdown("""
       <div class='custom-card'>
           <h1>زانکۆی پۆلیتەکنیکی گەرمیان</h1>
           <p style='color: #64748b;'>سیستەمی پێشکەوتووی ئامادەبوونی خوێندکاران</p>
       </div>
   """, unsafe_allow_html=True)

   if st.session_state.role is None:
       st.markdown("<div style='text-align: center; margin-bottom: 15px;'><h3>بۆ چوونەژوورەوە یەکێک هەڵبژێرە:</h3></div>", unsafe_allow_html=True)
       
       # بەتنەکان بە ستوونی بۆ مۆبایل باشترن
       if st.button("🔑 چوونەژوورەوەی ئەدمین"): 
           st.session_state.role = "admin_login"; st.rerun()
           
       if st.button("🌙 چوونەژوورەوەی مامۆستا"): 
           st.session_state.role = "teacher_login"; st.rerun()

   elif st.session_state.role == "admin_login":
       st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
       st.write("### چوونەژوورەوەی ئەدمین")
       email = st.text_input("ئیمەیڵ:")
       pw = st.text_input("پاسوۆرد:", type="password")
       if st.button("داخڵبوون"):
           h = hashlib.sha256(pw.encode()).hexdigest()
           res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (email, h), fetch_one=True)
           if res:
               st.session_state.dept, st.session_state.type, st.session_state.role = res[0], res[1], "admin_panel"
               st.rerun()
           else: st.error("زانیارییەکان هەڵەن!")
       if st.button("🔙 گەڕانەوە"): st.session_state.role = None; st.rerun()
       st.markdown("</div>", unsafe_allow_html=True)

   elif st.session_state.role == "admin_panel":
       st.sidebar.markdown(f"<h2 style='text-align: center;'>بەشی {st.session_state.dept}</h2>", unsafe_allow_html=True)
       menu = st.sidebar.radio("مەنیو", ["سەرەتا", "خوێندکاران", "مامۆستایان", "ڕاپۆرت"])
       
       st.markdown(f"<div class='custom-card'><h2>بەخێربێیت بۆ پانێڵی {menu}</h2></div>", unsafe_allow_html=True)
       
       if st.sidebar.button("🚪 دەرچوون"):
           st.session_state.role = None; st.rerun()

if __name__ == "__main__":
   main()
