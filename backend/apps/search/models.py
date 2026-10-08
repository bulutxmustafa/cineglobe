"""Search models: LLM usage accounting and daily counters for the cost guard (plan §3.10)."""

from django.db import models
from django.db.models import F


class DailyCounter(models.Model):
    """A per-day integer counter shared by every server instance (plan v1.8).

    Serverless functions share no memory, so quota and spend counters live in
    the database. Increments are single UPDATE statements, so two concurrent
    requests can never both take the last unit of a quota.
    """

    key = models.CharField(max_length=120)
    day = models.DateField()
    value = models.BigIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["key", "day"], name="uniq_counter_key_day")
        ]
        indexes = [models.Index(fields=["day"])]

    def __str__(self) -> str:
        return f"{self.day} {self.key}={self.value}"

    @classmethod
    def get(cls, key: str, day) -> int:
        return (
            cls.objects.filter(key=key, day=day).values_list("value", flat=True).first()
            or 0
        )

    @classmethod
    def add(cls, key: str, day, amount: int = 1) -> None:
        cls.objects.get_or_create(key=key, day=day)
        cls.objects.filter(key=key, day=day).update(value=F("value") + amount)

    @classmethod
    def add_if_below(cls, key: str, day, limit: int, amount: int = 1) -> bool:
        """Atomically add `amount` only if the result stays within `limit`."""
        cls.objects.get_or_create(key=key, day=day)
        updated = cls.objects.filter(
            key=key, day=day, value__lte=limit - amount
        ).update(value=F("value") + amount)
        return updated == 1


class LLMUsageLog(models.Model):
    """One row per LLM API call. Holds no personal data: no query text, user or IP."""

    class CallType(models.TextChoices):
        PARSE = "parse", "Query parsing"
        EXPLAIN = "explain", "Explanation"

    class Outcome(models.TextChoices):
        OK = "ok", "OK"
        UNAVAILABLE = "unavailable", "Unavailable (429/timeout/5xx)"
        BAD_OUTPUT = "bad_output", "Invalid output"
        ERROR = "error", "Other error"

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    provider = models.CharField(max_length=20)
    model = models.CharField(max_length=80)
    call_type = models.CharField(max_length=10, choices=CallType.choices)
    outcome = models.CharField(max_length=12, choices=Outcome.choices)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=12, decimal_places=8, default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "LLM usage log"

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.provider}/{self.call_type} {self.outcome}"
