from app import app
#from app import db
from flask import render_template, request, jsonify
import json
import requests
import pandas as pd
from datetime import datetime

def xor(v1, v2):
    if v1 and v2:
        return False
    if v1 and not(v2):
        return True
    if not(v1) and v2:
        return True
    if not(v1) and not(v2):
        return False

def found(val):
    if val == -1:
        return False
    else:
        return True

def fetch_news():
    API_KEY = 'e750e0189ede4b6b8b1a766b8523b29a'

    resp = requests.get('https://newsapi.org/v1/articles?source=techcrunch&apiKey=' + API_KEY)
    resp2 = requests.get('https://newsapi.org/v1/articles?source=reuters&apiKey=' + API_KEY)
    resp3 = requests.get('https://newsapi.org/v1/articles?source=newsweek&apiKey=' + API_KEY)
    resp4 = requests.get('https://newsapi.org/v1/articles?source=new-york-times&apiKey=' + API_KEY)
    resp5 = requests.get('https://newsapi.org/v1/articles?source=the-wall-street-journal&apiKey=' + API_KEY)
    resp6 = requests.get('https://newsapi.org/v1/articles?source=the-washington-post&apiKey=' + API_KEY)

    list_of_words =['cop', 'cops', 'crime', 'law enforcement', 'homocide', 'crime rate', 'white collar crime', 'blue collar crime']

    empty_set = set()
    mention_count = {}.fromkeys(list_of_words, 0)
    link_mentions = {}.fromkeys(list_of_words, empty_set)

    entries = resp.json()
    entries.update(resp2.json())
    entries.update(resp3.json())
    entries.update(resp4.json())
    entries.update(resp5.json())
    entries.update(resp6.json())

    for article in entries['articles']:
        for word in list_of_words:
            title_found = found(article['title'].find(word))
            description_found = found(article['description'].find(word))
            if xor(title_found, description_found):
                mention_count[word] += 1
                link_mentions[word].add(article['url'])

    link_mentions = {key:list(link_mentions[key]) for key in link_mentions}
    mention_count["timestamp"] = str(datetime.now())
    link_mentions["timestamp"] = str(datetime.now())
    return mention_count, link_mentions

    
@app.route("/api", methods=["GET", "POST"])
def api():
    mention_count, link_mentions = fetch_news()
    return jsonify(mention_count)
    

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")
