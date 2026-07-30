"""Tests for the file HTML views."""

from bs4 import BeautifulSoup
from django.urls import reverse

from utils.tests import BmaTestBase


class TestFileViews(BmaTestBase):
    """Unit tests for regular django views."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Add test data."""
        # first add users and other basics
        super().setUpTestData()
        # upload some files
        cls.upload_initial_test_files()

    ######### FILE LIST ######################################
    def assert_file_list_rows(self, expected_rows: int, fail_message: str = "", qs: str = "") -> None:
        """Make a file_list call and count the number of table rows (files)."""
        url = reverse("files:file_list_table")
        response = self.client.get(url + qs)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        if not fail_message:
            fail_message = f"did not get {expected_rows} from file_list view with filter: '{qs}'"
        self.assertEqual(len(rows), expected_rows, fail_message)

    def test_file_list_view_perms(self) -> None:
        """Test the permissions aspects of the file list view."""
        # the superuser can see all 24 files
        self.client.login(username="superuser", password="secret")
        self.assert_file_list_rows(24)

        # anonymous can see 0 files
        self.client.logout()
        self.assert_file_list_rows(0)

        # each creator can see their own files
        for user, count in [("creator2", 15), ("creator3", 9)]:
            self.client.login(username=user, password="secret")
            self.assert_file_list_rows(count, f"creator {user} can not see {count} files")

        # each moderator can see all 25 files
        for m in ["moderator4", "moderator5"]:
            self.client.login(username=m, password="secret")
            self.assert_file_list_rows(24, f"moderator {m} can not see 24 files")

        # each curator can see 0 files since none are approved yet
        for m in ["curator6", "curator7"]:
            self.client.login(username=m, password="secret")
            self.assert_file_list_rows(0, f"curator {m} can not see 0 files")

        # change it up a bit
        self.change_initial_test_files()

        # each curator can now see 3 files
        for m in ["curator6", "curator7"]:
            self.client.login(username=m, password="secret")
            self.assert_file_list_rows(3, f"curator {m} can not see 3 files")

        # anonymous can now see 3 files
        self.client.logout()
        self.assert_file_list_rows(3)

    def test_file_list_view_attribution_filters(self) -> None:
        """Test the attribution filter of the file list view."""
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # test attribution and attribution contains
        self.assert_file_list_rows(24, qs="?attribution__icontains=foto")
        self.assert_file_list_rows(0, qs="?attribution__icontains=notthere")
        self.assert_file_list_rows(1, qs="?attribution__icontains=fotofonzy")

    def test_file_list_view_license_filters(self) -> None:
        """Test the license filter of the file list view."""
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # test license filter
        self.assert_file_list_rows(1, qs="?licenses=CC_BY_4_0")
        self.assert_file_list_rows(1, qs="?licenses=CC_BY_SA_4_0")
        self.assert_file_list_rows(2, qs="?licenses=CC_BY_4_0&licenses=CC_BY_SA_4_0")

    def test_file_list_view_file_size_filters(self) -> None:
        """Test the size filter of the file list view."""
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # test file size filter
        self.assert_file_list_rows(24, qs="?file_size=8424")
        self.assert_file_list_rows(24, qs="?file_size__lt=100000")
        self.assert_file_list_rows(0, qs="?file_size__lt=100")
        self.assert_file_list_rows(0, qs="?file_size__gt=100000")
        self.assert_file_list_rows(24, qs="?file_size__gt=100")

    def test_file_list_view_album_filters(self) -> None:
        """Test the album filter of the file list view."""
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # test album filter
        self.assert_file_list_rows(11, qs=f"?in_all_albums={self.creator2_album}")
        self.assert_file_list_rows(11, qs=f"?in_all_albums={self.creator2_album}&in_all_albums={self.allfiles_album}")
        self.assert_file_list_rows(11, qs=f"?in_any_albums={self.creator2_album}")
        self.assert_file_list_rows(20, qs=f"?in_any_albums={self.creator2_album}&in_any_albums={self.creator3_album}")
        self.assert_file_list_rows(13, qs=f"?not_in_albums={self.creator2_album}")

    def test_file_list_view_uploaders_filters(self) -> None:
        """Test the uploaders filter of the file list view."""
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # test uploaders filter
        self.assert_file_list_rows(15, qs="?uploaders=creator2")
        self.assert_file_list_rows(24, qs="?uploaders=creator2&uploaders=creator3")

    def test_file_list_view_bool_filters(self) -> None:
        """Test the bool filters (approved, published, deleted) of the file list view."""
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # test approved filter
        self.assert_file_list_rows(0, qs="?approved=true")
        self.assert_file_list_rows(24, qs="?approved=false")

        # test published filter
        self.assert_file_list_rows(0, qs="?published=true")
        self.assert_file_list_rows(24, qs="?published=false")

        # test deleted filter
        self.assert_file_list_rows(0, qs="?deleted=true")
        self.assert_file_list_rows(24, qs="?deleted=false")

        # change it up
        self.change_initial_test_files()
        self.client.login(username="moderator4", password="secret")

        # test approved filter
        self.assert_file_list_rows(5, qs="?approved=true")
        self.assert_file_list_rows(19, qs="?approved=false")

        # test published filter
        self.assert_file_list_rows(5, qs="?published=true")
        self.assert_file_list_rows(19, qs="?published=false")

        # test deleted filter
        self.assert_file_list_rows(5, qs="?deleted=true")
        self.assert_file_list_rows(19, qs="?deleted=false")

    def test_file_list_view_tagged_filters(self) -> None:
        """Test the tagged filter of the file list view."""
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # test tagged_all filter
        self.assert_file_list_rows(0, qs="?tagged_all=foo&tagged_all=bar")
        self.assert_file_list_rows(11, qs="?tagged_all=foo")

        # test tagged_any filter
        self.assert_file_list_rows(20, qs="?tagged_any=foo&tagged_any=bar")
        self.assert_file_list_rows(9, qs="?tagged_any=bar")

        # test not_tagged filter
        self.assert_file_list_rows(22, qs="?not_tagged=tag1")

    def test_file_list_view_taggers_filters(self) -> None:
        """Test the taggers filter of the file list view."""
        self.change_initial_test_files()
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # user should be able to see 24 files now
        self.assert_file_list_rows(24)

        # test taggers_all filter
        self.assert_file_list_rows(0, qs="?taggers_all=creator2&taggers_all=creator3")
        self.assert_file_list_rows(11, qs="?taggers_all=creator2")
        self.assert_file_list_rows(3, qs="?taggers_all=creator2&taggers_all=curator6")

        # test taggers_any filter
        self.assert_file_list_rows(12, qs="?taggers_any=creator3&taggers_any=curator6")
        self.assert_file_list_rows(3, qs="?taggers_any=curator6")

        # test not_taggers filter
        self.assert_file_list_rows(21, qs="?not_taggers=curator6")

    def test_file_list_view_tagged_emoji(self) -> None:
        """Make sure searching for a slug with an emoji works."""
        self.client.login(username="moderator4", password="secret")
        self.change_initial_test_files()
        self.assert_file_list_rows(3, qs="?tagged_all=more-fire")

    ######### FILE LIST SORTING ##################################
    def test_file_list_view_default_sort(self) -> None:
        """Test that the default sort is newest first (descending created_at)."""
        self.client.login(username="moderator4", password="secret")
        url = reverse("files:file_list_table")
        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        # should get all 24 files
        self.assertEqual(len(rows), 24)

    def test_file_list_view_sort_newest_first(self) -> None:
        """Test sorting by newest first."""
        self.client.login(username="moderator4", password="secret")
        self.assert_file_list_rows(24, qs="?sort=-created_at")

    def test_file_list_view_sort_oldest_first(self) -> None:
        """Test sorting by oldest first."""
        self.client.login(username="moderator4", password="secret")
        self.assert_file_list_rows(24, qs="?sort=created_at")

    def test_file_list_view_sort_title(self) -> None:
        """Test sorting by title."""
        self.client.login(username="moderator4", password="secret")
        self.assert_file_list_rows(24, qs="?sort=title")
        self.assert_file_list_rows(24, qs="?sort=-title")

    def test_file_list_view_sort_hitcount(self) -> None:
        """Test sorting by popularity (hitcount)."""
        self.client.login(username="moderator4", password="secret")
        self.assert_file_list_rows(24, qs="?sort=-hitcount")
        self.assert_file_list_rows(24, qs="?sort=hitcount")

    ######### FILE MULTIPLE ACTION ######################################

    def test_file_multiple_actions_view(self) -> None:
        """Make sure the multiple file actions view works as intended."""
        # make sure we have some approved and published files so the curators can work
        self.approve_files_api(files=self.files, user=self.superuser)
        self.publish_files_api(files=self.files, user=self.superuser)

        url = reverse("files:file_multiple_action")
        self.client.login(username="curator6", password="secret")

        # create a new album with the 3 published files
        data = {"action": "create_album", "selection": self.files[2:5], "fromurl": "/"}
        response = self.client.post(url, data, follow=True)
        assert "Showing 3 files" in response.content.decode()

        # make sure the remove_from_album form renders correctly
        self.client.login(username="creator2", password="secret")
        data = {"action": "remove_from_album", "selection": [self.files[3]], "fromurl": "/"}
        response = self.client.post(url, data, follow=True)
        assert len(response.redirect_chain) == 0
        content = response.content.decode()
        assert "Remove Files from Album" in content
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div#id_album > div.form-check")
        # expect 1 albums in the form (only 1 albums have this file and perms for curator6)
        assert len(rows) == 1, "Did not see 1 albums in the remove form as expected"

        # remove files from album
        data = {"album": self.albums[0], "files_to_remove": [self.files[3]], "fromurl": "/"}
        response = self.client.post(reverse("albums:remove_files_from_album"), data, follow=True)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Removed 1 of 1 file(s)" in content

        # make sure the add_to_album form renders correctly
        data = {"action": "add_to_album", "selection": [self.files[3]], "fromurl": "/"}
        response = self.client.post(url, data, follow=True)
        assert len(response.redirect_chain) == 0
        content = response.content.decode()
        assert "Add Files to Album" in content
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div#id_album > div.form-check")
        # there should only be 1 album because the other albums with perm already has the file
        assert len(rows) == 1, "Did not see 1 albums in the add form as expected"

        # actually post the add_to_album form (add to existing album)
        data = {"album": self.albums[0], "files_to_add": [self.files[3]], "fromurl": "/"}
        response = self.client.post(reverse("albums:add_files_to_album"), data, follow=True)
        content = response.content.decode()
        assert "Added 1 of 1 file(s)" in content

    ######### FILE DETAIL ####################################

    def test_file_detail_view(self) -> None:
        """Test the file detail view."""
        self.client.login(username="creator2", password="secret")
        response = self.client.get(reverse("files:file_show", kwargs={"file_uuid": self.files[0]}))
        content = response.content.decode()
        assert "Image creator2 file 0" in content

    ######### FILE TAG LIST ####################################

    def test_file_tag_list_view(self) -> None:
        """Test the file tag list view."""
        self.client.login(username="creator2", password="secret")
        response = self.client.get(reverse("files:file_tags", kwargs={"file_uuid": self.files[0]}))
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        assert len(rows) == 2, "did not get 2 rows in file tag list view"

    ######### FILE JOB LIST ####################################

    def test_file_job_list_view(self) -> None:
        """Test the file job list view."""
        self.client.login(username="creator2", password="secret")
        response = self.client.get(reverse("files:file_jobs", kwargs={"file_uuid": self.files[0]}))
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        assert len(rows) == 25, "did not get 25 rows in file job list view"

    ######### FILE TAG CREATE ####################################

    def test_file_tag_create_view(self) -> None:
        """Make sure the file tag create view works as intended."""
        url = reverse("files:file_tag_create", kwargs={"file_uuid": self.files[0]})
        self.client.login(username="creator2", password="secret")
        # test GET
        response = self.client.get(url)
        content = response.content.decode()
        assert "Add Tags to Image" in content

        # add new tags
        data = {"tags": "testtag1 testtag2"}
        response = self.client.post(url, data, follow=True)
        content = response.content.decode()
        assert "Tag(s) added." in content, "Tags added message not found"
        soup = BeautifulSoup(content, "html.parser")
        tag_card = soup.select_one("#tag-card")
        tags = tag_card.select("form")
        assert len(tags) == 4, "did not find 4 tags after adding 2"

    ######### FILE TAG DETAIL ####################################

    def test_file_tag_detail_view(self) -> None:
        """Make sure the file tag detail view works."""
        url = reverse("files:file_tag_taggings_list", kwargs={"file_uuid": self.files[0], "tag_slug": "tag0"})
        self.client.login(username="creator2", password="secret")
        # test GET
        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        # only 1 tagging with this tag
        assert len(rows) == 1

    ######### FILE TAG DELETE ####################################

    def test_file_tag_delete_view(self) -> None:
        """Make sure the file tag delete view works as intended."""
        url = reverse("files:file_tag_delete", kwargs={"file_uuid": self.files[0], "tag_slug": "tag0"})
        self.client.login(username="creator2", password="secret")
        response = self.client.post(url, follow=True)
        content = response.content.decode()
        assert "Tag deleted." in content, "Tags deleted message not found"
        soup = BeautifulSoup(content, "html.parser")
        tag_card = soup.select_one("#tag-card")
        tags = tag_card.select("form")
        assert len(tags) == 1, "did not find 1 tags after removing 1"

    ######### FILE CROP CENTER ###################################

    def test_file_crop_center_view(self) -> None:
        """Make sure the file crop center view works as intended."""
        url = reverse("files:file_crop_center", kwargs={"file_uuid": self.files[0]})
        self.client.login(username="creator2", password="secret")
        data = {"center_x": 20, "center_y": 20}
        response = self.client.post(url, data, follow=True)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "Image crop center saved." in str(s)]
        self.assertEqual(len(matches), 1, "image crop center did not save.")
