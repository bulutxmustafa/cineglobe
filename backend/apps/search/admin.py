"""Admin view of LLM usage with today's / this month's cost totals (plan §3.10)."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib import admin
from django.db.models import Count, Q, Sum

from apps.search import cost_guard
from apps.search.models import LLMUsageLog


def usage_summary(since: datetime) -> dict:
    return LLMUsageLog.objects.filter(created_at__gte=since).aggregate(
        calls=Count("id"),
        failed=Count("id", filter=~Q(outcome=LLMUsageLog.Outcome.OK)),
        input_tokens=Sum("input_tokens"),
        output_tokens=Sum("output_tokens"),
        cost_usd=Sum("cost_usd"),
    )


@admin.register(LLMUsageLog)
class LLMUsageLogAdmin(admin.ModelAdmin):
    change_list_template = "admin/search/llmusagelog/change_list.html"
    list_display = (
        "created_at",
        "provider",
        "model",
        "call_type",
        "outcome",
        "input_tokens",
        "output_tokens",
        "cost_usd",
    )
    list_filter = ("provider", "call_type", "outcome", "model")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        tz = ZoneInfo(settings.QUOTA_TIME_ZONE)
        today = cost_guard.local_today()
        start_of_day = datetime.combine(today, time.min, tz)
        start_of_month = start_of_day.replace(day=1)
        extra_context = {
            **(extra_context or {}),
            "usage_today": usage_summary(start_of_day),
            "usage_month": usage_summary(start_of_month),
            "daily_budget_usd": settings.LLM_DAILY_BUDGET_USD,
            "spent_today_usd": cost_guard.spent_today_usd(),
        }
        return super().changelist_view(request, extra_context=extra_context)
