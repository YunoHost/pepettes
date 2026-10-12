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

from cachelib import FileSystemCache
from flask import Flask, render_template, jsonify, request, session, g
from flask_session import Session
from flask_babel import Babel


static_dir = str(os.path.abspath(os.path.join(__file__, "..", "assets")))
app = Flask(
    __name__, static_folder=static_dir, static_url_path="", template_folder=static_dir
)
app.config.from_pyfile("settings.py")
stripe.api_key = app.config["STRIPE_SECRET_KEY"]
app.config["SESSION_PERMANENT"] = False
app.config['SESSION_TYPE'] = 'cachelib'
app.config['SESSION_CACHELIB'] = FileSystemCache(cache_dir='flask_session', threshold=500)
Session(app)
def get_locale():
    return request.accept_languages.best_match(app.config["LANGUAGES"])
babel = Babel(app, locale_selector=get_locale)
babel.locale_selector_func = get_locale
ANTIBOT_CHALLENGE_MIN_DURATION = 5
ANTIBOT_CHALLENGE_VALIDITY = 600
ANTIBOT_MAX_SAME_DONATION_IN_A_DAY = 50
challenges = FileSystemCache(cache_dir='challenges', threshold=500, default_timeout=ANTIBOT_CHALLENGE_VALIDITY)
similarities = FileSystemCache(cache_dir='similarities', threshold=5000, default_timeout=24*3600)

def _generate_antibot_challenge(pow_force = 1000, extra = "") -> tuple[str, str]:

    from secrets import randbelow, choice

    from hashlib import sha256

    token = "".join(
        choice(string.ascii_letters + string.digits) for _ in range(64)
    )

    # Create a Proof of Work challenge

    # Force bots to bruteforce 10 hashes
    pow_sum = 0
    pow_answers = [str(pow_sum := randbelow(pow_force) + pow_sum) for i in range(20)]
    def createHash(value: str):
        m = sha256()
        m.update(value.encode())
        return m.hexdigest()
    pow_challenges = [createHash(token + pow_answer)
                      for pow_answer in pow_answers]
    pow_challenge = '|'.join(pow_challenges)

    generated_time = int(time.time())
    challenges.set(token, (generated_time, '|'.join(pow_answers) + extra))
    _cleanup_expired_antibot_challenges()

    return token, pow_challenge


def _cleanup_expired_antibot_challenges() -> None:
    # Also add some sort of limit to prevent an attacker from
    # filling up the RAM by requestinsession["challenges"] idk
    # tokens_to_get_rid_of = []
    # if len(session["challenges"]) > 10:
    #     all_tokens = list(session["challenges"].keys())
    #     tokens_to_get_rid_of = all_tokens[:-10]
    #     for token in tokens_to_get_rid_of:
    #         del session["challenges"][token]
    pass


def _verify_antibot_challenge(token: str, pow_answers: str) -> None:

    _cleanup_expired_antibot_challenges()

    if not (challenge := challenges.get(token)):
        raise Exception("Challenge expired")
    app.logger.error('%s', str(challenge))

    challenges.delete(token)
    generated_time, pow_expected_answers = challenge
    if not isinstance(pow_answers, str) or pow_answers != pow_expected_answers:
        raise Exception("Bad proof of work")


@app.context_processor
def utility_processor():
    return dict(lang=babel.locale_selector_func())

def count_similarities(key, since=3600):
    if not (last_calls := similarities.get(key)):
        last_calls = []
    now = time.time()
    return sum(1 for call in last_calls if call > now - since)

def log_similarity(key, prune=3600):
    if not (last_calls := similarities.get(key)):
        last_calls = []
    now = int(time.time())
    last_calls = [call for call in last_calls if call > now - prune]
    similarities.set(key, last_calls + [int(time.time())])


@app.route("/", methods=["GET"])
def get_index():
    log_similarity("index")
    return render_template(
        "index.html", **app.config["CUSTOM"]
    )

def under_attack(data, extra):
    # If in last hour, we see more call of challenge than call of index
    # It's very suspicious
    log_similarity("get_pow_force")
    conversion_rate = count_similarities("get_pow_force") / count_similarities("index")

    # If a lot of small price has been requested during the last 24 hours
    if data["quantity"] <= 3:
        log_similarity("small", prune=24 * 3600)
    else:
        log_similarity("not_small", prune=24 * 3600)
    ratio_small_price = count_similarities("small", since=24 * 3600) / count_similarities("not_small", since=24 * 3600)

    # Strange same extra data
    log_similarity(extra, prune=24 * 3600)
    nb_same_challenges = count_similarities(extra, since=24 * 3600)

    return conversion_rate > 2 or ratio_small_price > 2 or nb_same_challenges > ANTIBOT_MAX_SAME_DONATION_IN_A_DAY

def get_pow_force(data, extra):
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    app.logger.error('%s %s', str(ip), str(data))

    # Small price is a high indicator for credit cards tests
    if data["quantity"] == 1:
        pow_force = 20
    elif data["quantity"] < 5:
        pow_force = 10
    elif data["quantity"] < 7:
        pow_force = 7
    elif data["quantity"] < 10:
        pow_force = 5
    else:
        pow_force = 3

    # IP already used in last hour
    # 2th challenge in 1h => +8s, 3th + 16s , 4th +32s  ...
    if ":" in ip:
        ip = ":".join(ip.split(":")[0:3])  # /56
    log_similarity(ip)
    freq_ip = count_similarities(ip)
    if freq_ip >= 2:
        app.logger.warning('FREQ IP: %d', freq_ip)
        pow_force += min(60, 8 * (2 ** max(0, freq_ip - 2)))

    # Seems residential proxy prefers IPv4
    if "." in ip:
        pow_force *= 1.5

    # If we are under attack we increase the effort for every body
    if under_attack(data, extra):
        app.logger.warning('UNDER ATTACK')
        pow_force *= 2

    app.logger.warning('proof of work time: %ds', int(pow_force))

    # With a old core i5 ~2000 hash => 1s
    return min(10**9, round(pow_force) * 2000 * 2)

def get_extra(data):
    return f"{data['quantity']}{data['currency']}{data['frequency']}"


@app.route("/challenge", methods=["POST"])
def get_challenge():
    data = json.loads(request.data)
    currencies = [iso for iso, symbol in app.config["CUSTOM"]["currencies"]]
    if (
        data["frequency"] not in ["recuring", "one_time"]
        or data["currency"] not in currencies
        or int(data["quantity"]) <= 0
    ):
        return jsonify(error="Bad value"), 400
    extra = get_extra(data)
    token, pow_challenge = _generate_antibot_challenge(
        pow_force=get_pow_force(data, extra),
        extra=extra
    )
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

        _verify_antibot_challenge(data['token'], data['proof_of_work'] + get_extra(data))

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
