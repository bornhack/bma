# bma
BornHack Media Archive

## What
The BornHack Media Archive is a site for sharing pictures and video from BornHack events. It uses the BornHack website oauth2 provider for login.

## How
* Copy `bma/environment_settings.py.dist` to `bma/environment_settings.py` and either edit it directly, or use .env file or environment variables to configure.
* Set `OAUTH_SERVER_BASEURL` to point to a local instance of the BornHack website, or leave it pointing at the prod bornhack.dk server.
* Create an oauth app on the BornHack website specified in `OAUTH_SERVER_BASEURL`, client type `confidential` and grant type `authorization code`
* Add a social app on the BMA website using the client id and secret generated in the above step.

It should now be possible to login to BMA using a BornHack account.
