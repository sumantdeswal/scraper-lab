import os
from flask import Flask, jsonify, make_response, render_template, request, send_from_directory, url_for

from data.challenges import CHALLENGES
from data.protected_media import build_protected_manifest, initialize_protection_context, serve_protected_image

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "protected-media-demo-secret")

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

    if challenge_id == "protected-media":
        manifest = build_protected_manifest(url_for)
        response = make_response(render_template(
            "challenge.html",
            challenge=challenge,
            protected_media=manifest,
        ))
        initialize_protection_context(response)
        return response
    if challenge_id == "hybrid-challenge":
        # Hybrid challenge uses many of the same protected-media helpers to
        # demonstrate signed URLs, session and cookie protections alongside
        # other delivery mechanisms.
        manifest = build_protected_manifest(url_for)
        response = make_response(render_template(
            "challenge.html",
            challenge=challenge,
            protected_media=manifest,
        ))
        initialize_protection_context(response)
        return response

    return render_template(
        "challenge.html",
        challenge=challenge
    )


@app.route("/protected-media/signed/<image_id>")
def protected_media_signed_image(image_id):
    image_name = serve_protected_image(image_id, "signed")
    if image_name is False:
        return "Forbidden", 403
    if image_name is None:
        return "Not Found", 404

    return send_from_directory("static", image_name, mimetype="image/jpeg")


@app.route("/protected-media/expiring/<image_id>")
def protected_media_expiring_image(image_id):
    image_name = serve_protected_image(image_id, "expiring")
    if image_name is False:
        return "Forbidden", 403
    if image_name is None:
        return "Not Found", 404

    return send_from_directory("static", image_name, mimetype="image/jpeg")


@app.route("/protected-media/cookie/<image_id>")
def protected_media_cookie_image(image_id):
    image_name = serve_protected_image(image_id, "cookie")
    if image_name is False:
        return "Forbidden", 403
    if image_name is None:
        return "Not Found", 404

    return send_from_directory("static", image_name, mimetype="image/jpeg")


@app.route("/protected-media/auth/<image_id>")
def protected_media_auth_image(image_id):
    image_name = serve_protected_image(image_id, "auth")
    if image_name is False:
        return "Forbidden", 403
    if image_name is None:
        return "Not Found", 404

    return send_from_directory("static", image_name, mimetype="image/jpeg")


@app.route("/protected-media/session/<image_id>")
def protected_media_session_image(image_id):
    image_name = serve_protected_image(image_id, "session")
    if image_name is False:
        return "Forbidden", 403
    if image_name is None:
        return "Not Found", 404

    return send_from_directory("static", image_name, mimetype="image/jpeg")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )