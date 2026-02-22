"""Tests for Album views."""

from bs4 import BeautifulSoup
from django.urls import reverse

from albums.models import AlbumMember
from utils.tests import BmaTestBase


class TestAlbumViews(BmaTestBase):
    """Unit tests for regular django Album views."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Add test data."""
        # first add users and other basics
        super().setUpTestData()
        # then create some albums
        cls.upload_initial_test_files()

    def test_album_list_view(self) -> None:
        """Test the basics of the album list view."""
        url = reverse("albums:album_list")
        self.client.login(username="creator2", password="secret")

        # test listing all albums, no filters
        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        self.assertEqual(len(rows), 3, "album list does not return 3 albums")

    def test_album_memberships(self) -> None:
        """Test album memberships."""
        membership = AlbumMember.objects.get(album_id=self.albums[0], basefile=self.files[0])  # type: ignore[misc]
        assert f"{self.files[0]} is in album {self.albums[0]}" in membership.__str__()
        url = reverse("albums:album_remove_files", kwargs={"album_uuid": self.albums[0]})
        # remove file from album with the wrong user
        self.client.login(username="curator6", password="secret")
        response = self.client.post(
            path=url,
            data={"album": self.albums[0], "files_to_remove": [self.files[0]]},
            follow=True,
        )
        assert response.status_code == 403
        # remove file from album with the correct user
        self.client.login(username="creator2", password="secret")
        response = self.client.post(
            path=url,
            data={"album": self.albums[0], "files_to_remove": [self.files[0]]},
            follow=True,
        )
        assert "Removed 1 of 1 file(s) from album" in response.content.decode()
        membership.refresh_from_db()
        assert f"{self.files[0]} was in album {self.albums[0]}" in membership.__str__()

    def test_album_detail(self) -> None:
        """Test the album detail view."""
        url = reverse("albums:album_detail_table", kwargs={"album_uuid": self.albums[0]})
        remove_url = reverse("albums:album_remove_files", kwargs={"album_uuid": self.albums[0]})
        add_url = reverse("albums:album_add_files", kwargs={"album_uuid": self.albums[0]})

        # try add and remove without perms
        self.client.login(username="curator6", password="secret")
        response = self.client.get(path=add_url)
        assert response.status_code == 403
        response = self.client.get(path=remove_url)
        assert response.status_code == 403

        # showing the album requires no special perms
        response = self.client.get(path=url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        # but no files will be visible
        assert len(rows) == 0, "did not see 0 files as curator6"

        # try removing a file as the wrong user
        response = self.client.post(
            path=remove_url,
            data={"album": self.albums[0], "files_to_remove": [self.files[0]]},
            follow=True,
        )
        assert response.status_code == 403

        # then try the detailview as the correct user
        self.client.login(username="creator2", password="secret")
        response = self.client.get(path=url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        # but no files will be visible
        assert len(rows) == 11, "did not see 11 files as creator2"

        # remove the file with invalid payload
        response = self.client.post(
            path=remove_url,
            data={"album": self.albums[0], "files_to_remove": [self.files[15]]},
            follow=True,
        )
        assert "There was a validation issue with the form" in response.content.decode()
        # also try invalid payload with a fromurl
        response = self.client.post(
            path=remove_url,
            data={"fromurl": "/", "album": self.albums[0], "files_to_remove": [self.files[15]]},
            follow=True,
        )
        self.assertRedirects(response, "/", status_code=302)
        # then with valid payload
        response = self.client.post(
            path=remove_url,
            data={"album": self.albums[0], "files_to_remove": [self.files[0]]},
            follow=True,
        )
        assert "Removed 1 of 1 file(s) from album" in response.content.decode()
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        # this is the grid view
        rows = soup.select("div.pswp-gallery > span > a.gallerya")
        assert len(rows) == 10, "did not see 10 files left in the album after removing a file"

        # try adding some files as the wrong user
        self.client.login(username="curator6", password="secret")
        response = self.client.post(
            path=add_url,
            data={"album": self.albums[0], "files_to_add": self.files[15:20]},
            follow=True,
        )
        assert response.status_code == 403
        # then as the correct user
        self.client.login(username="creator2", password="secret")
        # but invalid payload
        response = self.client.post(
            path=add_url,
            data={"album": self.albums[0], "files_to_add": self.files[5:10]},
            follow=True,
        )
        assert "There was a validation issue with the form" in response.content.decode()
        # also try invalid payload with a fromurl
        response = self.client.post(
            path=add_url,
            data={"fromurl": "/", "album": self.albums[0], "files_to_add": self.files[5:10]},
        )
        self.assertRedirects(response, "/", status_code=302)
        # then the correct payload
        response = self.client.post(
            path=add_url,
            data={"album": self.albums[0], "files_to_add": [self.files[0]]},
            follow=True,
        )
        assert "Added 1 of 1 file(s) to album" in response.content.decode()
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        # this is the grid view
        rows = soup.select("div.pswp-gallery > span > a.gallerya")
        assert len(rows) == 11

    def test_album_update(self) -> None:
        """Test the album update view."""
        url = reverse("albums:album_update", kwargs={"album_uuid": self.albums[0]})
        self.client.login(username="creator2", password="secret")
        response = self.client.post(
            path=url,
            data={"title": "newtitle"},
            follow=True,
        )
        assert "newtitle" in response.content.decode()
        assert "Album updated!" in response.content.decode()
