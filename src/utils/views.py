from urllib.parse import quote

from django.http import HttpResponse


def AccelMediaView(request, path):
    response = HttpResponse(status=200)
    del response["Content-Type"]
    response["X-Accel-Redirect"] = f"/public/{quote(path)}"
    return response
