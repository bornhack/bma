from django.urls import reverse
from oauth2_provider.models import get_access_token_model
from oauth2_provider.models import get_application_model
from oauth2_provider.models import get_grant_model

from utils.tests import ApiTestBase

Application = get_application_model()
AccessToken = get_access_token_model()
Grant = get_grant_model()


class TestAlbumsApi(ApiTestBase):
    """Test for API endpoints in the albums API."""

    def test_album_create(
        self,
        title="album title here",
        description="album description here",
        files=None,
    ):
        """Test creating an album."""
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": title,
                "description": description,
                "files": files if files else [],
            },
            HTTP_AUTHORIZATION=self.auth,
            content_type="application/json",
        )
        assert response.status_code == 201
        self.album_uuid = response.json()["uuid"]

    def test_album_create_with_files(
        self,
        title="album title here",
        description="album description here",
    ):
        """Test creating an album with files."""
        self.files = []
        for _ in range(10):
            self.files.append(self.file_upload())
        self.test_album_create(title=title, description=description, files=self.files)

    def test_album_update(self):
        """First replace then update."""
        self.test_album_create_with_files()
        # try with the wrong user
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            HTTP_AUTHORIZATION=f"Bearer {self.user2.tokeninfo['access_token']}",
            content_type="application/json",
        )
        assert response.status_code == 403
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            HTTP_AUTHORIZATION=self.auth,
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["files"]) == 2
        assert response.json()["title"] == "new title"
        assert response.json()["description"] == "description here"

        response = self.client.patch(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {"files": self.files},
            HTTP_AUTHORIZATION=self.auth,
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["files"]) == 10

        response = self.client.patch(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {"files": []},
            HTTP_AUTHORIZATION=self.auth,
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["files"]) == 0

    def test_album_delete(self):
        """Test deleting an album."""
        self.test_album_create_with_files()
        response = self.client.delete(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
        )
        assert response.status_code == 403
        response = self.client.delete(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            HTTP_AUTHORIZATION=f"Bearer {self.user2.tokeninfo['access_token']}",
        )
        assert response.status_code == 403
        response = self.client.delete(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            HTTP_AUTHORIZATION=self.auth,
        )
        assert response.status_code == 204

    def test_album_get(self):
        """Get album metadata from the API."""
        self.test_album_create_with_files()
        response = self.client.get(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            HTTP_AUTHORIZATION=self.auth,
        )
        assert response.status_code == 200

    def test_album_list(self):
        """Get album list from the API."""
        for i in range(10):
            self.test_album_create_with_files(title=f"album{i}")
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            HTTP_AUTHORIZATION=self.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 10

        # test the file filter with files in different albums
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"files": [self.files[0], response.json()[1]["files"][0]]},
            HTTP_AUTHORIZATION=self.auth,
        )
        assert response.status_code == 200
        print(response.json())
        assert len(response.json()) == 0
        # test with files in the same album
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"files": [self.files[0], self.files[1]]},
            HTTP_AUTHORIZATION=self.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

        # test search
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"search": "album4"},
            HTTP_AUTHORIZATION=self.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

        # test sorting
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"sorting": "created_desc"},
            HTTP_AUTHORIZATION=self.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 10
        assert response.json()[0]["title"] == "album9"

        # test offset
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"sorting": "title_asc", "offset": 5},
            HTTP_AUTHORIZATION=self.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 5
        assert response.json()[0]["title"] == "album5"
