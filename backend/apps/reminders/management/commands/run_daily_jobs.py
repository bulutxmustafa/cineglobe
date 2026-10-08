"""Run the daily job by hand: python backend/manage.py run_daily_jobs"""

import json

from django.core.management.base import BaseCommand

from apps.reminders.jobs import run_daily


class Command(BaseCommand):
    help = "Refresh reminder release dates, deliver due reminders and tidy up old data."

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(run_daily().as_dict()))
