"""Tests for the file HTML views."""

from django.urls import reverse

from utils.tests import BmaTestBase


class TestFileAdmin(BmaTestBase):
    """Tests for the FileAdmin."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Add test data."""
        # first add users and other basics
        super().setUpTestData()
        # upload some files
        cls.upload_initial_test_files()

    def test_file_list_status_code(self) -> None:
        """Test the access controls for the list page in the FileAdmin."""
        url = reverse("file_admin:files_basefile_changelist")
        # try accessing the file_admin without a login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # try accessing the file_admin with a user without permissions for it
        self.client.login(username="user0", password="secret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # try accessing the file_admin with a user with is_creator=True
        self.client.login(username="creator2", password="secret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # try accessing the file_admin with a user with is_moderator=True
        self.client.login(username="moderator4", password="secret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # try accessing the file_admin with a user with is_curator=True
        self.client.login(username="curator6", password="secret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_file_list(self) -> None:
        """Test the file list page in the FileAdmin."""
        # the superuser can see all files
        url = reverse("file_admin:files_basefile_changelist")
        self.client.login(username="superuser", password="secret")
        response = self.client.get(url)
        self.assertInHTML(
            '<p class="paginator">24 files</p>', response.content.decode(), msg_prefix="superuser can not see 24 files"
        )

        # each creator can see their own files
        for u, c in [("creator2", 15), ("creator3", 9)]:
            self.client.login(username=u, password="secret")
            response = self.client.get(url)
            self.assertInHTML(
                f'<p class="paginator">{c} files</p>',
                response.content.decode(),
                msg_prefix=f"creator {u} can not see {c} files",
            )

        # each moderator can see all 24 files
        for m in ["moderator4", "moderator5"]:
            self.client.login(username=m, password="secret")
            response = self.client.get(url)
            self.assertInHTML(
                '<p class="paginator">24 files</p>',
                response.content.decode(),
                msg_prefix=f"moderator {m} can not see 24 files",
            )

        # make moderator4 approve 5 of the files owned by creator2
        data = {"action": "approve", "_selected_action": self.files[:5]}
        self.client.login(username="moderator4", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<p class="paginator">24 files</p>',
            response.content.decode(),
            msg_prefix=f"moderator {m} can not see 24 files",
        )

        # test filtering to see only approved files
        response = self.client.get(url + "?approved__exact=1")
        self.assertInHTML(
            '<p class="paginator">5 files</p>', response.content.decode(), msg_prefix="can not see 5 approved files"
        )

        # each creator can still see their own files
        for u, c in [("creator2", 15), ("creator3", 9)]:
            self.client.login(username=u, password="secret")
            response = self.client.get(url)
            self.assertInHTML(
                f'<p class="paginator">{c} files</p>',
                response.content.decode(),
                msg_prefix=f"creator {u} can not see {c} files",
            )

        # make creator2 publish the 5 approved files
        data = {"action": "publish", "_selected_action": self.files[:5]}
        self.client.login(username="creator2", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<p class="paginator">15 files</p>', response.content.decode(), msg_prefix="creator2 can not see 14 files"
        )
        response = self.client.get(url + "?published__exact=1")
        self.assertInHTML(
            '<p class="paginator">5 files</p>', response.content.decode(), msg_prefix="can not see 5 published files"
        )

        # make creator2 unpublish the 5 approved files
        data = {"action": "unpublish", "_selected_action": self.files[:5]}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            "5 files selected to be unpublished, "
            "out of those 5 files had needed permission, "
            "and out of those 5 files were successfully unpublished",
            response.content.decode(),
            msg_prefix="unpublished message not found",
        )
        self.assertInHTML(
            '<p class="paginator">15 files</p>', response.content.decode(), msg_prefix="creator2 can not see 15 files"
        )
        response = self.client.get(url + "?published__exact=0")
        self.assertInHTML(
            '<p class="paginator">15 files</p>',
            response.content.decode(),
            msg_prefix="creator2 can not see 15 unpublished files after unpublishing",
        )

        # make moderator4 unapprove 5 of the files owned by creator2
        data = {"action": "unapprove", "_selected_action": self.files[:5]}
        self.client.login(username="moderator4", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url + "?approved__exact=0")
        self.assertInHTML(
            '<p class="paginator">24 files</p>',
            response.content.decode(),
            msg_prefix=f"moderator {m} can not see 24 files pending moderation",
        )

        # make creator2 softdelete the 5 approved and pubhlished files
        data = {"action": "softdelete", "_selected_action": self.files[:5]}
        self.client.login(username="creator2", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<p class="paginator">15 files</p>', response.content.decode(), msg_prefix="creator2 can not see 15 files"
        )
        response = self.client.get(url + "?deleted__exact=1")
        self.assertInHTML(
            '<p class="paginator">5 files</p>', response.content.decode(), msg_prefix="can not see 5 deleted files"
        )
