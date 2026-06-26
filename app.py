from flask import Flask, jsonify, render_template, request, url_for
import os

from data.challenges import CHALLENGES

app = Flask(__name__)

@app.route("/")
def home():
    return render_template(
        "home.html",
        challenges=CHALLENGES
    )

@app.route("/api/product")
def api_product():
    return jsonify({
        "product": {
            "title": "Research Jacket",
            "description": "A product loaded from a REST API endpoint for scraping experiments.",
            "images": [
                url_for('static', filename='images/look1.jpg'),
                url_for('static', filename='images/look2.jpg'),
                url_for('static', filename='images/look3.jpg')
            ]
        }
    })

@app.route("/graphql", methods=["POST"])
def graphql():
    body = request.get_json(silent=True) or {}
    query = body.get('query', '')

    if 'product' in query:
        return jsonify({
            'data': {
                'product': {
                    'title': 'Research Jacket',
                    'description': 'A product loaded from a GraphQL endpoint for scraping experiments.',
                    'images': [
                        url_for('static', filename='images/look1.jpg'),
                        url_for('static', filename='images/look2.jpg'),
                        url_for('static', filename='images/look3.jpg')
                    ]
                }
            }
        })

    return jsonify({ 'errors': [{ 'message': 'Unsupported query' }] }), 400

@app.route("/challenge/<challenge_id>")
def challenge(challenge_id):
    challenge = CHALLENGES.get(challenge_id)

    if not challenge:
        return "Challenge Not Found", 404

    return render_template(
        "challenge.html",
        challenge=challenge
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )