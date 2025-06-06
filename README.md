# Pepettes, a donation form

A small form to donate money to a project. Support one-time or recuring payment.

**Demo**

The demo is running in test mode -- use `4242424242424242` as a test card number with any CVC + future expiration date.

Use the `4000002500003155` test card number to trigger a 3D Secure challenge flow.

Read more about testing on Stripe at <https://stripe.com/docs/testing>.

## How to run locally

Follow the steps below to run locally.

```bash
git clone https://github.com/YunoHost/pepettes
cd pepettes
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

Create a settings.py file with :

```python
ENV = 'development'
PORT = 8000
DOMAIN = 'http://localhost:8000'
SECRET_KEY = '712AZPOC87HXD5SQSb12rd'
SECRET_CSRF_KEY = '712AZPOC87HXD5SQSb12'
LANGUAGES = ['en', 'fr']
BABEL_TRANSLATION_DIRECTORIES = 'locales'

# Customization
CUSTOM = {}
CUSTOM['name'] = 'YunoHost'
# You can activate a donation management portal on https://dashboard.stripe.com/settings/billing/portal and display a link to it on the homepage.
CUSTOM['portal_url'] = ''
CUSTOM['contact_url'] = 'mailto:donate-6521@yunohost.org'
CUSTOM['logo'] = 'https://yunohost.org/user/images/logo.png'
CUSTOM['favicon'] = 'https://yunohost.org/user/themes/yunohost-docs/images/favicon.png'
CUSTOM['currencies'] = [
    ('EUR', '€'),
    ('USD', '$')
]

# Stripe keys
CUSTOM['stripe_publishable_key'] = 'pk_test_gOgGjacs9YfvDJY03BRZ576O'
STRIPE_SECRET_KEY = 'sk_test_'

# Stripe subscription data
DONATION={'one_time':{}, 'recuring': {}}
DONATION['one_time']['EUR'] = 'price_1IKuPVE7vOmTpJBiYMq7ztLH'
DONATION['one_time']['USD'] = 'price_1IKuQfE7vOmTpJBi0A3nRGCJ'
DONATION['recuring']['EUR'] = 'price_1IKumjE7vOmTpJBikyqS2NqD'
DONATION['recuring']['USD'] = 'price_1IKumAE7vOmTpJBiO4CEfa3Q'
```

```bash
export FLASK_APP=server.py
python3 -m flask run --port=8000
```

```bash
# extract new strings or update existing strings
pybabel extract -F babel.cfg -o messages.pot *.py assets/*.html

# then update the locale files, please translate into french any new string
pybabel update -i messages.pot -d locales
```
