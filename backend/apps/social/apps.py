from django.apps import AppConfig


class SocialConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.social"
    verbose_name = "Social"

    def ready(self):
        # Include profile, lists and share links in the account data export (KVKK/GDPR).
        from apps.accounts.services import EXPORT_SECTIONS
        from apps.social.services import export_social

        EXPORT_SECTIONS["social"] = export_social
