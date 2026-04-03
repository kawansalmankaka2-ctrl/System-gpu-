# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
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

# --- 2. Advanced & Eye-Friendly UI ---
def apply_advanced_theme():
   st.markdown("""
       <style>
       @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;600&display=swap');
       
       .stApp {
           background-color: #f8fafc !important;
           font-family: 'Noto Sans Arabic', sans-serif !important;
           direction: rtl;
       }

       section[data-testid="stSidebar"] {
           background-color: #ffffff !important;
           border-left: 1px solid #e2e8f0;
       }

       .custom-card {
           background-color: #ffffff;
           padding: 20px;
           border-radius: 15px;
           box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
           margin-bottom: 20px;
           border-top: 5px solid #0d9488;
           color: #1e293b;
       }

       div.stButton > button {
           width: 100% !important;
           background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%) !important;
           color: white !important;
           border-radius: 12px !important;
           border: none !important;
           padding: 12px 20px !important;
           font-size: 16px !important;
           font-weight: 600 !important;
           transition: all 0.3s ease !important;
       }
       
       div.stButton > button:hover {
           transform: translateY(-2px);
           box-shadow: 0 10px 15px -3px rgba(13, 148, 136, 0.3) !important;
       }

       h1, h2, h3 { color: #0f172a !important; text-align: center; }
       p, label { color: #475569 !important; text-align: right; }
       </style>
   """, unsafe_allow_html=True)

def main():
   st.set_page_config(page_title="Zankoy Garmian", layout="centered")
   apply_advanced_theme()
   
   if 'role' not in st.session_state: st.session_state.role = None

   st.markdown("""
       <div style='text-align: center; padding: 20px;'>
           <h1 style='margin-bottom: 0;'>زانکۆی پۆلیتەکنیکی گەرمیان</h1>
           <p style='margin-top: 5px; font-size: 1.1em;'>سیستەمی پێشکەوتووی ئامادەبوونی خوێندکاران</p>
       </div>
   """, unsafe_allow_html=True)

   if st.session_state.role is None:
       st.markdown("<div class='custom-card'><h3>بەخێربێیت، تکایە جۆری چوونەژوورەوە هەڵبژێرە</h3></div>", unsafe_allow_html=True)
       col1, col2 = st.columns(2)
       if col1.button("🔑 چوونەژوورەوەی ئەدمین"): 
           st.session_state.role = "admin_login"; st.rerun()
       # گۆڕینی ئیمۆجی لێرە ئەنجامدراوە
       if col2.button("🌙 چوونەژوورەوەی مامۆستا"): 
           st.session_state.role = "teacher_login"; st.rerun()

   elif st.session_state.role == "admin_login":
       st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
       email = st.text_input("ئیمەیڵ:")
       pw = st.text_input("پاسوۆرد:", type="password")
       if st.button("چوونەژوورەوە"):
           h = hashlib.sha256(pw.encode()).hexdigest()
           res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (email, h), fetch_one=True)
           if res:
               st.session_state.dept, st.session_state.type, st.session_state.role = res[0], res[1], "admin_panel"
               st.rerun()
           else: st.error("زانیارییەکان هەڵەن")
       if st.button("گەڕانەوە"): st.session_state.role = None; st.rerun()
       st.markdown("</div>", unsafe_allow_html=True)

   elif st.session_state.role == "admin_panel":
       st.sidebar.markdown(f"## بەشی {st.session_state.dept}")
       menu = st.sidebar.radio("مەنیو", ["سەرەتا", "خوێندکاران", "مامۆستایان", "ڕاپۆرت"])
       
       if menu == "سەرەتا":
           st.markdown(f"<div class='custom-card'><h2>بەخێربێیت بۆ پانێڵی {st.session_state.dept}</h2></div>", unsafe_allow_html=True)
       
       if st.sidebar.button("🚪 دەرچوون"):
           st.session_state.role = None; st.rerun()

if __name__ == "__main__":
   main()
