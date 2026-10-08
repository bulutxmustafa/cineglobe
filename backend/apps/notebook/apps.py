from django.apps import AppConfig


class NotebookConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notebook"
    verbose_name = "Film Notebook"

    def ready(self):
        # Include the notebook in the account data export (KVKK/GDPR).
        from apps.accounts.services import EXPORT_SECTIONS
        from apps.notebook.services import export_rows

        EXPORT_SECTIONS["notebook"] = export_rows
