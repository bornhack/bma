"""Tests for the files API, admin and HTML views."""

from pathlib import Path

from bs4 import BeautifulSoup
from django.conf import settings
from django.urls import reverse

from utils.tests import BmaTestBase

from .models import BaseFile


class TestFilesApi(BmaTestBase):
    """Test for methods in the files API."""

    def test_api_auth_bearer_token(self) -> None:
        """Test getting a token, and that the authorized_tokens view works with token auth."""
        response = self.client.get("/o/authorized_tokens/", headers={"authorization": self.creator2.auth})
        assert response.status_code == 200
        assert "revoke" in response.content.decode("utf-8")

    def test_api_auth_get_refresh_token(self) -> None:
        """Test getting a refresh token."""
        response = self.client.post(
            "/o/token/",
            {
                "grant_type": "refresh_token",
                "client_id": self.creator2.webapp_oauth_client_id,
                "refresh_token": self.creator2.tokeninfo["refresh_token"],
            },
        )
        assert response.status_code == 200
        assert "refresh_token" in response.json()

    def test_api_auth_django_session(self) -> None:
        """Test getting authorised tokens."""
        self.client.force_login(self.creator2)
        response = self.client.get("/o/authorized_tokens/")
        assert response.status_code == 200
        assert "revoke" in response.content.decode("utf-8")

    def test_file_upload(self) -> None:
        """Test file upload cornercases."""
        data = self.file_upload(title="", return_full=True)
        assert data["title"] == data["original_filename"]
        self.file_upload(file_license="notalicense", expect_status_code=422)

    def test_file_list(self) -> None:  # noqa: PLR0915
        """Test the file_list endpoint."""
        files = [self.file_upload(title=f"title{i}") for i in range(15)]
        [
            files.append(self.file_upload(title=f"title{i}", description="tag test", tags=["starttag", f"tag{i}"]))
            for i in range(15, 20)
        ]
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.creator2.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 20

        # test sorting
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": 5, "sorting": "title_asc"},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 5
        assert response.json()["bma_response"][0]["title"] == "title0"
        assert response.json()["bma_response"][1]["title"] == "title1"
        assert response.json()["bma_response"][2]["title"] == "title10"
        assert response.json()["bma_response"][4]["title"] == "title12"
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": 1, "sorting": "created_desc"},
            headers={"authorization": self.creator2.auth},
        )
        assert response.json()["bma_response"][0]["title"] == "title19"

        # test offset
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"offset": 5, "sorting": "created_asc"},
            headers={"authorization": self.creator2.auth},
        )
        assert response.json()["bma_response"][0]["title"] == "title5"
        assert response.json()["bma_response"][4]["title"] == "title9"

        # test uploader filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"uploaders": [self.creator2.uuid, self.user0.uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 20
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"uploaders": [self.user0.uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 0

        # test search
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"search": "title7"}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 1
        assert response.json()["bma_response"][0]["title"] == "title7"

        # create an album with some files
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": "album title here",
                "files": files[3:6],
            },
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 201
        self.album_uuid = response.json()["bma_response"]["uuid"]

        # test album filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 3

        # create another empty album
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": "another album title here",
            },
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 201
        uuid = response.json()["bma_response"]["uuid"]

        # test filtering for multiple albums
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid, uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 3

        # update album by removing a file
        response = self.client.patch(
            reverse("api-v1-json:album_update", kwargs={"album_uuid": self.album_uuid}),
            {
                "files": files[4:6],
            },
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure only 2 files are returned now
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 2

        # test file size filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size": 9478}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 20

        # test file size_lt filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_lt": 10000}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 20
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_lt": 1000}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 0

        # test file size_gt filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_gt": 10000}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 0
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_gt": 1000}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 20

        # test file type filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"filetypes": ["image"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 20
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"filetypes": ["audio", "video", "document"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 0

        # test file license filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_ZERO_1_0"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 20
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_BY_4_0", "CC_BY_SA_4_0"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 0

        # tag a couple of files using the api
        for i in range(5):
            tags = ["foo", f"tag{i}"]
            response = self.client.post(
                reverse("api-v1-json:file_tag", kwargs={"file_uuid": files[i]}),
                data={
                    "tags": tags,
                },
                headers={"authorization": self.creator2.auth},
                content_type="application/json",
            )
            assert response.status_code == 201

        # tag a couple of more files using another user
        for i in range(2, 10):
            tags = ["bar", f"tag{i}"]
            response = self.client.post(
                reverse("api-v1-json:file_tag", kwargs={"file_uuid": files[i]}),
                data={
                    "tags": tags,
                },
                headers={"authorization": self.curator6.auth},
                content_type="application/json",
            )
            assert response.status_code == 201

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_ZERO_1_0"]},
            headers={"authorization": self.creator2.auth},
        )

        # test tag filter
        for i in range(10):
            if i <= 2:
                tags = ["foo", f"tag{i}"]
            elif i < 5:
                tags = ["foo", "bar", f"tag{i}"]
            elif i >= 5:
                tags = ["bar", f"tag{i}"]
            response = self.client.get(
                reverse("api-v1-json:file_list"),
                data={"tags": tags},
                headers={"authorization": self.creator2.auth},
            )
            assert response.status_code == 200
            assert len(response.json()["bma_response"]) == 1

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"tags": ["foo"]},
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 5

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"tags": ["foo", "bar"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 3

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"tags": ["foo", "bar", "tag3"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 1

        # test taggers filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"taggers": [self.creator2.uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 10

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"taggers": [self.creator2.uuid, self.curator6.uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 3

        # untag some files and test filtering
        for i in range(4, 7):
            tags = [f"tag{i}"]
            # all 3 files are tagged with tagN, file4 has weight 2
            response = self.client.get(
                reverse("api-v1-json:file_list"),
                data={"tags": tags},
                headers={"authorization": self.creator2.auth},
            )
            assert len(response.json()["bma_response"]) == 1
            for tag in response.json()["bma_response"][0]["tags"]:
                if tag["name"] == tags[0]:
                    assert tag["weight"] == 2 if i == 4 else 1

            # remove curator6 tagN tagging from file
            response = self.client.post(
                reverse("api-v1-json:file_untag", kwargs={"file_uuid": files[i]}),
                data={
                    "tags": tags,
                },
                headers={"authorization": self.curator6.auth},
                content_type="application/json",
            )
            assert response.status_code == 200

            # only file4 is still tagged with tagN, weight for tagN for file4 is now one
            response = self.client.get(
                reverse("api-v1-json:file_list"),
                data={"tags": tags},
                headers={"authorization": self.creator2.auth},
            )
            if i == 4:
                assert len(response.json()["bma_response"]) == 1
                for tag in response.json()["bma_response"][0]["tags"]:
                    if tag["name"] == tags[0]:
                        assert tag["weight"] == 1
            else:
                assert len(response.json()["bma_response"]) == 0

        # curator6 still tagged 8 different files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"taggers": [self.curator6.uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 8

        # remove curator6 bar tagging from file4
        response = self.client.post(
            reverse("api-v1-json:file_untag", kwargs={"file_uuid": files[4]}),
            data={
                "tags": ["bar"],
            },
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 200

        # curator6 now only tagged 7 files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"taggers": [self.curator6.uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 7

        # bar tag is now ony only applied to 7 files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"tags": ["bar"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 7

    def test_file_list_permissions(self) -> None:
        """Test various permissions stuff for the file_list endpoint."""
        files = [self.file_upload(title=f"title{i}") for i in range(15)]

        # no files should be visible
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user0.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

        # the superuser can see all files
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.superuser.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 15

        # attempt to publish a file before approval
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200

        # attempt to unpublish a file before approval
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200

        # approve the file without permission
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 403

        # approve the file, check mode
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.superuser.auth},
        )
        assert response.status_code == 202

        # really approve the file
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.superuser.auth},
        )
        assert response.status_code == 200

        # now list unpublished files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"published": False},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 15

        # publish a file, check mode
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 202

        # publish the file
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200

        # make sure someone else can see it
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user0.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 1

        # make sure anonymous can see it
        response = self.client.get(
            reverse("api-v1-json:file_list"),
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 1

        # unpublish the file without permission
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.user0.auth},
        )
        assert response.status_code == 403

        # unpublish the file, check mode
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 202

        # unpublish the file
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200

        # make sure it is not visible anymore
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user0.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

        # make sure it is not visible anymore to anonymous
        response = self.client.get(
            reverse("api-v1-json:file_list"),
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

    def test_metadata_get(self) -> None:
        """Get file metadata from the API."""
        self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200
        assert "uuid" in response.json()["bma_response"]
        assert response.json()["bma_response"]["uuid"] == self.file_uuid

    def test_file_download(self) -> None:
        """Test downloading a file after uploading it."""
        self.file_upload()
        metadata = self.client.get(
            reverse("api-v1-json:file_list"), headers={"authorization": self.creator2.auth}
        ).json()["bma_response"][0]
        url = metadata["links"]["downloads"]["original"]
        # try download of unpublished file without auth
        response = self.client.get(url)
        assert response.status_code == 403
        # try again with auth
        self.client.force_login(self.creator2)
        response = self.client.get(url)
        assert response.status_code == 200
        assert response["content-type"] == "image/png"
        with (settings.BASE_DIR / "static_src/images/logo_wide_black_500_RGB.png").open("rb") as f:
            assert f.read() == response.getvalue()

    def test_file_metadata_update(self) -> None:
        """Replace and then update file metadata."""
        self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200
        original_metadata = response.json()["bma_response"]
        updates = {
            "title": "some title",
            "description": "some description",
            "license": "CC_ZERO_1_0",
            "attribution": "some attribution",
        }

        # update with no auth
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            content_type="application/json",
        )
        assert response.status_code == 403

        # update with wrong user
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            headers={"authorization": f"Bearer {self.user0.tokeninfo['access_token']}"},
            content_type="application/json",
        )
        assert response.status_code == 403

        # update the file, check mode
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}) + "?check=true",
            updates,
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 202

        # replace the file metadata
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 200
        original_metadata.update(updates)
        for k, v in response.json()["bma_response"].items():
            # "updated" will have changed of course,
            if k == "updated":
                assert v != original_metadata[k]
            # and "source" was initially set but not specified in the PUT call,
            # so it should be blank now, so it should return the files detail url
            elif k == "source":
                assert v == original_metadata["links"]["html"]
            # everything else should be the same
            else:
                assert v == original_metadata[k]

        # update instead of replace, first with invalid source url
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"original_source": "outer space"},
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 422
        # then with a valid url
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"original_source": "https://example.com/foo.png"},
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure we updated only the source attribute with the PATCH request
        assert response.json()["bma_response"]["source"] == "https://example.com/foo.png"
        assert response.json()["bma_response"]["attribution"] == "some attribution"

    def test_post_csrf(self) -> None:
        """Make sure CSRF is enforced on API views when using django session cookie auth."""
        self.file_upload()
        self.client.force_login(self.user0)
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"attribution": "csrfcheck"},
            content_type="application/json",
        )
        # this should fail because we did not add CSRF..
        assert response.status_code == 403

    def test_file_softdelete(self) -> None:
        """Test softdeleting a file."""
        self.file_upload()
        # test with no auth
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
        )
        assert response.status_code == 403

        # test with wrong auth
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": f"Bearer {self.user0.tokeninfo['access_token']}"},
        )
        assert response.status_code == 403

        # delete file, check mode
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}) + "?check=true",
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 202

        # delete file
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 204

    def test_metadata_get_404(self) -> None:
        """Get file metadata get with wrong uuid returns 404."""
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": "a35ce7c9-f814-46ca-8c4e-87b992e15819"},
            ),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 404

    def test_metadata_get_validationerror(self) -> None:
        """Get file metadata get with something that is not a uuid."""
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": "notuuid"}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 422

    def test_metadata_get_403(self) -> None:
        """Get file metadata get with wrong uuid returns 404."""
        self.file_upload()
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            headers={"authorization": f"Bearer {self.user0.tokeninfo['access_token']}"},
        )
        assert response.status_code == 403
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
        )
        assert response.status_code == 403

    def test_approve_files(self) -> None:
        """Approve multiple files."""
        for _ in range(10):
            self.file_upload()
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.creator2.auth})
        files = [f["uuid"] for f in response.json()["bma_response"]]
        # first try with no permissions
        response = self.client.patch(
            reverse("api-v1-json:approve_files"),
            {"files": files[0:5]},
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then check mode
        response = self.client.patch(
            reverse("api-v1-json:approve_files") + "?check=true",
            {"files": files[0:5]},
            headers={"authorization": self.superuser.auth},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then with permission
        response = self.client.patch(
            reverse("api-v1-json:approve_files"),
            {"files": files[0:5]},
            headers={"authorization": self.superuser.auth},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure files are now approved
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"approved": True},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 5

    def test_file_missing_on_disk(self) -> None:
        """Test the case where a file has gone missing from disk for some reason."""
        self.file_upload()
        basefile = BaseFile.objects.get(uuid=self.file_uuid)
        Path(basefile.original.path).unlink()
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            headers={"authorization": self.creator2.auth},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["bma_response"]["size_bytes"], 0)

    def test_thumbnail_upload(self) -> None:
        """Test uploading a thumbnail for a file."""
        data = self.file_upload(return_full=True)
        assert not data["has_thumbnail"]


class TestFileAdmin(BmaTestBase):
    """Tests for the FileAdmin."""

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
        # upload some files
        self.files = [self.file_upload() for _ in range(10)]
        for _ in range(10):
            self.files.append(self.file_upload(uploader="creator3"))

        # the superuser can see all files
        url = reverse("file_admin:files_basefile_changelist")
        self.client.login(username="superuser", password="secret")
        response = self.client.get(url)
        self.assertInHTML(
            '<p class="paginator">20 files</p>', response.content.decode(), msg_prefix="superuser can not see 20 files"
        )

        # each creator can see 10 files
        for c in ["creator2", "creator3"]:
            self.client.login(username=c, password="secret")
            response = self.client.get(url)
            self.assertInHTML(
                '<p class="paginator">10 files</p>',
                response.content.decode(),
                msg_prefix=f"creator {c} can not see 10 files",
            )

        # each moderator can see all 20 files
        for m in ["moderator4", "moderator5"]:
            self.client.login(username=m, password="secret")
            response = self.client.get(url)
            self.assertInHTML(
                '<p class="paginator">20 files</p>',
                response.content.decode(),
                msg_prefix=f"moderator {m} can not see 20 files",
            )

        # make moderator4 approve 5 of the files owned by creator2
        data = {"action": "approve", "_selected_action": self.files[:5]}
        self.client.login(username="moderator4", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<p class="paginator">20 files</p>',
            response.content.decode(),
            msg_prefix=f"moderator {m} can not see 20 files",
        )

        # test filtering to see only approved files
        response = self.client.get(url + "?approved__exact=1")
        self.assertInHTML(
            '<p class="paginator">5 files</p>', response.content.decode(), msg_prefix="can not see 5 approved files"
        )

        # each creator can still see 10 files
        for c in ["creator2", "creator3"]:
            self.client.login(username=c, password="secret")
            response = self.client.get(url)
            self.assertInHTML(
                '<p class="paginator">10 files</p>',
                response.content.decode(),
                msg_prefix=f"creator {c} can not see 10 files",
            )

        # make creator2 publish the 5 approved files
        data = {"action": "publish", "_selected_action": self.files[:5]}
        self.client.login(username="creator2", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<p class="paginator">10 files</p>', response.content.decode(), msg_prefix="creator2 can not see 10 files"
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
            '<p class="paginator">10 files</p>', response.content.decode(), msg_prefix="creator2 can not see 10 files"
        )
        response = self.client.get(url + "?published__exact=0")
        self.assertInHTML(
            '<p class="paginator">10 files</p>',
            response.content.decode(),
            msg_prefix="creator2 can not see 10 unpublished files after unpublishing",
        )

        # make moderator4 unapprove 5 of the files owned by creator2
        data = {"action": "unapprove", "_selected_action": self.files[:5]}
        self.client.login(username="moderator4", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url + "?approved__exact=0")
        self.assertInHTML(
            '<p class="paginator">20 files</p>',
            response.content.decode(),
            msg_prefix=f"moderator {m} can not see 20 files pending moderation",
        )

        # make creator2 softdelete the 5 approved and pubhlished files
        data = {"action": "softdelete", "_selected_action": self.files[:5]}
        self.client.login(username="creator2", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<p class="paginator">10 files</p>', response.content.decode(), msg_prefix="creator2 can not see 10 files"
        )
        response = self.client.get(url + "?deleted__exact=1")
        self.assertInHTML(
            '<p class="paginator">5 files</p>', response.content.decode(), msg_prefix="can not see 5 deleted files"
        )


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
        url = reverse("files:file_list")
        response = self.client.get(url + qs)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        if not fail_message:
            fail_message = f"did not get {expected_rows} from file_list view with filter: '{qs}'"
        self.assertEqual(len(rows), expected_rows, fail_message)
        return content

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
        self.assert_file_list_rows(1, qs="?attribution=fotoflummer")

    def test_file_list_view_license_filters(self) -> None:
        """Test the license filter of the file list view."""
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # test license filter
        self.assert_file_list_rows(1, qs="?license=CC_BY_4_0")
        self.assert_file_list_rows(1, qs="?license=CC_BY_SA_4_0")

    def test_file_list_view_file_size_filters(self) -> None:
        """Test the size filter of the file list view."""
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        # test file size filter
        self.assert_file_list_rows(24, qs="?file_size=9478")
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
        # use moderator so all files are visible
        self.client.login(username="moderator4", password="secret")

        self.change_initial_test_files()

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

    ######### FILE MULTIPLE ACTION ######################################

    def test_file_multiple_actions_view(self) -> None:
        """Make sure the multiple file actions view works as intended."""
        # make sure we have some approved and published files so the curators can work
        self.change_initial_test_files()
        url = reverse("files:file_multiple_action")
        self.client.login(username="curator6", password="secret")

        # create a new album with the 3 published files
        data = {"action": "create_album", "selection": self.files[2:5], "fromurl": "/"}
        response = self.client.post(url, data, follow=True)
        assert "Showing 3 of 3 files in album" in response.content.decode()

        data = {"action": "add_to_album", "selection": self.files[5:10], "fromurl": "/"}
        response = self.client.post(url, data, follow=True)
        assert len(response.redirect_chain) == 0
        content = response.content.decode()
        assert "Add Files to Album" in content
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div#id_album > div.form-check")
        # there should only be 1 album because the other already has all these files
        assert len(rows) == 1, "Did not see 1 albums in the form as expected"

    ######### FILE DETAIL ####################################

    def test_file_detail_view(self) -> None:
        """Test the file detail view."""
        self.client.login(username="creator2", password="secret")
        response = self.client.get(reverse("files:file_detail", kwargs={"file_uuid": self.files[0]}))
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

    ######### FILE TAG CREATE ####################################

    def test_file_tag_create_view(self) -> None:
        """Make sure the file tag create view works as intended."""
        url = reverse("files:file_tag_create", kwargs={"file_uuid": self.files[0]})
        self.client.login(username="creator2", password="secret")
        # test GET
        response = self.client.get(url)
        content = response.content.decode()
        assert f"Add Tags to image {self.files[0]}" in content

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
