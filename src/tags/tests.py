"""Tests for the files API."""

from django.urls import reverse

from utils.tests import BmaTestBase


class TestTagsApi(BmaTestBase):
    """Test tag stuff in the API."""

    def test_tag_api(self) -> None:
        """Test the tag api."""
        files = [self.file_upload(title=f"title{i}") for i in range(15)]

        # tag a couple of files using the api
        for i in range(5):
            tags = ["foo", f"tag{i}"]
            # weight is 1 because each file is only tagged once with each tag
            response_tags = [{"name": tag, "slug": tag, "weight": 1} for tag in tags]
            response = self.client.post(
                reverse("api-v1-json:file_tag", kwargs={"file_uuid": files[i]}),
                data={
                    "tags": tags,
                },
                headers={"authorization": self.creator2.auth},
                content_type="application/json",
            )
            assert response.status_code == 201
            assert response.json()["bma_response"] == response_tags

        # tag a couple of more files using another user
        for i in range(2, 7):
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
            # put the expected response together
            response_tags = [{"name": "bar", "slug": "bar", "weight": 1}]
            if i <= 4:
                # these files are also tagged foo
                response_tags.append({"name": "foo", "slug": "foo", "weight": 1})
                # weight is now 2 for tagN for these files
                response_tags.insert(0, {"name": f"tag{i}", "slug": f"tag{i}", "weight": 2})
            else:
                response_tags.append({"name": f"tag{i}", "slug": f"tag{i}", "weight": 1})
            assert response.json()["bma_response"] == response_tags

        # untag a couple of files using the api
        for i in range(3):
            tags = ["foo"]
            response = self.client.post(
                reverse("api-v1-json:file_untag", kwargs={"file_uuid": files[i]}),
                data={
                    "tags": tags,
                },
                headers={"authorization": self.creator2.auth},
                content_type="application/json",
            )
            # weight is 2 for tagN and there is also a foo tag for i>1
            if i > 1:
                response_tags = [
                    {"name": f"tag{i}", "slug": f"tag{i}", "weight": 2},
                    {"name": "bar", "slug": "bar", "weight": 1},
                ]
            else:
                response_tags = [{"name": f"tag{i}", "slug": f"tag{i}", "weight": 1}]
            assert response.status_code == 200
            assert response.json()["bma_response"] == response_tags
            assert response.json()["message"] == "OK, 1 tag(s) removed"
