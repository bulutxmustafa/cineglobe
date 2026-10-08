"""Moderation queue (plan Faz 7C): reports first, actions to restore or remove."""

from django.contrib import admin, messages
from django.utils import timezone

from apps.social.models import (
    Block,
    NotebookShare,
    Profile,
    Report,
    UserList,
    UserListItem,
)


def _targets(reports):
    for item in reports:
        model = Profile if item.target_type == Report.Target.PROFILE else UserList
        target = model.objects.filter(pk=item.target_id).first()
        if target is not None:
            yield item, target


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("__str__", "reporter", "counts", "created_at", "resolved_at")
    list_filter = (
        "target_type",
        "reason",
        "counts",
        ("resolved_at", admin.EmptyFieldListFilter),
    )
    raw_id_fields = ("reporter",)
    actions = ["unhide_target", "delete_target", "suspend_owner", "dismiss"]

    def _resolve(self, request, queryset, what: str) -> None:
        # Resolve every open report about the same targets, not only the selected rows.
        for item in queryset:
            Report.objects.filter(
                target_type=item.target_type,
                target_id=item.target_id,
                resolved_at__isnull=True,
            ).update(resolved_at=timezone.now())
        self.message_user(request, what, messages.SUCCESS)

    @admin.action(description="Restore (unhide) the reported content")
    def unhide_target(self, request, queryset):
        for _, target in _targets(queryset):
            target.is_hidden = False
            target.save(update_fields=["is_hidden"])
        self._resolve(request, queryset, "Restored.")

    @admin.action(description="Delete the reported list / hide the profile for good")
    def delete_target(self, request, queryset):
        for _, target in _targets(queryset):
            if isinstance(target, UserList):
                target.delete()
            else:
                target.is_hidden = True
                target.save(update_fields=["is_hidden"])
        self._resolve(request, queryset, "Removed.")

    @admin.action(description="Suspend the owner's account")
    def suspend_owner(self, request, queryset):
        for _, target in _targets(queryset):
            owner = target.user if isinstance(target, Profile) else target.owner
            owner.is_active = False
            owner.save(update_fields=["is_active"])
        self._resolve(request, queryset, "Suspended.")

    @admin.action(description="Dismiss (no action needed)")
    def dismiss(self, request, queryset):
        self._resolve(request, queryset, "Dismissed.")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "user", "profile_visibility", "is_hidden", "created_at")
    list_filter = ("profile_visibility", "is_hidden")
    search_fields = ("username", "display_name")
    raw_id_fields = ("user",)


class UserListItemInline(admin.TabularInline):
    model = UserListItem
    extra = 0


@admin.register(UserList)
class UserListAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "visibility", "is_hidden", "updated_at")
    list_filter = ("visibility", "is_hidden")
    search_fields = ("title", "slug")
    raw_id_fields = ("owner",)
    inlines = [UserListItemInline]


@admin.register(NotebookShare)
class NotebookShareAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "scope",
        "created_at",
        "expires_at",
        "revoked_at",
        "view_count",
    )
    exclude = ("token_hash",)
    raw_id_fields = ("user",)


admin.site.register(Block)
