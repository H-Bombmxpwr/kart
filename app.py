# import json
# from flask import Flask, render_template, request, redirect, url_for

# app = Flask(__name__)

# # Path to the JSON file
# stats_file_path = 'static/json/stats.json'

# # Function to compute total points based on positions
# def compute_total_points(positions):
#     points_mapping = {'1': 15, '2': 12, '3': 10, '4': 9, '5': 8, '6': 7, '7': 6, '8': 5, '9': 4, '10': 3, '11': 2, '12': 1}
#     total_points = sum(points_mapping.get(pos, 0) * count for pos, count in positions.items() if pos.isdigit())
#     return total_points

# # Function to recalculate total points for all players
# def recalculate_all_points():
#     for player, stats in players.items():
#         stats['total_points'] = compute_total_points(stats)
#     save_stats(players)

# # Function to load stats from the JSON file
# def load_stats():
#     try:
#         with open(stats_file_path, 'r') as file:
#             return json.load(file)      
#     except (FileNotFoundError, json.JSONDecodeError):
#         return {}  # Returns an empty dictionary if the file doesn't exist or if it's empty

# # Function to save stats to the JSON file
# def save_stats(stats):
#     with open(stats_file_path, 'w') as file:
#         json.dump(stats, file, indent=4)

# # Load existing stats from JSON file
# players = load_stats()

# # Variable to keep track of the last logged position for undo functionality
# last_position_logged = None

# @app.route('/', methods=['GET', 'POST'])
# def home():
#     global last_position_logged
#     if request.method == 'POST' and 'player_name' in request.form:
#         player_name = request.form['player_name']
#         # Add new player if not already exists
#         if player_name and player_name not in players:
#             players[player_name] = {str(pos): 0 for pos in range(1, 13)}
#             players[player_name]['total_points'] = 0  # Initialize total points
#             save_stats(players)  # Save updated stats
#         return redirect(url_for('home'))

#     recalculate_all_points()  # Recalculate points for all players
#     return render_template('home.html', players=players, last_position_logged=last_position_logged)

# @app.route('/log_position', methods=['POST'])
# def log_position():
#     global last_position_logged
#     player_name = request.form['player_name']
#     position = str(request.form['position'])
#     if player_name in players:
#         players[player_name][position] += 1
#         last_position_logged = {'player_name': player_name, 'position': position}
#         recalculate_all_points()  # Recalculate points for all players
#     return redirect(url_for('home'))

# @app.route('/remove_player', methods=['POST'])
# def remove_player():
#     player_name = request.form['player_name']
#     if player_name in players:
#         del players[player_name]
#         recalculate_all_points()  # Recalculate points for all players
#     return redirect(url_for('home'))

# @app.route('/undo_position', methods=['POST'])
# def undo_position():
#     global last_position_logged
#     if last_position_logged:
#         player_name = last_position_logged['player_name']
#         position = last_position_logged['position']
#         if player_name in players and players[player_name][position] > 0:
#             players[player_name][position] -= 1
#             last_position_logged = None  # Reset the last logged position
#         recalculate_all_points()  # Recalculate points for all players
#     return redirect(url_for('home'))

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)



import hashlib
from flask import Flask, render_template, request, redirect, url_for, session
import json
from functools import wraps


app = Flask(__name__)
app.secret_key = 'not-used-secret-key'

def hash_username(username):
    """ Hash the username to create a unique identifier. """
    return hashlib.sha256(username.encode('utf-8')).hexdigest()



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username_hashed' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# Function to compute total points based on positions
def compute_total_points(positions):
    points_mapping = {'1': 15, '2': 12, '3': 10, '4': 9, '5': 8, '6': 7, '7': 6, '8': 5, '9': 4, '10': 3, '11': 2, '12': 1}
    total_points = sum(points_mapping.get(pos, 0) * count for pos, count in positions.items() if pos.isdigit())
    return total_points

def get_user_stats_file(username_hashed):
    """ Get the user-specific stats file path based on the hashed username. """
    return f'static/json/{username_hashed}_stats.json'

def load_user_stats(username_hashed):
    """ Load the user-specific stats from their JSON file. """
    try:
        with open(get_user_stats_file(username_hashed), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # Return a default stats structure if the file doesn't exist
        return {str(i): 0 for i in range(1, 13)}

def save_user_stats(username_hashed, stats):
    """ Save the user-specific stats to their JSON file. """
    with open(get_user_stats_file(username_hashed), 'w') as file:
        json.dump(stats, file, indent=4)

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    # Check if the session has a stored username hash; if not, redirect to login
    if 'username_hashed' not in session:
        return redirect(url_for('login'))

    username_hashed = session['username_hashed']
    user_stats = load_user_stats(username_hashed)

    if request.method == 'POST' and 'player_name' in request.form:
        player_name = request.form['player_name']
        # Add new player if not already exists
        if player_name not in user_stats:
            user_stats[player_name] = {str(pos): 0 for pos in range(1, 13)}
        save_user_stats(username_hashed, user_stats)  # Save updated stats
        return redirect(url_for('home'))

    # No need to recalculate all points if we're not logging positions here
    return render_template('home.html', players=user_stats, last_position_logged=session.get('last_position_logged'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        username_hashed = hash_username(username)
        session['username_hashed'] = username_hashed  # Store the hashed username in the session
        return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/log_position', methods=['POST'])
@login_required
def log_position():
    if 'username_hashed' not in session:
        return redirect(url_for('login'))
    
    username_hashed = session['username_hashed']
    user_stats = load_user_stats(username_hashed)

    player_name = request.form['player_name']
    position = request.form['position']
    if player_name in user_stats:
        if position in user_stats[player_name]:
            user_stats[player_name][position] += 1
        else:
            user_stats[player_name][position] = 1
        user_stats[player_name]['total_points'] = compute_total_points(user_stats[player_name])
        session['last_position_logged'] = {'player_name': player_name, 'position': position}
        save_user_stats(username_hashed, user_stats)
    
    return redirect(url_for('home'))

@app.route('/remove_player', methods=['POST'])
@login_required
def remove_player():
    if 'username_hashed' not in session:
        return redirect(url_for('login'))
    
    username_hashed = session['username_hashed']
    user_stats = load_user_stats(username_hashed)

    player_name = request.form['player_name']
    if player_name in user_stats:
        del user_stats[player_name]
        save_user_stats(username_hashed, user_stats)
    
    return redirect(url_for('home'))

@app.route('/undo_position', methods=['POST'])
@login_required
def undo_position():
    if 'username_hashed' not in session:
        return redirect(url_for('login'))
    
    username_hashed = session['username_hashed']
    user_stats = load_user_stats(username_hashed)

    if 'last_position_logged' in session:
        last_position_logged = session['last_position_logged']
        player_name = last_position_logged['player_name']
        position = last_position_logged['position']
        
        if player_name in user_stats and position in user_stats[player_name] and user_stats[player_name][position] > 0:
            user_stats[player_name][position] -= 1
            user_stats[player_name]['total_points'] = compute_total_points(user_stats[player_name])
            save_user_stats(username_hashed, user_stats)
            session.pop('last_position_logged', None)  # Clear the last position logged
    
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('username_hashed', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)