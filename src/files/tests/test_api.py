"""Tests for the files API."""

from pathlib import Path

from django.conf import settings
from django.urls import reverse

from files.models import BaseFile
from utils.tests import BmaTestBase


class TestFilesApi(BmaTestBase):
    """Test for methods in the files API."""

    def test_api_auth_bearer_token(self) -> None:
        """Test getting a token, and that the authorized_tokens view works with token auth."""
        response = self.client.get("/o/authorized_tokens/", headers={"authorization": self.tokens[self.creator2]})
        assert response.status_code == 200
        assert "revoke" in response.content.decode("utf-8")

    def test_api_auth_get_refresh_token(self) -> None:
        """Test getting a refresh token."""
        response = self.client.post(
            "/o/token/",
            {
                "grant_type": "refresh_token",
                "client_id": self.creator2.webapp_oauth_client_id,
                "refresh_token": self.tokeninfos[self.creator2]["refresh_token"],
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
        self.file_upload(file_license="notalicense", expect_status_code=422)
        self.file_upload(uploader="moderator4", expect_status_code=403)
        self.file_upload(mimetype="application/pdf", width=0)
        self.file_upload(mimetype="video/mp4", width=0)
        self.file_upload(mimetype="audio/mpeg", width=0)
        self.file_upload(mimetype="foo/bar", expect_status_code=422)
        self.file_upload(title="")
        self.file_upload(file_license="notalicense", expect_status_code=422)
        self.file_upload(tags=["foo", "bar"])
        self.file_upload(thumbnail=True)

    def test_file_list(self) -> None:
        """Test the file_list endpoint."""
        files = [self.file_upload(title=f"title{i}") for i in range(15)]
        files = files + [
            self.file_upload(title=f"title{i}", description="tag test", tags=["starttag", f"tag{i}"])
            for i in range(15, 20)
        ]
        response = self.client.get(
            reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.creator2]}
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 20

        # test sorting
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": "5", "sorting": "title_asc"},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 5
        assert response.json()["bma_response"][0]["title"] == "title0"
        assert response.json()["bma_response"][1]["title"] == "title1"
        assert response.json()["bma_response"][2]["title"] == "title10"
        assert response.json()["bma_response"][4]["title"] == "title12"
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": "1", "sorting": "created_at_desc"},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.json()["bma_response"][0]["title"] == "title19"

        # test offset
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"offset": "5", "sorting": "created_at_asc"},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.json()["bma_response"][0]["title"] == "title5"
        assert response.json()["bma_response"][4]["title"] == "title9"

        # test uploader filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"uploaders": [str(self.creator2.uuid), str(self.user0.uuid)]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 20
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"uploaders": [str(self.user0.uuid)]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

        # test search
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"search": "title7"},
            headers={"authorization": self.tokens[self.creator2]},
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
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 201
        self.album_uuid = response.json()["bma_response"]["uuid"]

        # test album filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 3

        # create another empty album
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": "another album title here",
            },
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 201
        uuid = response.json()["bma_response"]["uuid"]

        # test filtering for multiple albums
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid, uuid]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 3

        # update album by removing a file
        response = self.client.patch(
            reverse("api-v1-json:album_update", kwargs={"album_uuid": self.album_uuid}),
            {
                "files": files[4:6],
            },
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure only 2 files are returned now
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 2

        # test file size filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size": 8424}, headers={"authorization": self.tokens[self.creator2]}
        )
        assert len(response.json()["bma_response"]) == 20

        # test file size_lt filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"size_lt": 10000},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 20
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"size_lt": 1000},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

        # test file size_gt filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"size_gt": 10000},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"size_gt": 1000},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 20

        # test file type filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"filetypes": ["image"]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 20
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"filetypes": ["audio", "video", "document"]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

        # test file license filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_ZERO_1_0"]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 20
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_BY_4_0", "CC_BY_SA_4_0"]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

        # test published filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"published": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

        # publish files
        self.publish_files_api(files=files[0:10], user=self.creator2)

        # test published filter again
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"published": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 10

        # test approved filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"approved": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

        # approve files
        self.approve_files_api(files=files[0:10], user=self.superuser)

        # test approved filter again
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"approved": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 10

        # files are approved and published, tag a couple of files using the api
        for i in range(5):
            tags = ["foo", f"tag{i}"]
            response = self.client.post(
                reverse("api-v1-json:file_tag", kwargs={"file_uuid": files[i]}),
                data={
                    "tags": tags,
                },
                headers={"authorization": self.tokens[self.creator2]},
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
                headers={"authorization": self.tokens[self.curator6]},
                content_type="application/json",
            )
            assert response.status_code == 201

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_ZERO_1_0"]},
            headers={"authorization": self.tokens[self.creator2]},
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
                headers={"authorization": self.tokens[self.creator2]},
            )
            assert response.status_code == 200
            assert len(response.json()["bma_response"]) == 1

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"tags": ["foo"]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 5

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"tags": ["foo", "bar"]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 3

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"tags": ["foo", "bar", "tag3"]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 1

        # test taggers filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"taggers": [str(self.creator2.uuid)]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 10

        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"taggers": [str(self.creator2.uuid), str(self.curator6.uuid)]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 3

        # untag some files and test filtering
        for i in range(4, 7):
            tags = [f"tag{i}"]
            # all 3 files are tagged with tagN, file4 has weight 2
            response = self.client.get(
                reverse("api-v1-json:file_list"),
                data={"tags": tags},
                headers={"authorization": self.tokens[self.creator2]},
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
                headers={"authorization": self.tokens[self.curator6]},
                content_type="application/json",
            )
            assert response.status_code == 200

            # only file4 is still tagged with tagN, weight for tagN for file4 is now one
            response = self.client.get(
                reverse("api-v1-json:file_list"),
                data={"tags": tags},
                headers={"authorization": self.tokens[self.creator2]},
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
            data={"taggers": [str(self.curator6.uuid)]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 8

        # remove curator6 bar tagging from file4
        response = self.client.post(
            reverse("api-v1-json:file_untag", kwargs={"file_uuid": files[4]}),
            data={
                "tags": ["bar"],
            },
            headers={"authorization": self.tokens[self.curator6]},
            content_type="application/json",
        )
        assert response.status_code == 200

        # curator6 now only tagged 7 files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"taggers": [str(self.curator6.uuid)]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 7

        # bar tag is now ony only applied to 7 files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"tags": ["bar"]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 7

    def test_file_list_permissions(self) -> None:
        """Test various permissions stuff for the file_list endpoint."""
        files = [self.file_upload(title=f"title{i}") for i in range(15)]

        # no files should be visible
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.user0]})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

        # the superuser can see all files
        response = self.client.get(
            reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.superuser]}
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 15

        # attempt to publish a file before approval
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200

        # attempt to unpublish a file before approval
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200

        # approve the file without permission
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 403

        # approve the file, check mode
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.tokens[self.superuser]},
        )
        assert response.status_code == 202

        # really approve the file
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.superuser]},
        )
        assert response.status_code == 200

        # now list unpublished files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"published": False},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 15

        # publish a file, check mode
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 202

        # publish the file
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200

        # make sure someone else can see it
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.user0]})
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
            headers={"authorization": self.tokens[self.user0]},
        )
        assert response.status_code == 403

        # unpublish the file, check mode
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 202

        # unpublish the file
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200

        # make sure it is not visible anymore
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.user0]})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

        # make sure it is not visible anymore to anonymous
        response = self.client.get(
            reverse("api-v1-json:file_list"),
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

        # delete the file without permission
        response = self.client.delete(
            reverse("api-v1-json:softdelete_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.creator3]},
        )
        assert response.status_code == 403

        # delete the file, check mode
        response = self.client.delete(
            reverse("api-v1-json:softdelete_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.tokens[self.superuser]},
        )
        assert response.status_code == 202

        # really delete the file
        response = self.client.delete(
            reverse("api-v1-json:softdelete_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.superuser]},
        )
        assert response.status_code == 204

        # now list deleted files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"deleted": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 1

        # undelete the file without permission
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.creator3]},
        )
        assert response.status_code == 403

        # undelete the file, check mode
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.tokens[self.superuser]},
        )
        assert response.status_code == 202

        # really undelete the file
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.superuser]},
        )
        assert response.status_code == 200

        # now list deleted files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"deleted": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

    def test_file_list_ordering(self) -> None:
        """Make sure files are ordered by date with the oldest file first."""
        # upload 15 files and get them all
        [self.file_upload(title=f"title{i}") for i in range(15)]
        response = self.client.get(
            reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.superuser]}
        )
        latest = None
        for f in response.json()["bma_response"]:
            if not latest:
                latest = f["created_at"]
            if latest > f["created_at"]:
                raise AssertionError(f"Files are sorted wrong! {latest} > {f['created_at']}")
            latest = f["created_at"]

    def test_metadata_get(self) -> None:
        """Get file metadata from the API."""
        self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200
        assert "uuid" in response.json()["bma_response"]
        assert response.json()["bma_response"]["uuid"] == self.file_uuid

    def test_file_download(self) -> None:
        """Test downloading a file after uploading it."""
        self.file_upload()
        metadata = self.client.get(
            reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.creator2]}
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
        with (settings.BASE_DIR / "static_src/images/file-video-solid.png").open("rb") as f:
            assert f.read() == response.getvalue()

    def test_file_metadata_update(self) -> None:
        """Replace and then update file metadata."""
        self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.tokens[self.creator2]},
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
            headers={"authorization": self.tokens[self.user0]},
            content_type="application/json",
        )
        assert response.status_code == 403

        # update the file, check mode
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}) + "?check=true",
            updates,
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 202

        # replace the file metadata
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 200
        original_metadata.update(updates)
        for k, v in response.json()["bma_response"].items():
            # "updated_at" will have changed of course,
            if k == "updated_at":
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
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 422
        # then with a valid url
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"original_source": "https://example.com/foo.png"},
            headers={"authorization": self.tokens[self.creator2]},
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
            headers={"authorization": self.tokens[self.user0]},
        )
        assert response.status_code == 403

        # delete file, check mode
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}) + "?check=true",
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 202

        # delete file
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 204

        # undelete file, wrong user
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_file", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.tokens[self.user0]},
        )
        assert response.status_code == 403

        # undelete file, check mode
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_file", kwargs={"file_uuid": self.file_uuid}) + "?check=true",
            headers={"authorization": self.tokens[self.superuser]},
        )
        assert response.status_code == 202

        # undelete file
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_file", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.tokens[self.superuser]},
        )
        assert response.status_code == 200

    def test_metadata_get_404(self) -> None:
        """Get file metadata get with wrong uuid returns 404."""
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": "a35ce7c9-f814-46ca-8c4e-87b992e15819"},
            ),
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 404

    def test_metadata_get_validationerror(self) -> None:
        """Get file metadata get with something that is not a uuid."""
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": "notuuid"}),
            headers={"authorization": self.tokens[self.creator2]},
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
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert response.status_code == 200
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            headers={"authorization": self.tokens[self.user0]},
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
        """Approve/unapprove single or multiple files."""
        for _ in range(10):
            self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.creator2]}
        )
        files = [f["uuid"] for f in response.json()["bma_response"]]
        # first try with no permissions
        response = self.client.patch(
            reverse("api-v1-json:approve_files"),
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then check mode
        response = self.client.patch(
            reverse("api-v1-json:approve_files") + "?check=true",
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then with permission, first single file
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200
        # then multiple files
        response = self.client.patch(
            reverse("api-v1-json:approve_files"),
            {"files": files[1:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure files are now approved
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"approved": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 5

        # now unapprove,
        # first try with no permissions
        response = self.client.patch(
            reverse("api-v1-json:unapprove_files"),
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then check mode
        response = self.client.patch(
            reverse("api-v1-json:unapprove_files") + "?check=true",
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then with permission, first single file
        response = self.client.patch(
            reverse("api-v1-json:unapprove_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200
        # then multiple files
        response = self.client.patch(
            reverse("api-v1-json:unapprove_files"),
            {"files": files[1:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure files are now unapproved
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"approved": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

    def test_publish_files(self) -> None:
        """Publish/unpublish single or multiple files."""
        for _ in range(10):
            self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.creator2]}
        )
        files = [f["uuid"] for f in response.json()["bma_response"]]
        # first try with no permissions
        response = self.client.patch(
            reverse("api-v1-json:publish_files"),
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.creator3]},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then check mode
        response = self.client.patch(
            reverse("api-v1-json:publish_files") + "?check=true",
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then with permission, first single file
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200
        # then multiple files
        response = self.client.patch(
            reverse("api-v1-json:publish_files"),
            {"files": files[1:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure files are now publishd
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"published": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 5

        # now unpublish,
        # first try with no permissions
        response = self.client.patch(
            reverse("api-v1-json:unpublish_files"),
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.creator3]},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then check mode
        response = self.client.patch(
            reverse("api-v1-json:unpublish_files") + "?check=true",
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then with permission, first single file
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200
        # then multiple files
        response = self.client.patch(
            reverse("api-v1-json:unpublish_files"),
            {"files": files[1:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure files are now unpublishd
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"published": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

    def test_delete_files(self) -> None:
        """Softdelete/unsoftdelete single or multiple files."""
        for _ in range(10):
            self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_list"), headers={"authorization": self.tokens[self.creator2]}
        )
        files = [f["uuid"] for f in response.json()["bma_response"]]
        # first try with no permissions
        response = self.client.delete(
            reverse("api-v1-json:softdelete_files"),
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.user0]},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then check mode
        response = self.client.delete(
            reverse("api-v1-json:softdelete_files") + "?check=true",
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then with permission, first single file
        response = self.client.delete(
            reverse("api-v1-json:softdelete_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 204
        # then multiple files
        response = self.client.delete(
            reverse("api-v1-json:softdelete_files"),
            {"files": files[1:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 204

        # make sure files are now deleted
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"deleted": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 5

        # now undelete,
        # first try with no permissions
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_files"),
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.user0]},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then check mode
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_files") + "?check=true",
            {"files": files[0:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then with permission, first single file
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200
        # then multiple files
        response = self.client.patch(
            reverse("api-v1-json:unsoftdelete_files"),
            {"files": files[1:5]},
            headers={"authorization": self.tokens[self.superuser]},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure files are now undeleted
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"deleted": True},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 0

    def test_file_missing_on_disk(self) -> None:
        """Test the case where a file has gone missing from disk for some reason."""
        self.file_upload()
        basefile = BaseFile.objects.get(uuid=self.file_uuid)
        Path(basefile.original.path).unlink()  # type: ignore[attr-defined]
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            headers={"authorization": self.tokens[self.creator2]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["bma_response"]["size_bytes"], 0)
