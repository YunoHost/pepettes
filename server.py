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

from flask import Flask, render_template, jsonify, request, session
from flask_babel import Babel
from flask_simple_csrf import CSRF


static_dir = str(os.path.abspath(os.path.join(__file__, "..", "assets")))
app = Flask(
    __name__, static_folder=static_dir, static_url_path="", template_folder=static_dir
)
app.config.from_pyfile("settings.py")
stripe.api_key = app.config["STRIPE_SECRET_KEY"]
CSRF = CSRF(config={"SECRET_CSRF_KEY": app.config["SECRET_CSRF_KEY"]})
app = CSRF.init_app(app)
babel = Babel(app)


@app.before_request
def before_request():
    if "CSRF_TOKEN" not in session or "USER_CSRF" not in session:
        session["USER_CSRF"] = "".join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(64)
        )
        session["CSRF_TOKEN"] = CSRF.create(session["USER_CSRF"])


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config["LANGUAGES"])


@app.context_processor
def utility_processor():
    return dict(lang=babel.locale_selector_func())


@app.route("/", methods=["GET"])
def get_index():
    return render_template(
        "index.html", **app.config["CUSTOM"], csrf=session["USER_CSRF"]
    )


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
            CSRF.verify(data["user_csrf"], session["CSRF_TOKEN"]) is False
            or data["frequency"] not in ["recuring", "one_time"]
            or data["currency"] not in currencies
            or int(data["quantity"]) <= 0
        ):
            return jsonify(error="Bad value"), 400

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
