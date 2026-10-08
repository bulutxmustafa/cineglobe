"""Social endpoints (plan §3.11, Faz 7C).

Public reads (profiles, lists, shared notebooks, community) need no account
(policy v1.7) but are noindex and never cached by a CDN, so hiding or revoking
takes effect immediately. Anything not visible answers 404, never 403.
"""

from __future__ import annotations

import random

from django.db.models import Count, Q
from django.http import Http404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.catalog.image_utils import poster_url
from apps.catalog.params import get_language, get_page
from apps.catalog.tmdb_client import TMDBClient, TMDBError
from apps.notebook.models import NotebookEntry
from apps.social import visibility
from apps.social.models import Block, NotebookShare, Profile, UserList
from apps.social.serializers import (
    BlockSerializer,
    ListItemsWriteSerializer,
    ListWriteSerializer,
    OwnProfileSerializer,
    ProfileWriteSerializer,
    ReportCreateSerializer,
    ShareCreateSerializer,
    ShareSerializer,
    list_data,
    list_item_data,
)
from apps.social.services import (
    SocialError,
    block,
    clone_list,
    community_rating,
    create_list,
    create_share,
    replace_items,
    report,
    resolve_share,
    shared_entries,
    unblock,
    update_list,
    update_profile,
)

PAGE_SIZE = 10


def _error(code: str, http_status: int = 400, field: str | None = None) -> Response:
    return Response(
        {
            "error": {
                "code": code,
                "message": code.replace("_", " "),
                "status_code": http_status,
                "details": {field: [code]} if field else None,
            }
        },
        status=http_status,
    )


def _tmdb() -> TMDBClient | None:
    try:
        return TMDBClient()
    except ValueError:
        return None


def _public(response: Response) -> Response:
    """User content: keep it out of search engines and out of shared caches."""
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Cache-Control"] = "private, no-store"
    return response


class WriteThrottle:
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social"


# --- My profile -----------------------------------------------------------------------


class MyProfileView(WriteThrottle, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="My profile settings", tags=["Social"])
    def get(self, request):
        # No profile yet: the defaults (empty username = not created) fill the form.
        profile = Profile.objects.filter(user=request.user).first() or Profile(
            user=request.user
        )
        return Response(OwnProfileSerializer(profile).data)

    @extend_schema(
        summary="Create or update my profile",
        request=ProfileWriteSerializer,
        tags=["Social"],
    )
    def patch(self, request):
        serializer = ProfileWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            profile = update_profile(request.user, serializer.validated_data)
        except SocialError as exc:
            return _error(exc.code, field=exc.field)
        return Response(OwnProfileSerializer(profile).data)


# --- My lists ---------------------------------------------------------------------------


class MyListsView(WriteThrottle, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="My lists", tags=["Social"])
    def get(self, request):
        lists = UserList.objects.filter(owner=request.user).prefetch_related("items")
        return Response([list_data(lst, with_items=False) for lst in lists])

    @extend_schema(
        summary="Create a list", request=ListWriteSerializer, tags=["Social"]
    )
    def post(self, request):
        serializer = ListWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_list = create_list(request.user, serializer.validated_data)
        except SocialError as exc:
            return _error(
                exc.code, 429 if exc.code == "daily_limit" else 400, exc.field
            )
        return Response(list_data(user_list), status=status.HTTP_201_CREATED)


