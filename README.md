# BMA - Bornhack Media Archive

[![Run Tox CI](https://github.com/bornhack/bma/actions/workflows/tox.yml/badge.svg?branch=develop)](https://github.com/bornhack/bma/actions/workflows/tox.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/bornhack/bma/graph/badge.svg?token=AN3NmaCDAr)](https://codecov.io/gh/bornhack/bma)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bornhack/bma/develop.svg)](https://results.pre-commit.ci/latest/github/bornhack/bma/develop)

## What:

The BornHack Media Archive is a site for sharing pictures, videos, audio and documents from BornHack events.  

It uses the BornHack website oauth2 provider for login (i.e. you log in with your BornHack.dk account), Django as a framework and PostgreSQL as a database.

## Setup:
> ⚠️ Note! The server is using database functions **not** compatible with SQLite! Use PostgreSQL instead 😁

BMA uses BornHack OIDC for authorization, so start by creating an oauth app on the BornHack instance you wish to use as auth server. This can be bornhack.dk or a local dev instance:

1. Login to the BornHack instance and go to: `/o/applications`.

2. Register a new app.

3. Choose client type: `public` and grant type: `authorization code`.

4. Enter your redirect uri's: "*BMA_BASEURL/accounts/oidc/bornhack/login/callback/*" e.g:

    >`http://127.0.0.1:8001/accounts/oidc/bornhack/login/callback/`

    ⚠️ For local development, make sure it's HTTP not HTTPS!

5. Choose algorithm: `RSA with SHA-2 256`, make a note of `Client id`and `Client secret`, then save ✅

6. Then copy `bma/environment_settings.py.dist` to `bma/environment_settings.py` and either edit it directly, or use .env file or environment variables to configure.

    >⚠️ Note: If it's a local dev, you might have more success making a copy of `bma/environment_settings.py.ci` and renaming it to: `bma/environment_settings.py` - The other template contains Jinja code, which Python doesn't like 😕

7. Enter the `Client id` and `Client secret` from earlier:

    ```
    BORNHACK_OIDC_CLIENT_ID = "client_id"
    BORNHACK_OIDC_CLIENT_SECRET = "client_secret"
    ```

8. And make sure the OIDC server URL is configured correctly:

    ````
    BORNHACK_OIDC_SERVER_URL = "http://bornhack.dk/o/.well-known/openid-configuration"
    ````

9. Now run `manage.py migrate` (or `make init`)

    * If you get a database error about missing 'gist', you need to run `create extension btree_gist;` on your postgresql instance.

10. Run `manage.py createsuperuser` (`make manage createsuperuser`) to create a local database-based superuser in the BMA instance

11. Now run `manage.py runserver`or `make run`, tada! 🎉

It should now be possible to login to BMA using a BornHack account.

⚠️ To use the CLI app for uploading or BMA workers, **make sure** the url of the autocreated oauth application for the user matches the BMA instance (for localhost dev change https to http).  
⚠️ Make also sure you've added your user to the appropriate groups and have been given the neccesary permissions - otherwise file uploading or job grinding will not work!

## Contribute:

 Bornhack Media Archive is still under development, so please submit any issues you come across! or a pull-request if you're *that* clever😉

 #### Contributers:

<a href="https://github.com/bornhack/bma/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=bornhack/bma"/>
</a>