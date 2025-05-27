"""Tests for the jobs API."""

import json
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.urls import reverse

from utils.tests import BmaTestBase


class TestJobsApi(BmaTestBase):
    """Test for methods in the jobs API."""

    files: list[str]
    jobs: list

    @classmethod
    def setUpTestData(cls) -> None:
        """Add test data."""
        # first add users and other basics
        super().setUpTestData()
        # upload some files
        cls.files = [cls.file_upload(title=f"title{i}") for i in range(5)]

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

    def test_api_job_settings(self) -> None:
        """Test the job settings endpoint."""
        response = self.client.get(
            reverse("api-v1-json:job_settings"), headers={"authorization": self.tokens[self.creator2]}
        )
        assert response.status_code == 200


    def test_job_list(self) -> None:
        """Test the job_list endpoint."""
        response = self.client.get(
            reverse("api-v1-json:job_list"), headers={"authorization": self.tokens[self.creator2]}
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 100

        # test limit
        response = self.client.get(
            reverse("api-v1-json:job_list"),
            data={"limit": "5", "sorting": "created_at_asc"},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 5

        # test finished
        response = self.client.get(
            reverse("api-v1-json:job_list"),
            data={"limit": "100", "finished": "false"},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 100

        # test offset
        response = self.client.get(
            reverse("api-v1-json:job_list"),
            data={"limit": "5", "offset": "5"},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 5

        # test file uuid filter.
        response = self.client.get(
            reverse("api-v1-json:job_list"),
            data={"file_uuid": self.files[0]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 29

        # test user uuid filter.
        response = self.client.get(
            reverse("api-v1-json:job_list"),
            data={"user_uuid": str(self.creator2.uuid)},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 5

        # test client uuid filter.
        response = self.client.get(
            reverse("api-v1-json:job_list"),
            data={"client_uuid": str(self.clientinfo["client_uuid"])},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 5

        # test client version filter.
        response = self.client.get(
            reverse("api-v1-json:job_list"),
            data={"client_version": self.clientinfo["client_version"]},
            headers={"authorization": self.tokens[self.creator2]},
        )
        assert len(response.json()["bma_response"]) == 5

    def test_job_assign(self) -> None:
        """Test the assign_file_jobs endpoint."""
        response = self.client.post(
            path=reverse("api-v1-json:assign_file_jobs"),
            data={"client_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "client_version": "test-1.2.3"},
            query_params={"limit": 100},
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert len(response.json()["bma_response"]) == 28

        #Test No worker permission
        response = self.client.post(
            path=reverse("api-v1-json:assign_file_jobs"),
            data={"client_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "client_version": "test-1.2.3"},
            query_params={"limit": 1},
            headers={"authorization": self.tokens[self.user0]},
            content_type="application/json",
        )
        assert response.json()["message"] == "No worker permission."

    def test_unassign_job(self) -> None:
        """Test the unassign_job endpoint."""
        response = self.client.post(
            path=reverse("api-v1-json:assign_file_jobs"),
            data={"client_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "client_version": "test-1.2.3"},
            query_params={"limit": 1},
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        jobs = response.json()["bma_response"]

        response = self.client.post(
            path=reverse("api-v1-json:unassign_job", kwargs={
                "job_uuid": jobs[0]["job_uuid"],
            }),
            query_params={"check": True},
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.json()["message"] == "OK"

        response = self.client.post(
            path=reverse("api-v1-json:unassign_job", kwargs={
                "job_uuid": jobs[0]["job_uuid"],
            }),
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        assert response.json()["message"] == "OK, job unassigned"

        #Test No worker permission
        response = self.client.post(
            path=reverse("api-v1-json:unassign_job", kwargs={
                "job_uuid": jobs[0]["job_uuid"],
            }),
            headers={"authorization": self.tokens[self.user0]},
            content_type="application/json",
        )
        assert response.json()["message"] == "No worker permission."

    def upload_result(self, job: dict, data: BytesIO | None, metadata: str):
        filepath: str | Path = settings.BASE_DIR / "static_src/images/file-video-solid.png"
        with Path(filepath).open("rb") as f:
            payload = {
                "data": data if data else f,
                "client": json.dumps({
                    "client_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "client_version": "test-1.2.3"
                }),
            }
            if metadata:
                payload.update(metadata=metadata)
            return self.client.post(
                reverse("api-v1-json:upload_result", kwargs={"job_uuid": job["job_uuid"]}),
                payload,
                headers={"authorization": self.tokens[self.creator2]},
            )

    def test_upload_result(self) -> None:
        """Test the upload result"""
        filepath: str | Path = settings.BASE_DIR / "static_src/images/file-video-solid.png"

        # Assign jobs
        response = self.client.post(
            path=reverse("api-v1-json:assign_file_jobs"),
            data={
                "client_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "client_version": "test-1.2.3"
            },
            query_params={"limit": 1},
            headers={"authorization": self.tokens[self.creator2]},
            content_type="application/json",
        )
        jobs = response.json()["bma_response"]
        thumbnail_job_tested: bool = False
        image_conversion_job_tested: bool = False
        thumbnail_source_job_tested: bool = False

        #Test No worker permission
        with Path(filepath).open("rb") as f:
            response = self.client.post(
                reverse("api-v1-json:upload_result", kwargs={
                    "job_uuid": "b7cd49a1-0822-4459-b51c-d90d3f08d12a",
                }),
                {
                    "data": f,
                    "client": json.dumps({
                        "client_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "client_version": "test-1.2.3",
                    })
                },
                headers={"authorization": self.tokens[self.user0]},
            )
        assert response.status_code == 403
        assert response.json()["message"] == "No worker permission."

        for job in jobs:
            if job["job_type"] == "ThumbnailJob" and not thumbnail_job_tested:
                # Test no metadata error
                response = self.upload_result(job, None, None)
                assert response.status_code == 422

                # Test normal ThumbnailJob result upload
                response = self.upload_result(
                    job=job,
                    data=None,
                    metadata=json.dumps({
                        "width": job["width"],
                        "height": job["height"],
                        "mimetype": job["mimetype"],
                    }),
                )
                assert response.status_code == 200
                thumbnail_job_tested = True
            if job["job_type"] == "ImageConversionJob" and not image_conversion_job_tested:
                # Test no metadata error
                response = self.upload_result(job, None, None)
                assert response.status_code == 422

                # Test normal ImageConversionJob result upload
                response = self.upload_result(
                    job=job,
                    data=None,
                    metadata=json.dumps({
                        "width": job["width"],
                        "height": job["height"],
                        "mimetype": job["mimetype"],
                    }),
                )
                assert response.status_code == 200
                image_conversion_job_tested = True
            if job["job_type"] == "ThumbnailSourceJob" and not thumbnail_source_job_tested:
                response = self.upload_result(
                    job=job,
                    data=None,
                    metadata=json.dumps({
                        "width": job["width"],
                        "height": job["height"],
                        "mimetype": job["mimetype"],
                    }),
                )
                assert response.status_code == 200
                thumbnail_source_job_tested = True
            if job["job_type"] == "ImageExifExtractionJob":
                with BytesIO() as buf:
                    buf.write(json.dumps({
                        "EXIF": {
                            "Flash": "Flash did not fire, compulsory flash mode",
                            "FNumber": "7/4",
                            "SceneType": "0",
                            "ColorSpace": "sRGB",
                        },
                        "Image": {
                            "Make": "OneTest",
                            "Model": "TestOne",
                        },
                    }).encode())
                    buf.seek(0)
                    response = self.upload_result(
                        job=job,
                        data=("exif.json", buf),
                        metadata=None,
                    )
                assert response.status_code == 200
