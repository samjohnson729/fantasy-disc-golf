import json

import streamlit as st

import utils
from database import Database

database = Database()

st.title('Leage Management')

tabs = st.tabs(['Create', 'Manage'])

with tabs[0]:

    st.header('Settings')
    controls = st.columns([.2, .8])
    with controls[0]:
        league_name = st.text_input('League Name')
        roster_size = st.number_input('Roster Size', value=8)
        bench_size = st.number_input('Bench Size', value=3)

    st.header('Teams')

    form = st.form('new-team-form', clear_on_submit=True, border=False)
    with form:
        controls = st.columns([.4,.4,.2], vertical_alignment='bottom')
        with controls[0]:
            owner = st.text_input('Owner')
        with controls[1]:
            team_name = st.text_input('Team Name')
        with controls[2]:
            if st.form_submit_button('Add'):
                if team_name == '':
                    st.warning('Team Name cannot be left blank')
                elif owner == '':
                    st.warning('Owner cannot be left blank')
                elif owner in [team['Owner'] for team in st.session_state.get('teams', [])]:
                    st.warning(f'Owner {owner} is not allowed to own multiple teams')
                else:
                    if 'teams' in st.session_state:
                        st.session_state['teams'].append({'Owner': owner, 'Team Name': team_name})
                    else:
                        st.session_state['teams'] = [{'Owner': owner, 'Team Name': team_name}]
                    st.rerun()

    for team in st.session_state.get('teams', []):
        controls = st.columns([.4, .4, .2], vertical_alignment='center')
        with controls[0]:
            st.text(team['Owner'])
        with controls[1]:
            st.text(team['Team Name'])
        with controls[2]:
            if st.button('Delete', key=team['Owner']):
                st.session_state['teams'].remove(team)
                st.rerun()

    st.header('Scoring')
 
    hole_score_dict = {}
    controls = st.columns(8)
    with controls[0]:
        hole_score_dict['ace'] = st.number_input('Ace', value=30)
    with controls[1]:
        hole_score_dict[-3] = st.number_input('Albatross', value=20)
    with controls[2]:
        hole_score_dict[-2] = st.number_input('Eagle', value=8)
    with controls[3]:
        hole_score_dict[-1] = st.number_input('Birdie', value=3)
    with controls[4]:
        hole_score_dict[0] = st.number_input('Par', value=1)
    with controls[5]:
        hole_score_dict[1] = st.number_input('Bogey', value=-1)
    with controls[6]:
        hole_score_dict[2] = st.number_input('Double Bogey', value=3)
    with controls[7]:
        hole_score_dict[3] = st.number_input('Triple+ Bogey', value=-5)

    tournament_position_dict = {}
    controls = st.columns(8)
    with controls[0]:
        tournament_position_dict[1] = st.number_input('1st Place', value=30)
    with controls[1]:
        tournament_position_dict[2] = st.number_input('2nd Place', value=20)
    with controls[2]:
        tournament_position_dict[3] = st.number_input('3rd Place', value=15)
    with controls[3]:
        tournament_position_dict[4] = st.number_input('4th Place', value=12)
    with controls[4]:
        tournament_position_dict[5] = st.number_input('5th Place', value=10)
    with controls[5]:
        tournament_position_dict[10] = st.number_input('6th - 10th Place', value=5)
    with controls[6]:
        tournament_position_dict[25] = st.number_input('11th - 25th Place', value=3)
    with controls[7]:
        tournament_position_dict[50] = st.number_input('26th - 50th Place', value=1)

    st.header("All finished?")
    if st.button('Create League'):
        if league_name == '':
            st.warning('Must choose league name before adding teams')
        elif len(st.session_state.get('teams', [])) == 0:
            st.warning('Must add teams before creating league')
        elif database.exists(f'league:{league_name}'):
            st.warning('League already exists, choose a different name')
        else:

            league = {
                'League Name': league_name,
                'Roster Size': roster_size,
                'Bench Size': bench_size,
                'Scoring': {
                    'hole-score': hole_score_dict,
                    'tournament-position': tournament_position_dict
                }
            }
            database.set(f'league:{league_name}', json.dumps(league))

            for team_dict in st.session_state.get('teams', []):

                team = {
                    'Team Name': team_dict['Team Name'],
                    'Owner': team_dict['Owner'],
                    'Players': []
                }
                database.set(f"team:{league_name}:{team['Owner']}", json.dumps(team))

            st.session_state['teams'] = []
            st.rerun()

with tabs[1]:

    league_name = st.selectbox('League', [l['League Name'] for l in database.get_leagues()])

    if st.button('Delete'):
        database.delete(f'league:{league_name}')
        for key in database.scan_iter(f'team:{league_name}:*'):
            database.delete(key)
        st.rerun()
