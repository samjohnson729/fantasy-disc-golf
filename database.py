import json, random
from io import StringIO

import requests
import streamlit as st
import pandas as pd
import numpy as np
from redis import Redis

class Database(Redis):

    EVENTS = {
        'Chess.com Invitational': 77775,
        'WACO Annual Charity Open': 77758,
        'The Open at Austin': 77759,
        'Texas State Disc Golf Championships': 77760,
        'Jonesboro Open': 77761,
        'Music City Open': 77762,
        'PDGA Champions Cup': 77099,
        'Dynamic Discs Open': 77763,
        'Copenhagen Open': 78193,
        'OTB Open': 77764,
        'Portland Open': 77765,
        'Beaver State Fling': 77766,
        'Turku Open': 78194,
        'The Preserve Championship': 78271,
        'Swedish Open': 78195,
        'Trubank Des Moines Challenge': 77768,
        'Krokhol Open': 78196,
        'European Open': 77750,
        'European Disc Golf Festival': 78197,
        'Ledgestone Open': 77769,
        'LWS Open at Idlewild': 77771,
        'PDGA Professional Disc Golf World Championships': 71315,
        'Great Lakes Open': 77772,
        'Green Mountain Championship': 82419,
        'MVP Open x OTB': 77773,
        'DGPT Championship': 77774
    }

    def __init__(self):
        super().__init__(**st.secrets['redis'])

    @st.cache_data
    def get_players(_self, num_players:int=100):
        players = pd.DataFrame()
        page = 0
        while len(players) < num_players:
            response = requests.get(f'https://www.pdga.com/players/stats?page={page}&order=player_Rating&sort=desc')
            df = pd.read_html(StringIO(response.text))[0]
            players = pd.concat([players, df], ignore_index=True)
            page += 1

        players = players[['Name', 'PDGA #', 'Rating', 'Events', 'Points', 'Cash']].copy()
        return players.iloc[:num_players].copy()

    def get_drafted_players(self, league_name:str, team_key:str='*'):
        drafted_players_ids = []
        for key in self.scan_iter(f'team:{league_name}:{team_key}'):
            team = json.loads(self.get(key))
            drafted_players_ids += team['Players']

        all_players = self.get_players()
        drafted_players = all_players[all_players['PDGA #'].apply(lambda x: str(x) in drafted_players_ids)].copy()
        return drafted_players

    def get_undrafted_players(self, league_name:str, num_players:int=100):
        all_players = self.get_players()
        drafted_players = self.get_drafted_players(league_name)
        undrafted_players = all_players[all_players['PDGA #'].apply(lambda x: str(x) not in drafted_players['PDGA #'].astype(str).values)].copy()
        return undrafted_players

    def get_leagues(self):
        return [json.loads(self.get(key)) for key in self.scan_iter(f'league:*')]
    
    def get_teams(self, league_name:str):
        return [json.loads(self.get(key)) for key in self.scan_iter(f'team:{league_name}:*')]

    def get_draft_order(self, league_name:str):
        league = json.loads(self.get(f'league:{league_name}'))
        teams = self.get_teams(league_name)
        random.seed(729)
        random.shuffle(teams)

        reverse = False
        draft_order = []
        for _ in range(league['Roster Size']):
            if reverse: draft_order += list(reversed(teams))
            else: draft_order += teams
            reverse = not reverse

        return draft_order
    
    def get_event_results(self, event_name:int, league_name:str):
        event_id = self.EVENTS.get(event_name)
        event_dict = requests.get(f'https://www.pdga.com/apps/tournament/live-api/live_results_fetch_event?TournID={event_id}').json()['data']

        results = {}
        for round in event_dict['RoundsList'].keys():
            pools = requests.get(f'https://www.pdga.com/apps/tournament/live-api/live_results_fetch_round?TournID={event_id}&Division=MPO&Round={round}').json()['data']
            pools = [pools] if isinstance(pools, dict) else pools
            for data in pools:
                pars = np.array([hole['Par'] for hole in data['holes']])
                for record in data['scores']:
                    try:
                        scores = np.array([int(score) for score in record['HoleScores'] if score != ''])
                        results[record['PDGANum']] = {
                            'Name':             record['Name'],
                            'Ace':              results.get(record['PDGANum'], {}).get('Ace', 0) + sum(scores == 1),
                            'Albatross':        results.get(record['PDGANum'], {}).get('Albatross', 0) + sum(scores - pars[:len(scores)] == -3),
                            'Eagle':            results.get(record['PDGANum'], {}).get('Eagle', 0) + sum(scores - pars[:len(scores)] == -2),
                            'Birdie':           results.get(record['PDGANum'], {}).get('Birdie', 0) + sum(scores - pars[:len(scores)] == -1),
                            'Par':              results.get(record['PDGANum'], {}).get('Par', 0) + sum(scores - pars[:len(scores)] == 0),
                            'Bogey':            results.get(record['PDGANum'], {}).get('Bogey', 0) + sum(scores - pars[:len(scores)] == 1),
                            'Double Bogey':     results.get(record['PDGANum'], {}).get('Double Bogey', 0) + sum(scores - pars[:len(scores)] == 2),
                            'Triple+ Bogey':    results.get(record['PDGANum'], {}).get('Triple+ Bogey', 0) + sum(scores - pars[:len(scores)] >= 3),
                            'Score':            record['ToPar'],
                            'Position':         int(record['RunningPlace'])
                        }
                    except:
                        pass

        results = pd.DataFrame.from_dict(results, orient='index')
        results['Points'] = results.apply(lambda x: self.calculate_score(league_name, x), axis=1)

        return results

    def calculate_score(self, league_name:str, row):
        league = json.loads(self.get(f'league:{league_name}'))
        hole_score_dict = league['Scoring']['hole-score']
        tournament_position_dict = league['Scoring']['tournament-position']

        output = sum([
            hole_score_dict['ace'] * row['Ace'],
            hole_score_dict['-3'] * row['Albatross'],
            hole_score_dict['-2'] * row['Eagle'],
            hole_score_dict['-1'] * row['Birdie'],
            hole_score_dict['0'] * row['Par'],
            hole_score_dict['1'] * row['Bogey'],
            hole_score_dict['2'] * row['Double Bogey'],
            hole_score_dict['3'] * row['Triple+ Bogey']
        ])

        for key, value in tournament_position_dict.items():
            if row['Position'] <= int(key):
                output += value
                break

        return output
