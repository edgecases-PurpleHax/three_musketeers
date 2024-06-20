import json
import os
import time
from flask import Flask, render_template
import requests

app = Flask(__name__)

# Load API key and IDs from keys.json
with open('keys.json') as f:
    keys = json.load(f)

API_KEY = keys['API_KEY']
ID = keys['ID']
JESS_ID = keys['JESS_ID']
AMBER_ID = keys['AMBER_ID']

# Directory to store game files
GAME_FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'game_files')
os.makedirs(GAME_FILES_DIR, exist_ok=True)


def get_owned_games(steam_id):
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={API_KEY}&steamid={steam_id}&format=json"
    response = requests.get(url).json()
    return response.get('response', {}).get('games', [])


def get_game_name(appid):
    url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        app_list = response.json().get('applist', {}).get('apps', [])
        for app in app_list:
            if app['appid'] == appid:
                return app['name']
        return None
    except requests.RequestException as e:
        print(f"Error fetching data from Steam API: {e}")
        return None


def get_common_games():
    my_games = get_owned_games(ID)
    jess_games = get_owned_games(JESS_ID)
    amber_games = get_owned_games(AMBER_ID)

    my_games_ids = {game['appid'] for game in my_games}
    jess_games_ids = {game['appid'] for game in jess_games}
    amber_games_ids = {game['appid'] for game in amber_games}

    common_game_ids = my_games_ids & jess_games_ids & amber_games_ids

    return [get_game_name(appid) for appid in common_game_ids if get_game_name(appid)]


def get_games_list(steam_id, filename):
    file_path = os.path.join(GAME_FILES_DIR, filename)

    # Check if the file exists and is less than 24 hours old
    if os.path.exists(file_path):
        file_mod_time = os.path.getmtime(file_path)
        if time.time() - file_mod_time < 86400:  # 24 hours in seconds
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            games = get_owned_games(steam_id)
            game_names = [get_game_name(game['appid']) for game in games if get_game_name(game['appid'])]
            with open(file_path, 'w') as f:
                json.dump(game_names, f)
            return game_names
    else:
        games = get_owned_games(steam_id)
        game_names = [get_game_name(game['appid']) for game in games if get_game_name(game['appid'])]
        with open(file_path, 'w') as f:
            json.dump(game_names, f)
        return game_names


@app.route('/')
def common_games():
    data_file = os.path.join(GAME_FILES_DIR, 'common_games.json')

    # Check if the file exists and is less than 24 hours old
    if os.path.exists(data_file):
        file_mod_time = os.path.getmtime(data_file)
        if time.time() - file_mod_time < 86400:  # 24 hours in seconds
            with open(data_file, 'r') as f:
                final_games_list = json.load(f)
        else:
            final_games_list = get_common_games()
            with open(data_file, 'w') as f:
                json.dump(final_games_list, f)
    else:
        final_games_list = get_common_games()
        with open(data_file, 'w') as f:
            json.dump(final_games_list, f)

    return render_template('common_games.html', games=final_games_list)


@app.route('/ryan_games')
def ryan_games():
    ryan_games_list = get_games_list(ID, 'ryan_games.json')
    return render_template('user_games.html', games=ryan_games_list, user="Ryan")


@app.route('/jess_games')
def jess_games():
    jess_games_list = get_games_list(JESS_ID, 'jess_games.json')
    return render_template('user_games.html', games=jess_games_list, user="Jess")


@app.route('/amber_games')
def amber_games():
    amber_games_list = get_games_list(AMBER_ID, 'amber_games.json')
    return render_template('user_games.html', games=amber_games_list, user="Amber")


if __name__ == '__main__':
    app.run()
