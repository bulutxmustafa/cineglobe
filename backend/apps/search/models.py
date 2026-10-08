"""Search models: LLM usage accounting for the cost guard (plan §3.10)."""

from django.db import models


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
