from flask import Flask, render_template, request, redirect, session, url_for
import csv, json, os

app = Flask(__name__)
app.secret_key = 'supersecret'

# --------------------
# File paths
# --------------------
STUDENTS_FILE = 'data/students.csv'
CANDIDATES_FILE = 'data/candidates.json'
VOTES_FILE = 'data/votes.json'

# --------------------
# Admin credentials
# --------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "royal123"

# --------------------
# Load students
# --------------------
def load_students():
    students = {}
    with open(STUDENTS_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            students[row['student_id']] = {
                'password': row['password'],
                'department': row['department'],
                'year': row['year']
            }
    return students

# --------------------
# Load candidates
# --------------------
def load_candidates():
    with open(CANDIDATES_FILE) as f:
        return json.load(f)

# --------------------
# Load votes
# --------------------
def load_votes():
    if not os.path.exists(VOTES_FILE):
        return {}
    with open(VOTES_FILE) as f:
        return json.load(f)

# --------------------
# Save votes
# --------------------
def save_votes(votes):
    with open(VOTES_FILE, 'w') as f:
        json.dump(votes, f, indent=4)

# --------------------
# Check if student voted
# --------------------
def has_voted(student_id):
    votes = load_votes()
    return student_id in votes

# --------------------
# Student Login
# --------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    students = load_students()
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']

        if student_id in students:
            if students[student_id]['password'] == password:
                if has_voted(student_id):
                    error = "You have already voted."
                else:
                    session['student_id'] = student_id
                    return redirect(url_for('vote'))
            else:
                error = "Invalid password"
        else:
            error = "Invalid Student ID"
    return render_template('login.html', error=error)

# --------------------
# Voting Page (Multi-position)
# --------------------
@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    candidates = load_candidates()
    for c in candidates:
        c['image'] = url_for('static', filename=f"images/{c['image']}")

    position_order = ["President", "Vice President", "Secretary", "Vice Secretary", "Treasurer", "Vice Treasurer"]

    if request.method == 'POST':
        votes = load_votes()
        student_votes = {}

        for position in position_order:
            selected_candidate = request.form.get(position)
            if selected_candidate:
                student_votes[position] = selected_candidate

        votes[session['student_id']] = student_votes
        save_votes(votes)
        return redirect(url_for('success'))

    return render_template('vote.html', candidates=candidates, position_order=position_order)

# --------------------
# Success Page
# --------------------
@app.route('/success')
def success():
    return render_template('success.html')

# --------------------
# Admin Login
# --------------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            error = "Invalid admin credentials"
    return render_template('admin_login.html', error=error)

# --------------------
# Admin Dashboard
# --------------------
@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    candidates = load_candidates()
    for c in candidates:
        c['image'] = url_for('static', filename=f"images/{c['image']}")
        c['votes'] = 0

    votes = load_votes()
    for student_vote in votes.values():
        for pos, candidate_id in student_vote.items():
            for c in candidates:
                if str(c['id']) == str(candidate_id):
                    c['votes'] += 1

    return render_template('admin.html', candidates=candidates)

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# --------------------
# Run App
# --------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
