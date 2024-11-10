"""Tests for the Album API."""

from bs4 import BeautifulSoup
from django.urls import reverse

from utils.tests import BmaTestBase


class TestAlbumsApi(BmaTestBase):
    """Test for API endpoints in the albums API."""

    def test_album_create_api(
        self,
        title: str = "album title here",
        description: str = "album description here",
        files: list[str] | None = None,
    ) -> None:
        """Test creating an album."""
        self.album_uuid = self.album_create(title=title, description=description, files=files)

    def test_album_create_api_with_files(
        self,
        title: str = "album title here",
        description: str = "album description here",
    ) -> None:
        """Test creating an album with files."""
        self.files = []
        for _ in range(10):
            self.files.append(self.file_upload())
        self.album_uuid = self.album_create(title=title, description=description, files=self.files)

    def test_album_update_api(self) -> None:
        """First replace (PUT) then update (PATCH)."""
        self.test_album_create_api_with_files()

        # try PUT with the wrong user
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            headers={"authorization": self.user0.auth},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then PUT with the correct user, check mode
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}) + "?check=true",
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then PUT with the correct user
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]["files"]) == 2, "album does not have 2 files after PUT"
        assert response.json()["bma_response"]["title"] == "new title"
        assert response.json()["bma_response"]["description"] == "description here"

        # PATCH update the album with more files
        response = self.client.patch(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {"files": self.files},
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]["files"]) == 10

        # PATCH update to remove all files
        response = self.client.patch(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {"files": []},
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]["files"]) == 0

    def test_album_get_api(self) -> None:
        """Get album metadata from the API."""
        self.test_album_create_api_with_files()
        response = self.client.get(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200

    def test_album_list_api(self) -> None:
        """Get album list from the API."""
        for i in range(10):
            self.test_album_create_api_with_files(title=f"album{i}")
        response = self.client.get(reverse("api-v1-json:album_list"), headers={"authorization": self.curator6.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 10, "Did not get 10 albums"

        # test the file filter with files in different albums
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"files": [self.files[0], response.json()["bma_response"][1]["files"][0]]},
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200
        assert (
            len(response.json()["bma_response"]) == 0
        ), "Did not get 0 albums when checking with files in two different albums"

        # test with files in the same album
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"files": [self.files[0], self.files[1]]},
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200
        assert (
            len(response.json()["bma_response"]) == 1
        ), "Did not get 1 album when testing with files in the same album"

        # test search
        response = self.client.get(
            reverse("api-v1-json:album_list"), data={"search": "album4"}, headers={"authorization": self.curator6.auth}
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 1, "Did not get 1 album when searching"

        # test sorting
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"sorting": "created_desc"},
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 10
        assert response.json()["bma_response"][0]["title"] == "album9", "Did not see the expected sort order"

        # test offset
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"sorting": "title_asc", "offset": 5},
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 5
        assert response.json()["bma_response"][0]["title"] == "album5", "Did not get the expected offset"


class TestAlbumViews(BmaTestBase):
    """Unit tests for regular django Album views."""

    def create_albums(self) -> None:
        """Create som albums for testing."""
        # upload some files as creator2
        self.files = []
        for _ in range(10):
            self.files.append(self.file_upload())
        # add them to an album created by creator6
        self.album_uuid = self.album_create(title="creator2 files", files=self.files)
        # upload some files as creator3
        for _ in range(10):
            self.files.append(self.file_upload(uploader="creator3"))
        self.album_create(title="creator3 files", files=self.files[10:], creator="curator7")

    def test_album_list_view(self) -> None:
        """Test the basics of the album list view."""
        url = reverse("albums:album_list")
        self.create_albums()
        self.client.login(username="creator2", password="secret")

        # test listing both albums, no filters
        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        self.assertEqual(len(rows), 2, "album list does not return 2 albums")

        # test filtering by files to show albums containing a single file
        url += f"?files={self.files[0]}"
        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        self.assertEqual(len(rows), 1, "filtering by files does not return 1 album")
