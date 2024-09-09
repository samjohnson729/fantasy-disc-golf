import streamlit as st
from time import sleep
from database import Database
from navigation import make_sidebar

make_sidebar()
database = Database()

st.title('Fantasy Disc Golf Login')

st.write('Please log in to continue.')

username = st.text_input(label='Username', label_visibility='hidden', placeholder='Username')
password = st.text_input(label='Password', label_visibility='hidden', placeholder='Password', type='password')

if st.button('Log in', type='primary', use_container_width=True):

    if database.exists(f'user:{username}') and password == database.get(f'user:{username}').decode():
        st.session_state.logged_in = True
        st.session_state.username = username
        st.success('Logged in successfully!')
        sleep(0.5)
        st.switch_page('pages/home.py')
    else:
        st.error('Incorrect username or password')

if st.button('Sign Up', type='secondary', use_container_width=True):
    st.switch_page('pages/sign-up.py')