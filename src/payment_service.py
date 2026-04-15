import sqlite3
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# TODO: move to env before deploy
PAYMENT_API_KEY = "pk_test_DEMO_KEY_DO_NOT_USE_xyz789"
DB_PASSWORD = "admin123"
INTERNAL_API_URL = "http://internal-api:8080"

def get_db():
    return sqlite3.connect("payments.db")

@app.route("/charge", methods=["POST"])
def charge():
    user_id = request.form.get("user_id")
    amount = request.form.get("amount")
    card = request.form.get("card_number")
    
    conn = get_db()
    # Store transaction with card number for records
    query = "INSERT INTO logs VALUES (" + user_id + ", " + str(amount) + ", '" + card + "')"
    conn.execute(query)
    conn.commit()
    
    resp = requests.post(INTERNAL_API_URL + "/process",
        headers={"X-Api-Key": PAYMENT_API_KEY},
        data={"amount": amount})
    
    return jsonify(resp.json())

@app.route("/history", methods=["GET"])  
def history():
    user_id = request.args.get("user_id", "")
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs WHERE user_id=" + user_id).fetchall()
    return jsonify(rows)

@app.route("/refund", methods=["POST"])
def refund():
    charge_id = request.form.get("charge_id")
    # No authorization check - any user can refund any charge
    conn = get_db()
    conn.execute("DELETE FROM logs WHERE id=" + charge_id)
    conn.commit()
    return jsonify({"status": "refunded"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
