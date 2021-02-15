# Donate to YunoHost

A small form to donate to YunoHost. Support one-time or recuring payment.

**Demo**

The demo is running in test mode -- use `4242424242424242` as a test card number with any CVC + future expiration date.

Use the `4000002500003155` test card number to trigger a 3D Secure challenge flow.

Read more about testing on Stripe at https://stripe.com/docs/testing.

## How to run locally

Follow the steps below to run locally.

```
git clone https://github.com/yunohost/donate
cd donate
python3 -m venv venv
source venv/bin/activate
pip3 install requirements.txt
```

Create a .env file with :
```
PORT=8000
DEBUG=True
PROJECT_NAME=YunoHost
DOMAIN=http://localhost:8000
STATIC_DIR=assets

# Stripe keys
STRIPE_PUBLISHABLE_KEY=pk_test_gOgGjacs9YfvDJY03BRZ576O
STRIPE_SECRET_KEY=TO_REPLACE_BY_THE_GOOD_VALUE

# Stripe subscription data
ONE_TIME_EUR_DONATION=price_1IKuPVE7vOmTpJBiYMq7ztLH
RECURING_EUR_DONATION=price_1IKumjE7vOmTpJBikyqS2NqD

ONE_TIME_USD_DONATION=price_1IKuQfE7vOmTpJBi0A3nRGCJ
RECURING_USD_DONATION=price_1IKumAE7vOmTpJBiO4CEfa3Q
```

```
export FLASK_APP=server.py
python3 -m flask run --port=8000
```
