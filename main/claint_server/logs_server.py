from flask import Flask, request, jsonify
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/")
def index():
    return jsonify({"message": "Logs server is running"})



if __name__ == "__main__":
    app.run(host=app.config["SERVER_IP"], port=app.config["SERVER_PORT"])