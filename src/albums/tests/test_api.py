"""Tests for the Album API."""

from django.urls import reverse

from utils.tests import BmaTestBase


class TestAlbumsApi(BmaTestBase):
    """Test for API endpoints in the albums API."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Add test data."""
        # first add users and other basics
        super().setUpTestData()
        # upload some files
        cls.upload_initial_test_files()

    def test_album_update_api(self) -> None:
        """First replace (PUT) then update (PATCH)."""
        # try PUT with the wrong user
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.albums[0]}),
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            headers={"authorization": self.tokens[self.user0]},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then PUT with the correct user, check mode
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.albums[0]}) + "?check=true",
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then PUT with the correct user
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.albums[0]}),
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]["files"]) == 2, "album does not have 2 files after PUT"
        assert response.json()["bma_response"]["title"] == "new title"
        assert response.json()["bma_response"]["description"] == "description here"

        # PATCH update the album with more files
        response = self.client.patch(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.albums[0]}),
            {"files": self.files},
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]["files"]) == 24

        # PATCH update to remove all files
        response = self.client.patch(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.albums[0]}),
            {"files": []},
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]["files"]) == 0

    def test_album_get_api(self) -> None:
        """Get album metadata from the API."""
        response = self.client.get(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.albums[0]}),
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200

    def test_album_list_api(self) -> None:
        """Get album list from the API."""
        response = self.client.get(
            reverse("api-v1-json:album_list"), headers={"authorization": self.tokens[self.creator2]}
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 3, "Did not get 3 albums"

        # make sure albums are sorted as expected
        latest = None
        for album in response.json()["bma_response"]:
            if latest:
                assert latest["created_at"] < album["created_at"], f"Albums are sorted wrong! {latest} > {album}"
            latest = album

        # test the file filter with files in different albums
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"files": [self.files[0], self.files[15]]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200
        assert (
            len(response.json()["bma_response"]) == 1
        ), "Did not get 1 albums when checking with files in two different albums"

        # test with files in the same album
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"files": [self.files[0], self.files[1]]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200
        assert (
            len(response.json()["bma_response"]) == 2
        ), "Did not get 2 albums when testing with files in the same album"

        # test search
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"search": "creator2"},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 1, "Did not get 1 album when searching"

        # test sorting
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"sorting": "created_at_desc"},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 3
        assert response.json()["bma_response"][0]["title"] == "all files", "Did not see the expected sort order"

        # test offset
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"sorting": "title_asc", "offset": "2"},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 1
        assert response.json()["bma_response"][0]["title"] == "creator3 first 9", "Did not get the expected offset"

    def test_album_create_validation_error(self) -> None:
        """Create an album with invalid data."""
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": "",
                "description": "",
                "files": [],
            },
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 422
