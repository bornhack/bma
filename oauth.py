"""Quick oauth2 authorization code flow demo for whatever.

Create a user, login, go to /o/applications/ and create a new application:
- type: public
- grant type: authorization code
- redirect uri https://example.com/redirect/

Then call this script with <hostname> <username> <password> <client_id>
./oauth.py http://127.0.0.1:8080 admin admin some_client_id

"""
import base64
import hashlib
import random
import string
import sys
from urllib.parse import parse_qs
from urllib.parse import urlparse

import requests

host = sys.argv[1]
username = sys.argv[2]
password = sys.argv[3]
client_id = sys.argv[4]

s = requests.Session()
csrf = s.get(host + "/api/csrf/")
csrf = s.post(
    host + "/accounts/login/?next=/api/csrf/",
    data={
        "csrfmiddlewaretoken": csrf.text.strip(),
        "login": username,
        "password": password,
    },
)
code_verifier = "".join(
    random.choice(string.ascii_uppercase + string.digits)
    for _ in range(random.randint(43, 128))
)
code_verifier = base64.urlsafe_b64encode(code_verifier.encode("utf-8"))
code_challenge = hashlib.sha256(code_verifier).digest()
code_challenge = (
    base64.urlsafe_b64encode(code_challenge).decode("utf-8").replace("=", "")
)
state = "".join(random.choice(string.ascii_letters) for i in range(15))

data = {
    "csrfmiddlewaretoken": csrf.text.strip(),
    "client_id": client_id,
    "state": state,
    "redirect_uri": "https://example.com/redirect/",
    "response_type": "code",
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
    "nonce": "",
    "claims": "",
    "scope": "read",
    "allow": "Authorize",
}
auth = s.post(host + "/o/authorize/", allow_redirects=False, data=data)
url = auth.headers["Location"]
result = urlparse(url)
qs = parse_qs(result.query)
assert state == qs["state"][0]
authcode = qs["code"][0]
token = s.post(
    host + "/o/token/",
    data={
        "grant_type": "authorization_code",
        "code": authcode,
        "redirect_uri": "https://example.com/redirect/",
        "client_id": client_id,
        "code_verifier": code_verifier,
    },
)
print(token.json())
