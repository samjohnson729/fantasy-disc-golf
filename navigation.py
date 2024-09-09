import streamlit as st
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages


def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    pages = get_pages('')
    return pages[ctx.page_script_hash]['page_name']


def make_sidebar():
    with st.sidebar:

        st.title('Fantasy Disc Golf')
        st.page_link('pages/home.py', label='Home')
        st.page_link('pages/league-management.py', label='League Management')
        #st.page_link('pages/league.py', label='League')
        #st.page_link('pages/draft.py', label='Draft')
        #st.page_link('pages/matchup.py', label='Matchup')

        if st.session_state.get('logged_in', False):
            if st.button('Log out'):
                logout()

        elif get_current_page_name() not in ['login', 'sign-up']:
            st.switch_page('login.py')


def logout():
    st.session_state.logged_in = False
    st.info('Logged out successfully!')
    sleep(0.5)
    st.switch_page('login.py')