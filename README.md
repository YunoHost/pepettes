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
export FLASK_APP=server.py
python3 -m flask run --port=8000
```
