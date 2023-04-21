AnimeSite/
  ├── app.py
  ├── static/
  │   ├── css/
  │   │   └── styles.css
  │   ├── js/
  │   │   └── script.js
  │   └── data/
  │       └── anime.json
  ├── templates/
  │   └── index.html
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anime Site</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    <script src="{{ url_for('static', filename='js/script.js') }}" defer></script>
</head>
<body>
    <div class="container">
        <h1>Anime Gallery</h1>
        <div id="anime-gallery">
            <!--
body {
    font-family: Arial, sans-serif;
    background-color: #222;
    color: #eee;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
}

h1 {
    font-size: 2rem;
    margin-bottom: 1rem;
}

#anime-gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    grid-gap: 1rem;
}

img {
    max-width: 100%;
    height: auto;
}
document.addEventListener("DOMContentLoaded", () => {
  fetch("/static/data/anime.json")
    .then((response) => response.json())
    .then((data) => {
      const gallery = document.getElementById("anime-gallery");
      data.anime_images.forEach((image_url) => {
        const img = document.createElement("img");
        img.src = image_url;
        gallery.appendChild(img);
      });
    });
});
document.addEventListener("DOMContentLoaded", () => {
  fetch("/static/data/zalthorius.json")
    .then((response) => response.json())
    .then((data) => {
      const gallery = document.getElementById("anime-gallery");
      data.anime_images.forEach((image_url) => {
        const img = document.createElement("img");
        img.src = image_url;
        gallery.appendChild(img);
      });
    });
});
document.addEventListener("DOMContentLoaded", () => {
  fetch("/static/data/zalthorius.json")
    .then((response) => response.json())
    .then((data) => {
      const gallery = document.getElementById("anime-gallery");
      data.anime_images.forEach((image_url) => {
        const img = document.createElement("img");
        img.src = image_url;
        gallery.appendChild(img);
      });
    });
});


