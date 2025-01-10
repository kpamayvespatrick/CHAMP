from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import random

# Initialize Flask app and configure the database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'tournament.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Models
class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    players = db.relationship('Player', backref='tournament', lazy=True)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_number = db.Column(db.Integer, nullable=False)
    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player1_score = db.Column(db.Integer, nullable=True)
    player2_score = db.Column(db.Integer, nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)


@app.before_request
def create_tables():
    db.create_all()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/create', methods=['GET', 'POST'])
def create_tournament():
    if request.method == 'POST':
        tournament_name = request.form['tournament-name']
        players = [request.form[f'player{i}'] for i in range(1, 17)]

        tournament = Tournament.query.first()
        if tournament:
            tournament.name = tournament_name
            Player.query.filter_by(tournament_id=tournament.id).delete()
        else:
            tournament = Tournament(name=tournament_name)
            db.session.add(tournament)
            db.session.commit()

        for player_name in players:
            player = Player(name=player_name, tournament_id=tournament.id)
            db.session.add(player)

        db.session.commit()
        return redirect(url_for('generate_tournament'))

    return render_template('create.html')


@app.route('/tourgen', methods=['GET'])
def generate_tournament():
    tournament = Tournament.query.first()
    players = Player.query.filter_by(tournament_id=tournament.id).all()
    if not players:
        return redirect(url_for('create_tournament'))

    matches_exist = Match.query.count() > 0
    if not matches_exist:
        randomized_players = random.sample(players, len(players))
        create_matches(randomized_players, 1)

    return render_tournament_bracket(tournament)


def create_matches(players, round_number):
    if not players or len(players) < 2:
        return

    for i in range(0, len(players), 2):
        match = Match(
            round_number=round_number,
            player1_id=players[i].id,
            player2_id=players[i + 1].id
        )
        db.session.add(match)
    db.session.commit()


def render_tournament_bracket(tournament):
    rounds = []
    current_round = 1
    while True:
        matches = Match.query.filter_by(round_number=current_round).all()
        if not matches:
            break

        formatted_round = []
        for match in matches:
            player1 = Player.query.get(match.player1_id)
            player2 = Player.query.get(match.player2_id)
            formatted_round.append({
                'player1': player1,
                'player2': player2,
                'player1_score': match.player1_score,
                'player2_score': match.player2_score,
                'winner_id': match.winner_id
            })
        rounds.append(formatted_round)
        current_round += 1

    return render_template('tournament_bracket.html', tournament=tournament, rounds=rounds)


@app.route('/view')
def view_brackets():
    tournament = Tournament.query.first()
    if not tournament:
        return redirect(url_for('home'))
    return render_template('view.html', tournament=tournament)


@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    try:
        round_number = int(request.args.get('round', 1))
        matches = Match.query.filter_by(round_number=round_number).all()

        if request.method == 'POST':
            for match in matches:
                player1_score = request.form.get(f'player1_score_{match.id}')
                player2_score = request.form.get(f'player2_score_{match.id}')

                if player1_score is not None and player2_score is not None:
                    match.player1_score = int(player1_score)
                    match.player2_score = int(player2_score)
                    match.winner_id = match.player1_id if match.player1_score > match.player2_score else match.player2_id

            db.session.commit()

            if all(m.player1_score is not None and m.player2_score is not None for m in matches):
                winners = [Player.query.get(m.winner_id) for m in matches]
                create_matches(winners, round_number + 1)

            return redirect(url_for('admin_dashboard', round=round_number))

        max_round = Match.query.order_by(Match.round_number.desc()).first().round_number if Match.query.first() else 1

        detailed_matches = []
        for match in matches:
            player1 = Player.query.get(match.player1_id)
            player2 = Player.query.get(match.player2_id)

            if not player1 or not player2:
                continue

            detailed_matches.append({
                'id': match.id,
                'round_number': match.round_number,
                'player1': player1,
                'player2': player2,
                'player1_score': match.player1_score,
                'player2_score': match.player2_score,
            })

        return render_template(
            'admin_dashboard.html',
            matches=detailed_matches,
            current_round=round_number,
            max_round=max_round
        )
    except Exception as e:
        app.logger.error(f"Error in admin_dashboard: {e}")
        return "An error occurred while loading the admin dashboard. Please check the server logs for details.", 500

@app.route('/clear_database', methods=['POST'])
def clear_database():
    try:
        Match.query.delete()
        Player.query.delete()
        Tournament.query.delete()
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        app.logger.error(f"Error clearing database: {e}")
        return "An error occurred while clearing the database. Please check the server logs for details.", 500

@app.route('/bracket', methods=['GET', 'POST'])
def tournament_bracket():
    round_number = int(request.args.get('round', 1))
    matches = Match.query.filter_by(round_number=round_number).all()
    max_round = Match.query.order_by(Match.round_number.desc()).first().round_number if Match.query.first() else 1

    round_completed = all(m.player1_score is not None and m.player2_score is not None for m in matches) if matches else False

    return render_template(
        'tournament_bracket.html',
        matches=matches,
        tournament=Tournament.query.first(),
        current_round=round_number,
        max_round=max_round,
        round_completed=round_completed
    )


@app.route('/update_match', methods=['POST'])
def update_match():
    match_id = request.form.get('match_id')
    match = Match.query.get(match_id)

    if match:
        # Update scores
        player1_score = request.form.get('player1_score', None)
        player2_score = request.form.get('player2_score', None)

        if player1_score is not None and player2_score is not None:
            match.player1_score = int(player1_score)
            match.player2_score = int(player2_score)
            # Determine winner
            match.winner_id = match.player1_id if match.player1_score > match.player2_score else match.player2_id
            db.session.commit()

    return redirect(url_for('admin_dashboard', round=match.round_number))



@app.route('/update_scores', methods=['POST'])
def update_scores():
    updated_match_ids = []
    for key, value in request.form.items():
        if key.startswith('player1_score_') or key.startswith('player2_score_'):
            match_id = int(key.split('_')[-1])
            match = Match.query.get(match_id)

            if match:
                if key.startswith('player1_score_'):
                    match.player1_score = int(value)
                else:
                    match.player2_score = int(value)

                match.winner_id = match.player1_id if match.player1_score > match.player2_score else match.player2_id
                db.session.add(match)
                updated_match_ids.append(match_id)

    db.session.commit()
    return jsonify(updated_match_ids)


if __name__ == '__main__':
    app.run(debug=True)
