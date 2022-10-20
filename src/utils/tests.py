import base64
import hashlib
import json
import logging
import random
import string
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlsplit

from django.test import Client
from django.test import TestCase
from django.urls import reverse
from oauth2_provider.models import get_access_token_model
from oauth2_provider.models import get_application_model
from oauth2_provider.models import get_grant_model

from users.factories import UserFactory

Application = get_application_model()
AccessToken = get_access_token_model()
Grant = get_grant_model()


class ApiTestBase(TestCase):
    """The base class used by all api tests."""

    @classmethod
    def setUpTestData(cls):
        """Test setup."""
        # disable logging
        logging.disable(logging.CRITICAL)

        # TODO figure out why using ORJSONRenderer() doesn't work
        # cls.client = Client(enforce_csrf_checks=True, json_encoder=ORJSONRenderer())
        cls.client = Client(enforce_csrf_checks=True)

        # create 4 regular users and 1 superuser
        for i in range(6):
            if i == 5:
                username = "superuser"
            else:
                username = f"user{i}"
            user = UserFactory.create(username=username)
            user.set_password("secret")
            if i == 5:
                user.is_superuser = True
            user.save()
            setattr(cls, username, user)
            # create oauth application
            cls.application = Application.objects.create(
                name="Test Application",
                redirect_uris="https://example.com/noexist/callback/",
                user=user,
                client_type=Application.CLIENT_PUBLIC,
                authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
                client_id=f"client_id_{username}",
                client_secret="client_secret",
                skip_authorization=True,
            )
            user.auth = cls.get_access_token(user)
            user.save()
        cls.client.logout()

    @classmethod
    def get_access_token(cls, user):
        """Test the full oauth2 public client authorization code pkce token flow."""

        # prepare to get access token
        code_verifier = "".join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(random.randint(43, 128))
        )
        code_verifier = base64.urlsafe_b64encode(code_verifier.encode("utf-8"))
        code_challenge = hashlib.sha256(code_verifier).digest()
        code_challenge = (
            base64.urlsafe_b64encode(code_challenge).decode("utf-8").replace("=", "")
        )

        # this requires login
        cls.client.force_login(user)

        # get the authorization code
        data = {
            "client_id": f"client_id_{user.username}",
            "state": "something",
            "redirect_uri": "https://example.com/noexist/callback/",
            "response_type": "code",
            "allow": True,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        response = cls.client.get("/o/authorize/", data=data)
        assert response.status_code == 302
        assert "Location" in response.headers
        result = urlsplit(response.headers["Location"])
        qs = parse_qs(result.query)
        assert "code" in qs

        # the rest doesn't require login
        cls.client.logout()

        # get the code to get the access token
        response = cls.client.post(
            "/o/token/",
            {
                "grant_type": "authorization_code",
                "code": qs["code"],
                "redirect_uri": "https://example.com/noexist/callback/",
                "client_id": f"client_id_{user.username}",
                "code_verifier": code_verifier.decode("utf-8"),
            },
        )
        assert response.status_code == 200
        user.tokeninfo = json.loads(response.content)
        return f"Bearer {user.tokeninfo['access_token']}"

    def file_upload(
        cls,
        filepath="static_src/images/logo_wide_black_500_RGB.png",
        title="some title",
        license="CC_ZERO_1_0",
        attribution="fotoarne",
        source="the internet",
        return_full=False,
        expect_status_code=201,
    ):
        with open(filepath, "rb") as f:
            response = cls.client.post(
                reverse("api-v1-json:upload"),
                {
                    "f": f,
                    "metadata": json.dumps(
                        {
                            "title": title,
                            "license": license,
                            "attribution": attribution,
                            "source": source,
                        },
                    ),
                },
                HTTP_AUTHORIZATION=cls.user1.auth,
            )
        assert response.status_code == expect_status_code
        if expect_status_code == 422:
            return
        data = response.json()
        assert "uuid" in data
        if not title:
            title = Path(filepath).name
        assert data["title"] == title
        assert data["attribution"] == attribution
        assert data["license"] == license
        assert data["source"] == source
        cls.file_uuid = data["uuid"]
        if return_full:
            return data
        else:
            return data["uuid"]