class MyListView(WriteThrottle, APIView):
    permission_classes = [IsAuthenticated]

    def _list(self, request, pk: int) -> UserList:
        user_list = UserList.objects.filter(pk=pk, owner=request.user).first()
        if user_list is None:
            raise Http404
        return user_list

    @extend_schema(summary="One of my lists", tags=["Social"])
    def get(self, request, pk: int):
        return Response(list_data(self._list(request, pk)))

    @extend_schema(
        summary="Rename / change visibility",
        request=ListWriteSerializer,
        tags=["Social"],
    )
    def patch(self, request, pk: int):
        serializer = ListWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            user_list = update_list(self._list(request, pk), serializer.validated_data)
        except SocialError as exc:
            return _error(exc.code, field=exc.field)
        return Response(list_data(user_list))

    @extend_schema(summary="Delete a list", responses={204: None}, tags=["Social"])
    def delete(self, request, pk: int):
        self._list(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyListItemsView(WriteThrottle, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Replace all items in order (drag & drop or keyboard reorder)",
        request=ListItemsWriteSerializer,
        tags=["Social"],
    )
    def put(self, request, pk: int):
        user_list = UserList.objects.filter(pk=pk, owner=request.user).first()
        if user_list is None:
            raise Http404
        serializer = ListItemsWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            replace_items(
                user_list,
                serializer.validated_data["items"],
                _tmdb(),
                get_language(request),
            )
        except SocialError as exc:
            return _error(exc.code, 404 if exc.code == "title_not_found" else 400)
        except TMDBError:
            return _error("service_unavailable", 503)
        user_list.refresh_from_db()
        return Response(list_data(user_list))


# --- Public reads -------------------------------------------------------------------------


class PublicProfileView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    @extend_schema(
        summary="A member's public profile (no account needed)", tags=["Social"]
    )
    def get(self, request, username: str):
        profile = (
            Profile.objects.filter(username=username.lower())
            .select_related("user")
            .first()
        )
        if profile is None or not visibility.can_view_profile(profile, request.user):
            raise Http404
        entries = visibility.entries_on_profile(profile, request.user)
        favorites = entries.filter(is_favorite=True)[:12]
        recent = entries.filter(rating_x2__isnull=False).order_by("-updated_at")[:12]
        data = {
            "id": profile.pk,  # target id for reports
            "username": profile.username,
            "display_name": profile.display_name or profile.username,
            "bio": profile.bio,
            "avatar_kind": profile.avatar_kind,
            "avatar_url": poster_url(profile.avatar_poster_path or ""),
            "is_owner": visibility.is_owner(profile.user_id, request.user),
            "favorites": [_entry_card(e) for e in favorites],
            "recent_ratings": [_entry_card(e) for e in recent],
            "lists": [
                list_data(lst, with_items=False)
                for lst in visibility.lists_on_profile(profile, request.user)
            ],
        }
        if profile.show_stats:
            data["stats"] = entries.aggregate(
                watched=Count("id", filter=Q(status="watched")),
                rated=Count("id", filter=Q(rating_x2__isnull=False)),
            )
        return _public(Response(data))


def _entry_card(entry: NotebookEntry) -> dict:
    return {
        "media_type": entry.media_type,
        "tmdb_id": entry.tmdb_id,
        "title": entry.title,
        "year": entry.year,
        "poster_url": poster_url(entry.poster_path or ""),
        "rating_x2": entry.rating_x2,
        "status": entry.status,
    }


class PublicListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    @extend_schema(summary="A list by its link (public or unlisted)", tags=["Social"])
    def get(self, request, slug: str):
        return _public(Response(_visible_list_data(request, slug)))


def _visible_list(request, slug: str) -> UserList:
    user_list = (
        UserList.objects.filter(slug=slug).select_related("owner__profile").first()
    )
    if user_list is None or not visibility.can_view_list(user_list, request.user):
        raise Http404
    return user_list


def _visible_list_data(request, slug: str) -> dict:
    user_list = _visible_list(request, slug)
    data = list_data(user_list)
    profile = getattr(user_list.owner, "profile", None)
    show_owner = profile and visibility.can_view_profile(profile, request.user)
    data["owner"] = profile.username if show_owner else None
    data["is_owner"] = visibility.is_owner(user_list.owner_id, request.user)
    return data


class PublicListRandomView(APIView):
    """Lucky Globe source: a random title from a visible list (plan Faz 7C)."""

    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    @extend_schema(summary="Random title from a list", tags=["Social"])
    def get(self, request, slug: str):
        user_list = _visible_list(request, slug)
        exclude = {
            k.strip()
            for k in request.query_params.get("exclude", "").split(",")
            if k.strip()
        }
        items = list(user_list.items.all())
        pool = [
            i for i in items if f"{i.media_type}:{i.tmdb_id}" not in exclude
        ] or items
        pick = random.choice(pool) if pool else None  # noqa: S311
        return _public(Response({"pick": list_item_data(pick) if pick else None}))


class CloneListView(WriteThrottle, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Copy a visible list into my lists", tags=["Social"])
    def post(self, request, slug: str):
        source = _visible_list(request, slug)  # cannot copy what you cannot see
        try:
            copy = clone_list(source, request.user)
        except SocialError as exc:
            return _error(exc.code, 429 if exc.code == "daily_limit" else 400)
        return Response(list_data(copy), status=status.HTTP_201_CREATED)


class SharedNotebookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(summary="A notebook shared by link (read-only)", tags=["Social"])
    def get(self, request, token: str):
        share = resolve_share(token)
        if share is None:
            raise Http404  # unknown, revoked and expired look the same
        NotebookShare.objects.filter(pk=share.pk).update(
            view_count=share.view_count + 1
        )
        profile = Profile.objects.filter(user=share.user).first()
        body = {
            "owner": profile.display_name or profile.username if profile else None,
            "scope": share.scope,
            "includes_notes": share.scope == NotebookShare.Scope.RATINGS_NOTES,
            "entries": shared_entries(share),
        }
        return _public(Response(body))


class CommunityView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    @extend_schema(
        summary="Community rating and public raters for a title", tags=["Social"]
    )
    def get(self, request, media_type: str, tmdb_id: int):
        if media_type not in ("movie", "tv"):
            raise Http404
        rating = community_rating(media_type, tmdb_id)
        raters = visibility.public_raters(media_type, tmdb_id, request.user).order_by(
            "-updated_at"
        )
        page = get_page(request)
        start = (page - 1) * PAGE_SIZE
        chunk = list(raters[start : start + PAGE_SIZE])
        response = Response(
            {
                "average": rating.average,  # stars (0.5-5); None below 5 votes
                "votes": rating.votes,
                "raters": [
                    {
                        "username": e.user.profile.username,
                        "display_name": e.user.profile.display_name
                        or e.user.profile.username,
                        "rating_x2": e.rating_x2,
                    }
                    for e in chunk
                ],
                "page": page,
            }
        )
        return _public(response)


# --- Shares, reports, blocks ------------------------------------------------------------------


class MySharesView(WriteThrottle, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="My share links", tags=["Social"])
    def get(self, request):
        return Response(
            ShareSerializer(
                NotebookShare.objects.filter(user=request.user), many=True
            ).data
        )

    @extend_schema(
        summary="Create a read-only link to my notebook (token shown once)",
        request=ShareCreateSerializer,
        tags=["Social"],
    )
    def post(self, request):
        serializer = ShareCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        share, token = create_share(request.user, **serializer.validated_data)
        body = {**ShareSerializer(share).data, "token": token, "path": f"/s/{token}"}
        if share.scope == NotebookShare.Scope.RATINGS_NOTES:
            body["warning"] = {
                "tr": "Bu bağlantıyı alan herkes notlarını okuyabilir.",
                "en": "Anyone with this link can read your notes.",
            }[get_language(request)]
        return Response(body, status=status.HTTP_201_CREATED)


class MyShareView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Revoke a share link (immediately)",
        responses={204: None},
        tags=["Social"],
    )
    def delete(self, request, pk: int):
        updated = NotebookShare.objects.filter(
            pk=pk, user=request.user, revoked_at__isnull=True
        ).update(revoked_at=timezone.now())
        if (
            not updated
            and not NotebookShare.objects.filter(pk=pk, user=request.user).exists()
        ):
            raise Http404
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportView(WriteThrottle, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Report a profile or list",
        request=ReportCreateSerializer,
        tags=["Social"],
    )
    def post(self, request):
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            report(request.user, **serializer.validated_data)
        except SocialError as exc:
            return _error(exc.code, 429 if exc.code == "daily_limit" else 400)
        # Same answer whether or not it hid the content.
        return Response(
            {"detail": "Thanks, we will review it."}, status=status.HTTP_201_CREATED
        )


class MyBlocksView(WriteThrottle, APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="People I blocked", tags=["Social"])
    def get(self, request):
        names = Block.objects.filter(blocker=request.user).values_list(
            "blocked__profile__username", flat=True
        )
        return Response([n for n in names if n])

    @extend_schema(summary="Block someone", request=BlockSerializer, tags=["Social"])
    def post(self, request):
        serializer = BlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            block(request.user, serializer.validated_data["username"])
        except SocialError as exc:
            return _error(exc.code)
        return Response(status=status.HTTP_201_CREATED)


class MyBlockView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Unblock", responses={204: None}, tags=["Social"])
    def delete(self, request, username: str):
        unblock(request.user, username)
        return Response(status=status.HTTP_204_NO_CONTENT)
