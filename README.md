[![Run Tox CI](https://github.com/bornhack/bma/actions/workflows/tox.yml/badge.svg?branch=develop)](https://github.com/bornhack/bma/actions/workflows/tox.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/bornhack/bma/graph/badge.svg?token=AN3NmaCDAr)](https://codecov.io/gh/bornhack/bma)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bornhack/bma/develop.svg)](https://results.pre-commit.ci/latest/github/bornhack/bma/develop)

# bma
BornHack Media Archive

## What
The BornHack Media Archive is a site for sharing pictures and video from BornHack events. It uses the BornHack website oauth2 provider for login.

## How
> Note! The server is using database functions not compatible with sqlite. Use postgresql instead.


* BMA uses BornHack OIDC for auth. Start by creating an oauth app on the BornHack instance you wish to use as auth server. This can be bornhack.dk or a local dev instance:
    * login to the BornHack instance and go to the url `/o/applications`.
    * register a new app.
    * client type `public`
    * grant type `authorization code`
    * redirect uri's `BMA_BASEURL/accounts/oidc/bornhack/login/callback/` eg. `http://127.0.0.1:8001/accounts/oidc/bornhack/login/callback/`.
    * Algorithm `RSA with SHA-2 256`

* Then copy `bma/environment_settings.py.dist` to `bma/environment_settings.py` and either edit it directly, or use .env file or environment variables to configure.
* Run `manage.py migrate`
    * If you get a database error about missing 'gist', you need to run `create extension btree_gist;` on your postgresql instance.
* Run `manage.py createsuperuser` to create a local database-based superuser in the BMA instance

It should now be possible to login to BMA using a BornHack account.

To use the CLI app for uploading or BMA workers make sure the url of the autocreated oauth application for the user matches the BMA instance (for localhost dev change https to http).
