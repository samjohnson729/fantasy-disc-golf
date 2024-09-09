import streamlit as st
from time import sleep
from database import Database
from navigation import make_sidebar

make_sidebar()
database = Database()

st.title('Account Creation')

st.write('Please sign up to continue.')

username = st.text_input(label='Username', label_visibility='hidden', placeholder='Username')
password = st.text_input(label='Password', label_visibility='hidden', placeholder='Password', type='password')

if st.button('Sign Up', type='primary', use_container_width=True):
    if not database.exists(f'user:{username}'):
        database.set(f'user:{username}', password)
        st.session_state.logged_in = True
        st.session_state.username = username
        st.success('Logged in successfully!')
        sleep(0.5)
        st.switch_page('pages/home.py')