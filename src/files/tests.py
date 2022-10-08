from django.urls import reverse
from oauth2_provider.models import get_access_token_model
from oauth2_provider.models import get_application_model
from oauth2_provider.models import get_grant_model

from utils.tests import ApiTestBase

Application = get_application_model()
AccessToken = get_access_token_model()
Grant = get_grant_model()


class TestFilesApi(ApiTestBase):
    """Test for methods in the files API."""

    def test_api_auth_bearer_token(self):
        response = self.client.get(
            "/o/authorized_tokens/",
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 200
        assert "revoke" in response.content.decode("utf-8")

    def test_api_auth_get_refresh_token(self):
        response = self.client.post(
            "/o/token/",
            {
                "grant_type": "refresh_token",
                "client_id": f"client_id_{self.user1.username}",
                "refresh_token": self.user1.tokeninfo["refresh_token"],
            },
        )
        assert response.status_code == 200
        assert "refresh_token" in response.json()

    def test_api_auth_django_session(self):
        self.client.force_login(self.user1)
        response = self.client.get("/o/authorized_tokens/")
        assert response.status_code == 200
        assert "revoke" in response.content.decode("utf-8")

    def test_file_upload(self):
        """Test file upload cornercases."""
        data = self.file_upload(title="", return_full=True)
        assert data["title"] == data["original_filename"]
        self.file_upload(license="notalicense", expect_status_code=422)

    def test_file_list(self):
        """Test the file_list endpoint."""
        files = []
        for i in range(15):
            files.append(self.file_upload(title=f"title{i}"))
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 15

        # test sorting
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": 5, "sorting": "title_asc"},
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert len(response.json()) == 5
        assert response.json()[0]["title"] == "title0"
        assert response.json()[1]["title"] == "title1"
        assert response.json()[2]["title"] == "title10"
        assert response.json()[4]["title"] == "title12"
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": 1, "sorting": "created_desc"},
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.json()[0]["title"] == "title14"

        # test offset
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"offset": 5, "sorting": "created_asc"},
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.json()[0]["title"] == "title5"
        assert response.json()[4]["title"] == "title9"

        # test search
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"search": "title7"},
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "title7"

        # create an album with some files
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": "album title here",
                "files": files[3:6],
            },
            HTTP_AUTHORIZATION=self.user1.auth,
            content_type="application/json",
        )
        assert response.status_code == 201
        self.album_uuid = response.json()["uuid"]

        # test album filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid]},
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert len(response.json()) == 3

    def test_file_list_permissions(self):
        """Test various permissions stuff for the file_list endpoint."""
        files = []
        for i in range(15):
            files.append(self.file_upload(title=f"title{i}"))

        # no files should be visible
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            HTTP_AUTHORIZATION=self.user2.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 0

        # the superuser can see all files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            HTTP_AUTHORIZATION=self.superuser.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 15

        # attempt to publish a file before approval
        response = self.client.patch(
            reverse("api-v1-json:file_publish", kwargs={"file_uuid": files[0]}),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 403

        # approve the file without permission
        response = self.client.patch(
            reverse("api-v1-json:file_approve", kwargs={"file_uuid": files[0]}),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 403

        # approve the file
        response = self.client.patch(
            reverse("api-v1-json:file_approve", kwargs={"file_uuid": files[0]}),
            HTTP_AUTHORIZATION=self.superuser.auth,
        )
        assert response.status_code == 200

        # now list UNPUBLISHED files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"statuses": ["UNPUBLISHED"]},
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert len(response.json()) == 1

        # publish a file
        response = self.client.patch(
            reverse("api-v1-json:file_publish", kwargs={"file_uuid": files[0]}),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 200

        # make sure someone else can see it
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            HTTP_AUTHORIZATION=self.user2.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

        # unpublish the file without permission
        response = self.client.patch(
            reverse("api-v1-json:file_unpublish", kwargs={"file_uuid": files[0]}),
            HTTP_AUTHORIZATION=self.user2.auth,
        )
        assert response.status_code == 403

        # unpublish the file again
        response = self.client.patch(
            reverse("api-v1-json:file_unpublish", kwargs={"file_uuid": files[0]}),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 200

        # make sure it is not visible anymore
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            HTTP_AUTHORIZATION=self.user2.auth,
        )
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_metadata_get(self):
        """Get file metadata from the API."""
        self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 200
        assert "uuid" in response.json()
        assert response.json()["uuid"] == self.file_uuid

    def test_file_download(self):
        """Test downloading a file after uploading it."""
        self.file_upload()
        metadata = self.client.get(
            reverse("api-v1-json:file_list"),
            HTTP_AUTHORIZATION=self.user1.auth,
        ).json()[0]
        url = metadata["url"]
        # try download of unpublished file without auth
        response = self.client.get(url)
        assert response.status_code == 404
        # try again with auth
        self.client.force_login(self.user1)
        response = self.client.get(url)
        assert response.status_code == 200
        assert response["content-type"] == "image/png"
        with open("static_src/images/logo_wide_black_500_RGB.png", "rb") as f:
            assert f.read() == response.getvalue()

    def test_file_metadata_update(self):
        """Replace and then update file metadata."""
        self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 200
        original_metadata = response.json()
        updates = {
            "title": "some title",
            "description": "some description",
            "license": "CC_ZERO_1_0",
            "attribution": "some attribution",
        }
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            content_type="application/json",
        )
        assert response.status_code == 403
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            HTTP_AUTHORIZATION=f"Bearer {self.user2.tokeninfo['access_token']}",
            content_type="application/json",
        )
        assert response.status_code == 403
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            HTTP_AUTHORIZATION=self.user1.auth,
            content_type="application/json",
        )
        assert response.status_code == 200
        original_metadata.update(updates)
        for k, v in response.json().items():
            # "updated" will have changed of course,
            if k == "updated":
                assert v != original_metadata[k]
            # and "source" was initially set but not specified in the PUT call,
            # so it should be blank now
            elif k == "source":
                assert v == ""
            # everything else should be the same
            else:
                assert v == original_metadata[k]

        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"source": "outer space"},
            HTTP_AUTHORIZATION=self.user1.auth,
            content_type="application/json",
        )
        assert response.status_code == 200
        # make sure we updated only the source attribute with the PATCH request
        assert response.json()["source"] == "outer space"
        assert response.json()["attribution"] == "some attribution"

    #   def test_post_csrf(self):
    #       """Make sure CSRF is enforced on API views when using django session cookie auth."""
    #       self.file_upload()
    #       self.client.force_login(self.user)
    #       response = self.client.patch(
    #           reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
    #           {"attribution": "csrfcheck"},
    #           content_type="application/json",
    #       )
    #       # this should fail because we did not add CSRF..
    #       assert response.status_code == 403

    def test_file_delete(self):
        """Test deleting a file."""
        self.file_upload()
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
        )
        assert response.status_code == 403
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            HTTP_AUTHORIZATION=f"Bearer {self.user2.tokeninfo['access_token']}",
        )
        assert response.status_code == 403
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 204

    def test_metadata_get_404(self):
        """Get file metadata get with wrong uuid returns 404."""
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": "a35ce7c9-f814-46ca-8c4e-87b992e15819"},
            ),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 404

    def test_metadata_get_validationerror(self):
        """Get file metadata get with something that is not a uuid."""
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": "notuuid"}),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 422

    def test_metadata_get_403(self):
        """Get file metadata get with wrong uuid returns 404."""
        self.file_upload()
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            HTTP_AUTHORIZATION=self.user1.auth,
        )
        assert response.status_code == 200
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.user2.tokeninfo['access_token']}",
        )
        assert response.status_code == 403
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
        )
        assert response.status_code == 403
