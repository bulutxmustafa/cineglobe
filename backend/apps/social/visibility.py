"""THE place that decides who may see what (plan §3.11, Faz 7C: "merkezi izin fonksiyonu").

Every read path of profiles, lists, notebook entries and community data must go
through these functions. Rules:
- private: only the owner;
- unlisted: anyone who has the link (never listed anywhere);
- public: anyone, and listed on the owner's profile only if the profile is public;
- hidden by moderation or a block between the two users → same as not existing;
- callers answer "not visible" with 404, never 403, so existence is not revealed.
"""

from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.notebook.models import NotebookEntry
from apps.social.models import Block, Profile, UserList, Visibility


def _user(viewer):
    return viewer if viewer is not None and viewer.is_authenticated else None


def blocked_between(owner_id: int, viewer) -> bool:
    viewer = _user(viewer)
    if viewer is None or viewer.pk == owner_id:
        return False
    return Block.objects.filter(
        Q(blocker_id=owner_id, blocked_id=viewer.pk)
        | Q(blocker_id=viewer.pk, blocked_id=owner_id)
    ).exists()


def is_owner(owner_id: int, viewer) -> bool:
    viewer = _user(viewer)
    return viewer is not None and viewer.pk == owner_id


def can_view_profile(profile: Profile, viewer) -> bool:
    if is_owner(profile.user_id, viewer):
        return True
    if profile.is_hidden or not profile.user.is_active:
        return False
    if profile.profile_visibility == Visibility.PRIVATE:
        return False
    return not blocked_between(profile.user_id, viewer)


def can_view_list(user_list: UserList, viewer) -> bool:
    """Direct access by link: public and unlisted lists qualify."""
    if is_owner(user_list.owner_id, viewer):
        return True
    if user_list.is_hidden or not user_list.owner.is_active:
        return False
    if user_list.visibility == Visibility.PRIVATE:
        return False
    return not blocked_between(user_list.owner_id, viewer)


def lists_on_profile(profile: Profile, viewer) -> QuerySet:
    """Lists shown on a profile page: public ones only (unlisted never listed)."""
    lists = UserList.objects.filter(owner_id=profile.user_id)
    if is_owner(profile.user_id, viewer):
        return lists
    return lists.filter(visibility=Visibility.PUBLIC, is_hidden=False)


def entries_on_profile(profile: Profile, viewer) -> QuerySet:
    """Notebook entries shown on a profile page: entry public AND profile public."""
    entries = NotebookEntry.objects.filter(user_id=profile.user_id)
    if is_owner(profile.user_id, viewer):
        return entries
    if profile.profile_visibility != Visibility.PUBLIC:
        return entries.none()
    return entries.filter(visibility=Visibility.PUBLIC)


def public_raters(media_type: str, tmdb_id: int, viewer) -> QuerySet:
    """'Who rated this': only public entries of public, visible, unblocked profiles."""
    entries = NotebookEntry.objects.filter(
        media_type=media_type,
        tmdb_id=tmdb_id,
        rating_x2__isnull=False,
        visibility=Visibility.PUBLIC,
        user__is_active=True,
        user__profile__profile_visibility=Visibility.PUBLIC,
        user__profile__is_hidden=False,
    ).select_related("user__profile")
    viewer = _user(viewer)
    if viewer is not None:
        blocked = Block.objects.filter(
            Q(blocker=viewer) | Q(blocked=viewer)
        ).values_list("blocker_id", "blocked_id")
        ids = {i for pair in blocked for i in pair} - {viewer.pk}
        entries = entries.exclude(user_id__in=ids)
    return entries
