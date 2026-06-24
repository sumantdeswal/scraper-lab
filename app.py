from flask import Flask, render_template
import os

app = Flask(__name__)

CHALLENGES = {
    1: {
        "name": "Plain HTML Images",
        "difficulty": "Easy"
    }
}

@app.route("/")
def home():
    return render_template(
        "home.html",
        challenges=CHALLENGES
    )

@app.route("/challenge/<int:challenge_id>")
def challenge(challenge_id):

    challenge = CHALLENGES.get(challenge_id)

    if not challenge:
        return "Challenge Not Found", 404

    return render_template(
        f"challenge_{challenge_id}.html",
        challenge=challenge
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )