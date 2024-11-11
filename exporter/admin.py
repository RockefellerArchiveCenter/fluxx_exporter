from django.contrib import admin

from .models import Column, Entity, FluxxConfig, S3Config, User

admin.site.register(Entity)
admin.site.register(Column)
admin.site.register(User)
admin.site.register(FluxxConfig)
admin.site.register(S3Config)
