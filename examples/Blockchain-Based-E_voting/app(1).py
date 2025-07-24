import sqlite3

import cv2
from my_blockchain import Blockchain

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

app = Flask(__name__)
app.secret_key = "e-voting-secure-key"
voting_chain = Blockchain()

# Load face detection model
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# Database Connection
def get_db_connection():
    conn = sqlite3.connect("voters.db")
    conn.row_factory = sqlite3.Row
    return conn


# Home Route
@app.route("/")
def home():
    return render_template("index.html")


# Voter Authentication (Live Face Detection)
@app.route("/login", methods=["POST"])
def login():
    voter_name = request.form["name"]

    # Check voter in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM voters WHERE name=?", (voter_name,))
    voter = cursor.fetchone()
    conn.close()

    if voter:
        # Start Face Verification
        cap = cv2.VideoCapture(0)
        verified = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
            )

            if len(faces) > 0:
                verified = True
                break

            cv2.imshow("Face Verification - Press 'Q' to Exit", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

        if verified:
            session["voter_name"] = voter_name
            return redirect(url_for("vote"))
        else:
            return "❌ Face Verification Failed! Try Again."

    return "❌ Voter Not Found! Please Register First."


# Voting Page
@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "voter_name" not in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        vote_choice = request.form["vote"]
        voter_name = session["voter_name"]

        voting_chain.add_vote(voter_name, vote_choice)
        session.pop("voter_name", None)

        return redirect(url_for("results"))

    return render_template("vote.html")


# Results Page
@app.route("/results")
def results():
    vote_counts = {}
    for block in voting_chain.chain[1:]:
        vote = block["vote"]
        vote_counts[vote] = vote_counts.get(vote, 0) + 1

    return render_template("results.html", votes=vote_counts)


# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
