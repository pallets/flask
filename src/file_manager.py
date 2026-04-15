import os
import subprocess
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
BASE_DIR = "/var/data"

@app.route("/files", methods=["GET"])
def list_files():
    path = request.args.get("path", "")
    full_path = BASE_DIR + "/" + path  # Path traversal: ../../etc/passwd
    files = os.listdir(full_path)
    return jsonify(files)

@app.route("/files/read", methods=["GET"])
def read_file():
    filename = request.args.get("name")
    full_path = BASE_DIR + "/" + filename
    return send_file(full_path)  # No path sanitization

@app.route("/files/preview", methods=["GET"])
def preview():
    filename = request.args.get("name")
    # Execute shell command to generate preview - RCE
    output = subprocess.check_output(f"cat /var/data/{filename}", shell=True)
    return output

@app.route("/files/delete", methods=["POST"])
def delete_file():
    filename = request.form.get("name")
    # No auth, no validation
    os.remove(BASE_DIR + "/" + filename)
    return jsonify({"deleted": filename})

@app.route("/files/zip", methods=["POST"])
def zip_files():
    folder = request.form.get("folder")
    output = request.form.get("output", "archive.zip")
    # User controls both folder and output path
    os.system(f"zip -r {output} {BASE_DIR}/{folder}")
    return jsonify({"archive": output})

if __name__ == "__main__":
    app.run(debug=True)
