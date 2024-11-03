"""Utils for the hitcounter.

Most of this code is originally borrowed from https://github.com/thornomad/django-hitcount/
"""

from ipaddress import ip_address as validate_ip
from typing import NamedTuple

from django.conf import settings
from django.http import HttpRequest

from albums.models import AlbumType
from files.models import BaseFileType
from tags.models import BmaTagType

from .models import BlocklistIP
from .models import BlocklistUserAgent


class UpdateHitCountResponse(NamedTuple):
    """The response from a hitcount update."""

    updated: bool
    reason: str


def count_hit(request: HttpRequest, content_object: BaseFileType | AlbumType | BmaTagType) -> UpdateHitCountResponse:
    """Called with a HttpRequest and a model object it will return a namedtuple.

    UpdateHitCountResponse(hit_counted=Boolean, hit_message='Message').

    `hit_counted` will be True if the hit was counted and False if it was
    not.  `'hit_message` will indicate by what means the Hit was either
    counted or ignored.
    """
    # as of Django 1.8.4 empty sessions are not being saved
    # https://code.djangoproject.com/ticket/25489
    if request.session.session_key is None:
        request.session.save()

    session_key = str(request.session.session_key)
    ip = get_ip(request)
    user_agent = request.headers.get("User-Agent", "")[:255]
    hits_per_ip_limit = getattr(settings, "HITCOUNT_HITS_PER_IP_LIMIT", 0)
    exclude_user_group = getattr(settings, "HITCOUNT_EXCLUDE_USER_GROUP", None)

    # first, check our request against the IP blocklist
    if BlocklistIP.objects.filter(ip__exact=ip):
        return UpdateHitCountResponse(updated=False, reason="Not counted: user IP has been blocklisted")

    # second, check our request against the user agent blocklist
    if BlocklistUserAgent.objects.filter(user_agent__exact=user_agent):
        return UpdateHitCountResponse(updated=False, reason="Not counted: user agent has been blocklisted")

    # third, see if we are excluding a specific user group or not
    if exclude_user_group and request.user.is_authenticated and request.user.groups.filter(name__in=exclude_user_group):
        return UpdateHitCountResponse(updated=False, reason="Not counted: user excluded by group")

    # eliminated first three possible exclusions, now on to checking our database of
    # active hits to see if we should count another one

    # start with a fresh active query set (HITCOUNT_KEEP_HIT_ACTIVE)
    qs = content_object.hits.filter_active()

    # check limit on hits from a unique ip address (HITCOUNT_HITS_PER_IP_LIMIT)
    if hits_per_ip_limit and qs.filter(ip__exact=ip).count() >= hits_per_ip_limit:
        return UpdateHitCountResponse(updated=False, reason="Not counted: hits per IP address limit reached")

    # create a new Hit object with request data
    hit = content_object.hits.model(
        session=session_key,
        ip=get_ip(request),
        user_agent=request.headers.get("User-Agent", "")[:255],
        content_object=content_object,
    )

    # first, use a user's authentication to see if they made an earlier hit
    if request.user.is_authenticated:
        if not qs.filter(user=request.user):
            hit.user = request.user  # associate this hit with a user
            hit.save()
            response = UpdateHitCountResponse(updated=True, reason="Hit counted: user authentication")
        else:
            response = UpdateHitCountResponse(updated=False, reason="Not counted: authenticated user has active hit")

    # if not authenticated, see if we have a repeat session
    elif not qs.filter(session=session_key):
        hit.save()
        response = UpdateHitCountResponse(updated=True, reason="Hit counted: session key")
    else:
        response = UpdateHitCountResponse(updated=False, reason="Not counted: session key has active hit")
    return response


def get_ip(request: HttpRequest) -> str:
    """Retrieves the remote IP address from the request data.

    If the user is behind a proxy, they may have a comma-separated list of IP addresses, so
    we need to account for that.  In such a case, only the first IP in the
    list will be retrieved.  Also, some hosts that use a proxy will put the
    REMOTE_ADDR into HTTP_X_FORWARDED_FOR.  This will handle pulling back the
    IP from the proper place.

    **NOTE** This function was taken from django-tracking (MIT LICENSE)
             http://code.google.com/p/django-tracking/
    """
    # this will return None if REMOTE_ADDR is missing from the request
    ip_address = request.headers.get("X-Forwarded-For", request.META.get("REMOTE_ADDR", ""))
    if "," in ip_address:
        ip_address = ip_address.split(",")[0]
    # this will raise an exception if the IP is not valid
    validate_ip(ip_address.strip())
    # all good
    return ip_address
