import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Path to the JSON file
stats_file_path = 'static/json/stats.json'
def compute_total_points(positions):
    points_mapping = {'1': 15, '2': 12, '3': 10, '4': 9, '5': 8, '6': 7, '7': 6, '8': 5, '9': 4, '10': 3, '11': 2, '12': 1}
    total_points = sum(points_mapping.get(pos, 0) * count for pos, count in positions.items())
    print(f"Calculating points for positions: {positions} => Total points: {total_points}")  # Debug print
    return total_points



# Load stats on server start
def load_stats():
    try:
        with open(stats_file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Returns an empty dictionary if the file doesn't exist or if it's empty

# Save stats
def save_stats(stats):
    with open(stats_file_path, 'w') as file:
        json.dump(stats, file, indent=4)

players = load_stats()
last_position_logged = None  # To keep track of the last logged position for undo functionality

@app.route('/', methods=['GET', 'POST'])
def home():
    global last_position_logged
    if request.method == 'POST' and 'player_name' in request.form:
        player_name = request.form['player_name']
        # Add new player if not already exists
        if player_name and player_name not in players:
            players[player_name] = {str(pos): 0 for pos in range(1, 13)}
            save_stats(players)  # Save updated stats
        return redirect(url_for('home'))

    # Compute total points for each player
    for player, stats in players.items():
        total_points = compute_total_points(stats)
        stats['total_points'] = total_points  # Add total_points to the stats for each player
    
    save_stats(players)  # Save the updated stats including total_points
    return render_template('home.html', players=players, last_position_logged=last_position_logged)

    # Compute total points for each player
    player_points = {player: compute_total_points(positions) for player, positions in players.items()}
    return render_template('home.html', players=players, player_points=player_points, last_position_logged=last_position_logged)

@app.route('/log_position', methods=['POST'])
def log_position():
    global last_position_logged
    player_name = request.form['player_name']
    position = str(request.form['position'])
    if player_name in players:
        players[player_name][position] += 1
        last_position_logged = {'player_name': player_name, 'position': position}
        save_stats(players)  # Save updated stats
    return redirect(url_for('home'))

@app.route('/remove_player', methods=['POST'])
def remove_player():
    player_name = request.form['player_name']
    if player_name in players:
        del players[player_name]
        save_stats(players)  # Save updated stats
    return redirect(url_for('home'))

@app.route('/undo_position', methods=['POST'])
def undo_position():
    global last_position_logged
    if last_position_logged:
        player_name = last_position_logged['player_name']
        position = last_position_logged['position']
        if player_name in players and players[player_name][position] > 0:
            players[player_name][position] -= 1
            save_stats(players)  # Save updated stats
        last_position_logged = None  # Reset the last logged position
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
