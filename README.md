[![Run Tox CI](https://github.com/bornhack/bma/actions/workflows/tox.yml/badge.svg?branch=develop)](https://github.com/bornhack/bma/actions/workflows/tox.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/bornhack/bma/graph/badge.svg?token=AN3NmaCDAr)](https://codecov.io/gh/bornhack/bma)

# bma
BornHack Media Archive

## What
The BornHack Media Archive is a site for sharing pictures and video from BornHack events. It uses the BornHack website oauth2 provider for login.

## How
> Note! The server is using database functions not compatible with sqlite. Use postgresql instead.


* Copy `bma/environment_settings.py.dist` to `bma/environment_settings.py` and either edit it directly, or use .env file or environment variables to configure.
    * Set `OAUTH_SERVER_BASEURL` to point to a local instance of the BornHack website eg. `http://127.0.0.1:8000`, or leave it pointing at the prod bornhack.dk server.
* Create an oauth app on the BornHack instance you specified in `OAUTH_SERVER_BASEURL`:
    * login to the BornHack instance and go to the url `OAUTH_SERVER_BASEURL/o/applications`.
    * register a new app.
    * client type `confidential`
    * grant type `authorization code`
    * redirect uri's `BMA_BASEURL/accounts/bornhack/login/callback/` eg. `http://127.0.0.1:8001/accounts/bornhack/login/callback/`.
* Run `manage.py migrate`
    * If you get a database error about missing 'gist', you need to run `create extension btree_gist;` on your postgresql instance.
* Run `manage.py createsuperuser` to create a local database user in the BMA instance
* Log in with the superuser and add a social app on the BMA admin website using the client id and secret from the bornhack website used in the above step.
* Move `example.com` to `chosen sites`.


It should now be possible to login to BMA using a BornHack account.
