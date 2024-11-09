"""Unit tests base class."""

import base64
import hashlib
import json
import logging
import secrets
import string
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth.models import Group
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


class BmaTestBase(TestCase):
    """The base class used by all BMA tests."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        # disable logging
        logging.disable(logging.CRITICAL)
        cls.client = Client(enforce_csrf_checks=False)

        # create 2 regular users, 2 creators, 2 moderators, 2 curators, and 1 superuser
        cls.users = []
        for i in range(9):
            kwargs = {}
            if i in [0, 1]:
                kwargs["username"] = f"user{i}"
            elif i in [2, 3]:
                kwargs["username"] = f"creator{i}"
            elif i in [4, 5]:
                kwargs["username"] = f"moderator{i}"
            elif i in [6, 7]:
                kwargs["username"] = f"curator{i}"
            elif i == 8:
                kwargs["username"] = "superuser"
                kwargs["is_superuser"] = True
                kwargs["is_staff"] = True
            kwargs["handle"] = kwargs["username"]
            user = UserFactory.create(**kwargs)
            user.set_password("secret")
            user.save()
            setattr(cls, user.username, user)
            cls.users.append(user)
            user.auth = cls.get_access_token(user)
            user.save()
            cls.client.logout()

        # create groups and add users
        creators, _ = Group.objects.get_or_create(name=settings.BMA_CREATOR_GROUP_NAME)
        creators.user_set.add(cls.creator2, cls.creator3)
        moderators, _ = Group.objects.get_or_create(name=settings.BMA_MODERATOR_GROUP_NAME)
        moderators.user_set.add(cls.moderator4, cls.moderator5)
        curators, _ = Group.objects.get_or_create(name=settings.BMA_CURATOR_GROUP_NAME)
        # everyone is a curator (except user0 and user1)
        curators.user_set.add(cls.creator2, cls.creator3, cls.moderator4, cls.moderator5, cls.curator6, cls.curator7)

    @classmethod
    def get_access_token(cls, user) -> str:  # noqa: ANN001
        """Test the full oauth2 public client authorization code pkce token flow."""
        # generate a verifier string from 43-128 chars
        alphabet = string.ascii_uppercase + string.digits
        code_verifier = "".join(secrets.choice(alphabet) for i in range(43 + secrets.randbelow(86)))
        code_verifier_base64 = base64.urlsafe_b64encode(code_verifier.encode("utf-8"))
        code_challenge = hashlib.sha256(code_verifier_base64).digest()
        code_challenge_base64 = base64.urlsafe_b64encode(code_challenge).decode("utf-8").replace("=", "")

        # this requires login
        cls.client.force_login(user)

        # get the authorization code
        data = {
            "client_id": user.webapp_oauth_client_id,
            "state": "something",
            "redirect_uri": "https://localhost/api/csrf/",
            "response_type": "code",
            "allow": True,
            "code_challenge": code_challenge_base64,
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

        # get the access token
        response = cls.client.post(
            "/o/token/",
            {
                "grant_type": "authorization_code",
                "code": qs["code"],
                "redirect_uri": "https://localhost/api/csrf/",
                "client_id": user.webapp_oauth_client_id,
                "code_verifier": code_verifier_base64.decode("utf-8"),
            },
        )
        assert response.status_code == 200
        user.tokeninfo = json.loads(response.content)
        return f"Bearer {user.tokeninfo['access_token']}"

    @classmethod
    def file_upload(  # noqa: PLR0913
        cls,
        *,
        uploader: str = "creator2",
        filepath: str = settings.BASE_DIR / "static_src/images/logo_wide_black_500_RGB.png",
        title: str = "some title",
        file_license: str = "CC_ZERO_1_0",
        mimetype: str = "image/png",
        attribution: str = "fotoarne",
        description: str = "",
        original_source: str = "https://example.com/something.png",
        tags: list[str] | None = None,
        thumbnail_url: str = "",
        return_full: bool = False,
        expect_status_code: int = 201,
        width: int | None = 800,
        height: int | None = 600,
    ) -> str | dict[str, str]:
        """The upload method used by many tests."""
        metadata = {
            "title": title,
            "license": file_license,
            "attribution": attribution,
            "mimetype": mimetype,
            "original_source": original_source,
        }
        if thumbnail_url:
            metadata["thumbnail_url"] = thumbnail_url
        if description:
            metadata["description"] = description
        if tags:
            metadata["tags"] = tags
        if width:
            metadata["width"] = width
            metadata["height"] = height
        with Path(filepath).open("rb") as f:
            response = cls.client.post(
                reverse("api-v1-json:upload"),
                {
                    "f": f,
                    "metadata": json.dumps(metadata),
                },
                headers={"authorization": getattr(cls, uploader).auth},
            )
        assert response.status_code == expect_status_code
        if expect_status_code == 422:
            return None
        data = response.json()["bma_response"]
        assert "uuid" in data
        if not title:
            title = Path(filepath).name
        assert data["title"] == title, "wrong title"
        assert data["attribution"] == attribution, "wrong attribution"
        assert data["license"] == file_license, "wrong license"
        assert data["source"] == original_source, "wrong source"
        cls.file_uuid = data["uuid"]
        if tags:
            tags.sort()
            assert data["tags"] == [{"name": tag, "slug": tag, "weight": 1} for tag in tags]
        return data if return_full else data["uuid"]

    @classmethod
    def album_create(
        cls,
        *,
        title: str = "album title here",
        description: str = "album description here",
        files: list[str] | None = None,
        creator: str = "curator6",
    ) -> str:
        """Create an album optionally with some files."""
        response = cls.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": title,
                "description": description,
                "files": files if files else [],
            },
            headers={"authorization": getattr(cls, creator).auth},
            content_type="application/json",
        )
        assert response.status_code == 201
        return response.json()["bma_response"]["uuid"]

    @classmethod
    def admin_files_action(cls, *file_uuids: str, username: str, action: str) -> None:
        """Approve or publish or other action on the files using the admin."""
        # make moderator4 approve 5 of the files owned by creator2 (using the admin)
        adminurl = reverse("file_admin:files_basefile_changelist")
        data = {"action": action, "_selected_action": file_uuids}
        cls.client.login(username=username, password="secret")
        response = cls.client.post(adminurl, data, follow=True)
        assert response.status_code == 200

    @classmethod
    def api_album_create(
        cls,
        username: str,
        title: str = "album title",
        description: str = "album description goes here",
        files: list[str] | None = None,
    ) -> str:
        """Create album using the api and return the album uuid."""
        response = cls.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": title,
                "description": description,
                "files": files,
            },
            headers={"authorization": getattr(cls, username).auth},
            content_type="application/json",
        )
        assert response.status_code == 201
        return response.json()["bma_response"]["uuid"]

    @classmethod
    def upload_initial_test_files(cls) -> None:
        """Upload some files for testing."""
        # upload some files as creator2
        cls.files = [cls.file_upload(title=f"creator2 file {i}", tags=[f"tag{i}", "foo"]) for i in range(11)]
        cls.creator2_album = cls.api_album_create(username="curator6", title="creator2 first 11", files=cls.files)

        # upload some files as creator3
        for i in range(9):
            cls.files.append(cls.file_upload(uploader="creator3", title=f"creator3 file {i}", tags=[f"tag{i}", "bar"]))
        cls.creator3_album = cls.api_album_create(username="curator7", title="creator3 first 9", files=cls.files[10:20])

        # upload with attribution
        cls.files.append(cls.file_upload(attribution="fotoflummer"))
        cls.files.append(cls.file_upload(attribution="fotofonzy"))

        # upload with licenses
        cls.files.append(cls.file_upload(file_license="CC_BY_4_0"))
        cls.files.append(cls.file_upload(file_license="CC_BY_SA_4_0"))

        # create an album with all files
        cls.allfiles_album = cls.api_album_create(username="curator7", title="all files", files=cls.files)

    @classmethod
    def change_initial_test_files(cls) -> None:
        """Change some of the uploaded files."""
        # approve some of creator2 files as moderator4
        cls.admin_files_action(*cls.files[:5], username="moderator4", action="approve")

        # publish some of creator2 files
        cls.admin_files_action(*cls.files[2:7], username="creator2", action="publish")

        # softdelete some of creator3 files
        cls.admin_files_action(*cls.files[11:16], username="creator3", action="softdelete")

        # tag a couple of more files
        for i in range(2, 5):
            tags = ["testtag", "more 🔥"]
            response = cls.client.post(
                reverse("api-v1-json:file_tag", kwargs={"file_uuid": cls.files[i]}),
                data={
                    "tags": tags,
                },
                headers={"authorization": cls.curator6.auth},
                content_type="application/json",
            )
            assert response.status_code == 201
