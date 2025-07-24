import getpass

from django.core.management.base import BaseCommand

from exporter.models import User


class Command(BaseCommand):
    help = "Creates superuser if none exists."

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            username = input("Enter username for superuser: ")
            password = getpass.getpass("Enter password for superuser: ")
            User.objects.create_superuser(
                username=username,
                password=password
            )
