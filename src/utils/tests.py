"""Unit tests base class."""

import base64
import hashlib
import json
import logging
import secrets
import string
import uuid
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
from users.models import User

Application = get_application_model()
AccessToken = get_access_token_model()
Grant = get_grant_model()


class BmaTestBase(TestCase):
    """The base class used by all BMA tests."""

    users: list[User]
    files: list[str]
    albums: list[str]
    user0: User
    user1: User
    creator2: User
    creator3: User
    moderator4: User
    moderator5: User
    curator6: User
    curator7: User
    superuser: User
    clientinfo: dict[str, str]
    creator2_album: str
    creator3_album: str
    allfiles_album: str
    tokeninfos: dict[User, dict[str, str]]
    tokens: dict[User, str]
    file_uuid: str

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        # disable logging
        logging.disable(logging.WARNING)
        cls.client = Client(enforce_csrf_checks=False)

        # create 2 regular users, 2 creators, 2 moderators, 2 curators, and 1 superuser
        cls.users = []
        cls.tokeninfos = {}
        cls.tokens = {}
        for i in range(9):
            kwargs: dict[str, bool | str] = {}
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
            cls.tokens[user] = cls.get_access_token(user)
            user.save()
            cls.client.logout()
        # clientinfo
        cls.clientinfo = {"client_uuid": str(uuid.uuid4()), "client_version": settings.BMA_VERSION}
        # create groups and add users
        creators, _ = Group.objects.get_or_create(name=settings.BMA_CREATOR_GROUP_NAME)
        creators.user_set.add(cls.creator2, cls.creator3)
        moderators, _ = Group.objects.get_or_create(name=settings.BMA_MODERATOR_GROUP_NAME)
        moderators.user_set.add(cls.moderator4, cls.moderator5)
        curators, _ = Group.objects.get_or_create(name=settings.BMA_CURATOR_GROUP_NAME)
        # everyone is a curator (except user0 and user1)
        curators.user_set.add(cls.creator2, cls.creator3, cls.moderator4, cls.moderator5, cls.curator6, cls.curator7)

    @classmethod
    def get_access_token(cls, user: User) -> str:
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
        data: dict[str, str | bool] = {
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
        cls.tokeninfos[user] = json.loads(response.content)
        return f"Bearer {cls.tokeninfos[user]['access_token']}"

    @classmethod
    def file_upload(  # noqa: PLR0913
        cls,
        *,
        uploader: str = "creator2",
        filepath: str | Path = settings.BASE_DIR / "static_src/images/file-video-solid.png",
        title: str = "some title",
        file_license: str = "CC_ZERO_1_0",
        mimetype: str = "image/png",
        attribution: str = "fotoarne",
        description: str = "",
        original_source: str = "https://example.com/something.png",
        tags: list[str] | None = None,
        expect_status_code: int = 201,
        width: int = 800,
        height: int = 600,
        thumbnail: bool = False,
    ) -> str:
        """The upload method used by many tests."""
        metadata: dict[str, str | int | list[str]] = {
            "title": title,
            "license": file_license,
            "attribution": attribution,
            "mimetype": mimetype,
            "original_source": original_source,
        }
        if description:
            metadata["description"] = description
        if tags:
            metadata["tags"] = tags
        if width:
            metadata["width"] = width
            metadata["height"] = height
        with Path(filepath).open("rb") as f:
            payload = {
                "file_data": f,
                "file_metadata": json.dumps(metadata),
                "client": json.dumps(cls.clientinfo),
            }
            if thumbnail:
                payload["thumbnail_metadata"] = json.dumps(
                    {
                        "mimetype": "image/png",
                        "width": 200,
                        "height": 200,
                    }
                )
                payload["thumbnail_data"] = f
            response = cls.client.post(
                reverse("api-v1-json:upload"),
                payload,
                headers={"authorization": cls.tokens[getattr(cls, uploader)]},
            )
        assert response.status_code == expect_status_code, (
            f"expected status code {expect_status_code}, got {response.status_code}"
        )
        if expect_status_code != 201:
            return ""
        data = response.json()["bma_response"]
        assert "uuid" in data
        if not title:
            title = Path(filepath).name
        assert data["title"] == title, "wrong title"
        assert data["attribution"] == attribution, "wrong attribution"
        assert data["license"] == file_license, "wrong license"
        assert data["source"] == original_source, "wrong source"
        if tags:
            tags.sort()
            assert data["tags"] == [{"name": tag, "slug": tag, "weight": 1} for tag in tags]
        cls.file_uuid = data["uuid"]
        return data["uuid"]  # type: ignore[no-any-return]

    @classmethod
    def album_create_api(
        cls,
        *,
        title: str = "album title here",
        description: str = "album description here",
        files: list[str] | None = None,
        creator: str = "curator6",
    ) -> str:
        """Create an album using the api, optionally with some files."""
        response = cls.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": title,
                "description": description,
                "files": files if files else [],
            },
            headers={"authorization": cls.tokens[getattr(cls, creator)]},
            content_type="application/json",
        )
        assert response.status_code == 201
        return response.json()["bma_response"]["uuid"]  # type: ignore[no-any-return]

    @classmethod
    def album_create_view(
        cls,
        *,
        title: str = "album title here",
        description: str = "album description here",
        files: list[str] | None = None,
        creator: str = "curator6",
    ) -> str:
        """Create an album using the html view, optionally with some files."""
        cls.client.login(username=creator, password="secret")
        response = cls.client.post(
            path=reverse("albums:album_create"),
            data={
                "title": title,
                "description": description,
                "files": files if files else [],
            },
            follow=True,
        )
        assert response.status_code == 200
        assert " created!" in response.content.decode()
        return response.context_data["album"].uuid  # type: ignore[no-any-return]

    @classmethod
    def admin_files_action(cls, *file_uuids: str, username: str, action: str) -> None:
        """Approve or publish or other action on the files using the admin."""
        adminurl = reverse("file_admin:files_basefile_changelist")
        data = {"action": action, "_selected_action": file_uuids}
        cls.client.login(username=username, password="secret")
        response = cls.client.post(adminurl, data, follow=True)
        assert response.status_code == 200

    @classmethod
    def upload_initial_test_files(cls) -> None:
        """Upload some files for testing."""
        # upload some files as creator2
        cls.files = [cls.file_upload(title=f"creator2 file {i}", tags=[f"tag{i}", "foo"]) for i in range(11)]
        cls.creator2_album = cls.album_create_view(creator="creator2", title="creator2 first 11", files=cls.files)

        # upload some files as creator3
        for i in range(9):
            cls.files.append(cls.file_upload(uploader="creator3", title=f"creator3 file {i}", tags=[f"tag{i}", "bar"]))
        cls.creator3_album = cls.album_create_api(creator="creator3", title="creator3 first 9", files=cls.files[10:20])

        # upload with attribution
        cls.files.append(cls.file_upload(attribution="fotoflummer"))
        cls.files.append(cls.file_upload(attribution="fotofonzy"))

        # upload with licenses
        cls.files.append(cls.file_upload(file_license="CC_BY_4_0"))
        cls.files.append(cls.file_upload(file_license="CC_BY_SA_4_0"))

        # create an album with all files
        cls.allfiles_album = cls.album_create_api(creator="superuser", title="all files", files=cls.files)
        cls.albums = [cls.creator2_album, cls.creator3_album, cls.allfiles_album]

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
                headers={"authorization": cls.tokens[cls.curator6]},
                content_type="application/json",
            )
            assert response.status_code == 201

    @classmethod
    def approve_files_api(cls, files: list[str], user: User) -> None:
        """Approve files."""
        response = cls.client.patch(
            reverse("api-v1-json:approve_files"),
            {"files": files},
            headers={"authorization": cls.tokens[user]},
            content_type="application/json",
        )
        assert f"approve {len(files)} files OK" in response.content.decode()
        assert response.status_code == 200

    @classmethod
    def publish_files_api(cls, files: list[str], user: User) -> None:
        """Publish files."""
        response = cls.client.patch(
            reverse("api-v1-json:publish_files"),
            {"files": files},
            headers={"authorization": cls.tokens[user]},
            content_type="application/json",
        )
        assert f"publish {len(files)} files OK" in response.content.decode()
        assert response.status_code == 200

    @classmethod
    def delete_files_api(cls, files: list[str], user: User) -> None:
        """Delete files."""
        response = cls.client.delete(
            reverse("api-v1-json:softdelete_files"),
            {"files": files},
            headers={"authorization": cls.tokens[user]},
            content_type="application/json",
        )
        assert f"softdelete {len(files)} files OK" in response.content.decode()
        assert response.status_code == 200

    @classmethod
    def create_albums(cls) -> None:
        """Create some albums for testing."""
        cls.albums = []
        # upload some files as creator2
        cls.files = []
        for _ in range(10):
            cls.files.append(cls.file_upload())
        # publish all the files
        response = cls.client.patch(
            reverse("api-v1-json:publish_files"),
            {"files": cls.files[0:10]},
            headers={"authorization": cls.tokens[cls.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert "publish 10 files OK" in response.content.decode()

        # upload some files as creator3
        for _ in range(10):
            cls.files.append(cls.file_upload(uploader="creator3"))
        # publish all the files
        response = cls.client.patch(
            reverse("api-v1-json:publish_files"),
            {"files": cls.files[10:20]},
            headers={"authorization": cls.tokens[cls.creator3]},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert "publish 10 files OK" in response.content.decode()

        # approve files
        cls.approve_files_api(files=cls.files, user=cls.superuser)

        # create albums
        cls.albums.append(cls.album_create_api(title="creator2 files", files=cls.files[0:10], creator="curator6"))
        cls.albums.append(cls.album_create_view(title="creator3 files", files=cls.files[10:20], creator="curator7"))
