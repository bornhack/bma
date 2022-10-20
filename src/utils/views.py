from django.middleware.csrf import get_token
from django.shortcuts import render


def csrfview(request):
    token = get_token(request)
    return render(request, "csrf.html", {"csrftoken": token})
