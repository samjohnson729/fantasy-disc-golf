import json, time

import streamlit as st

from database import Database
from navigation import make_sidebar

make_sidebar()

database = Database()

st.title('Leage Management')

tabs = st.tabs(['Create', 'Manage', 'Delete', 'Join'])

with tabs[0]:

    st.subheader('Create League')
    league_name = st.text_input('League Name')
    password = st.text_input('League Password (for others to enter when they join your league)')
    roster_size = st.number_input('Roster Size', min_value=1, max_value=20, value=8)
    bench_size = st.number_input('Bench Size', min_value=0, max_value=roster_size, value=min(3, roster_size))

    st.subheader('Scoring Settings')
 
    hole_score_dict = {}
    tournament_position_dict = {}
    controls = st.columns(4)
    with controls[0]:
        hole_score_dict['ace'] = st.number_input('Ace', value=30)
        hole_score_dict['par'] = st.number_input('Par', value=1)
        st.write('')
        st.write('')
        tournament_position_dict[1] = st.number_input('1st Place', value=30)
        tournament_position_dict[5] = st.number_input('5th Place', value=10)
    with controls[1]:
        hole_score_dict['albatross'] = st.number_input('Albatross', value=20)
        hole_score_dict['bogey'] = st.number_input('Bogey', value=-1)
        st.write('')
        st.write('')
        tournament_position_dict[2] = st.number_input('2nd Place', value=20)
        tournament_position_dict[10] = st.number_input('6th - 10th Place', value=5)
    with controls[2]:
        hole_score_dict['eagle'] = st.number_input('Eagle', value=8)
        hole_score_dict['double bogey'] = st.number_input('Double Bogey', value=3)
        st.write('')
        st.write('')
        tournament_position_dict[3] = st.number_input('3rd Place', value=15)
        tournament_position_dict[25] = st.number_input('11th - 25th Place', value=3)
    with controls[3]:
        hole_score_dict['birdie'] = st.number_input('Birdie', value=3)
        hole_score_dict['triple+ bogey'] = st.number_input('Triple+ Bogey', value=-5)
        st.write('')
        st.write('')
        tournament_position_dict[4] = st.number_input('4th Place', value=12)
        tournament_position_dict[50] = st.number_input('26th - 50th Place', value=1)

    st.write('')
    st.write('')
    if st.button('Create League'):
        if league_name == '':
            st.warning('League Name cannot be left blank')
        elif database.exists(f'league:{league_name}'):
            st.warning('League already exists, choose a different name')
        else:

            # create league record
            league = {
                'league-name': league_name,
                'roster-size': roster_size,
                'bench-size': bench_size,
                'draft-status': 'before',
                'usernames': [st.session_state.username],
                'password': password,
                'scoring': {
                    'hole-score': hole_score_dict,
                    'tournament-position': tournament_position_dict
                }
            }
            database.save_league(league)

            # create team record
            team = {'username': st.session_state.username, 'players': [], 'bench': []}
            database.save_team(league_name, team)
            st.rerun()

with tabs[1]:

    st.header('Manage Existing League')
    league_name = st.selectbox('League', [l['league-name'] for l in database.list_leagues()], key='manage-league-selectbox')
    league = database.get_league(league_name)

    if league_name is not None:

        st.subheader('Teams')
        for team in database.list_teams(league_name):
            st.write(team['username'])

        st.subheader('Draft')
        draft_done = league['draft-status'] == 'after'
        if st.button('Go To Draft', disabled=draft_done):
            if len(league['usernames']) % 2 != 0:
                st.warning('You must have an even number of teams before drafting')
            else:
                league['draft-status'] = 'during'
                database.save_league(league)
                st.switch_page('pages/draft.py')

        st.subheader('Update League Password')
        form = st.form('Update Password')
        with form:
            password = st.text_input(
                label='League Password (for others to enter when they join your league)',
                value=league['password']
            )
            if st.form_submit_button('Update'):
                league['password'] = password
                database.save_league(league)
                st.rerun()

with tabs[2]:

    st.header('Delete League')
    league_name = st.selectbox('League', [l['league-name'] for l in database.list_leagues()], key='delete-league-selectbox')

    if league_name is not None:
        if st.button('Delete', type='primary'):
            database.delete_league(league_name)
            st.rerun()

with tabs[3]:
    
    st.header('Join a League')
    form = st.form('Join League')
    with form:
        league_name = st.text_input('League Name')
        password = st.text_input('League Password')
        if st.form_submit_button('Join'):
            if database.exists(f'league:{league_name}'):
                league = database.get_league(league_name)
                if password == league['password']:
                    if st.session_state.username in league['usernames']:
                        st.error('You have already joined this league')
                    elif league['draft-status'] != 'before':
                        st.error('You cannot join this league, the draft is already complete')
                    else:

                        # add username to league
                        league['usernames'].append(st.session_state.username)
                        database.save_league(league)

                        # creating team record
                        team = {'username': st.session_state.username, 'players': [], 'bench': []}
                        database.save_team(league_name, team)
                        st.success('Success!')
                        time.sleep(.5)
                        st.rerun()
                else:
                    st.error('Incorrect League Name or Password')
            else:
                st.error('Incorrect League Name or Password')
