"""Social serializers (plan §3.11)."""

from rest_framework import serializers

from apps.catalog.image_utils import poster_url
from apps.notebook.models import NotebookEntry
from apps.social.models import NotebookShare, Profile, Report, UserList, Visibility


class ProfileWriteSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20, required=False)
    display_name = serializers.CharField(
        max_length=40, allow_blank=True, required=False
    )
    bio = serializers.CharField(max_length=200, allow_blank=True, required=False)
    avatar_kind = serializers.ChoiceField(
        choices=Profile.Avatar.choices, required=False
    )
    avatar_poster_path = serializers.RegexField(
        r"^(/[\w.-]{1,120})?$", required=False, allow_blank=True
    )
    profile_visibility = serializers.ChoiceField(
        choices=Visibility.choices, required=False
    )
    show_stats = serializers.BooleanField(required=False)


class OwnProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "username",
            "display_name",
            "bio",
            "avatar_kind",
            "avatar_poster_path",
            "profile_visibility",
            "show_stats",
            "username_changed_at",
            "is_hidden",
        ]


class ListWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=80)
    description = serializers.CharField(
        max_length=500, allow_blank=True, required=False
    )
    is_ranked = serializers.BooleanField(required=False)
    visibility = serializers.ChoiceField(choices=Visibility.choices, required=False)


class ListItemWriteSerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(choices=["movie", "tv"])
    tmdb_id = serializers.IntegerField(min_value=1)
    comment = serializers.CharField(max_length=280, allow_blank=True, required=False)


class ListItemsWriteSerializer(serializers.Serializer):
    items = ListItemWriteSerializer(many=True, max_length=UserList.MAX_ITEMS)


def list_item_data(item) -> dict:
    return {
        "position": item.position,
        "media_type": item.media_type,
        "tmdb_id": item.tmdb_id,
        "title": item.title,
        "year": item.year,
        "poster_url": poster_url(item.poster_path or ""),
        "comment": item.comment,
    }


def list_data(user_list: UserList, with_items: bool = True) -> dict:
    data = {
        "id": user_list.id,
        "slug": user_list.slug,
        "title": user_list.title,
        "description": user_list.description,
        "is_ranked": user_list.is_ranked,
        "visibility": user_list.visibility,
        "item_count": user_list.items.count(),
        "updated_at": user_list.updated_at,
    }
    if with_items:
        data["items"] = [list_item_data(i) for i in user_list.items.all()]
    return data


class ShareCreateSerializer(serializers.Serializer):
    scope = serializers.ChoiceField(
        choices=NotebookShare.Scope.choices, default="ratings"
    )
    statuses = serializers.ListField(
        child=serializers.ChoiceField(choices=NotebookEntry.Status.choices),
        required=False,
        default=list,
    )
    expires_in_days = serializers.IntegerField(
        min_value=1, max_value=365, required=False, allow_null=True
    )


class ShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotebookShare
        fields = [
            "id",
            "scope",
            "statuses",
            "expires_at",
            "revoked_at",
            "view_count",
            "created_at",
        ]


class ReportCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=Report.Target.choices)
    target_id = serializers.IntegerField(min_value=1)
    reason = serializers.ChoiceField(choices=Report.Reason.choices)
    details = serializers.CharField(
        max_length=200, allow_blank=True, required=False, default=""
    )


class BlockSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20)
