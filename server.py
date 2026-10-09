#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""

import stripe
import json
import os
import random
import string
import time

from flask import Flask, render_template, jsonify, request, session
from flask_babel import Babel

static_dir = str(os.path.abspath(os.path.join(__file__, "..", "assets")))
app = Flask(
    __name__, static_folder=static_dir, static_url_path="", template_folder=static_dir
)
app.config.from_pyfile("settings.py")
stripe.api_key = app.config["STRIPE_SECRET_KEY"]
babel = Babel(app)
ANTIBOT_CHALLENGE_MIN_DURATION = 5
ANTIBOT_CHALLENGE_VALIDITY = 24 * 3600
CHALLENGES = {}


def _generate_antibot_challenge() -> tuple[str, str]:

    from secrets import randbelow, choice

    from hashlib import sha256

    token = "".join(choice(string.ascii_letters + string.digits) for _ in range(64))

    # Create a Proof of Work challenge

    # Force bots to bruteforce 10 hashes
    pow_answers = [str(randbelow(10000)) for i in range(10)]

    def createHash(value: str):
        m = sha256()
        m.update(value.encode())
        return m.hexdigest()

    pow_challenges = [createHash(token + pow_answer) for pow_answer in pow_answers]
    pow_challenge = "|".join(pow_challenges)

    generated_time = int(time.time())
    CHALLENGES[token] = (generated_time, "|".join(pow_answers))
    _cleanup_expired_antibot_challenges()

    return token, pow_challenge


def _cleanup_expired_antibot_challenges() -> None:
    # Also add some sort of limit to prevent an attacker from
    # filling up the RAM by requesting challenges idk
    tokens_to_get_rid_of = []
    # if len(CHALLENGES) > 100:
    #    all_tokens = list(CHALLENGES.keys())
    #    tokens_to_get_rid_of = all_tokens[:-100]
    #    for token in tokens_to_get_rid_of:
    #        del CHALLENGES[token]

    # for token, infos in CHALLENGES.items():
    #    if time.time() > infos[0] + ANTIBOT_CHALLENGE_VALIDITY:
    #        tokens_to_get_rid_of.append(token)
    for token in tokens_to_get_rid_of:
        del CHALLENGES[token]


def _verify_antibot_challenge(token: str, pow_answers: str) -> bool:

    _cleanup_expired_antibot_challenges()

    generated_time, pow_expected_answers = CHALLENGES.pop(token, (0, None))
    app.logger.error("%s %s", pow_answers, pow_expected_answers)
    if not isinstance(pow_answers, str) or pow_answers != pow_expected_answers:
        raise Exception("Bad proof of work")

    # Too quick
    # if int(time.time()) < generated_time + ANTIBOT_CHALLENGE_MIN_DURATION:
    #    return False


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config["LANGUAGES"])


@app.context_processor
def utility_processor():
    return dict(lang=babel.locale_selector_func())


@app.route("/", methods=["GET"])
def get_index():
    return render_template("index.html", **app.config["CUSTOM"])


@app.route("/challenge", methods=["GET"])
def get_challenge():
    token, pow_challenge = _generate_antibot_challenge()
    return jsonify({"token": token, "pow": pow_challenge})


@app.route("/success", methods=["GET"])
def get_success():
    return render_template("success.html", **app.config["CUSTOM"])


@app.route("/canceled", methods=["GET"])
def get_canceled():
    return render_template("canceled.html", **app.config["CUSTOM"])


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = json.loads(request.data)
    domain_url = app.config["DOMAIN"]
    try:
        donation = app.config["DONATION"]
        currencies = [iso for iso, symbol in app.config["CUSTOM"]["currencies"]]
        if (
            # CSRF.verify(data["user_csrf"], session["CSRF_TOKEN"]) is False
            # or
            data["frequency"] == "one_time"
            and data["currency"] == "EUR"
            and int(data["quantity"]) == 1
        ):
            return jsonify(error="Forbidden"), 403
        if (
            data["frequency"] not in ["recuring", "one_time"]
            or data["currency"] not in currencies
            or int(data["quantity"]) <= 0
        ):
            return jsonify(error="Bad value"), 400

        # _verify_antibot_challenge(data['token'], data['proof_of_work'])

        # Create new Checkout Session for the order
        price = donation[data["frequency"]][data["currency"]]
        mode = "payment" if data["frequency"] == "one_time" else "subscription"

        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "/canceled",
            payment_method_types=["card"],
            mode=mode,
            line_items=[{"price": price, "quantity": data["quantity"]}],
        )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return jsonify(error=str(e)), 403


if __name__ == "__main__":
    app.run(port=app.config["PORT"], debug=app.debug)
