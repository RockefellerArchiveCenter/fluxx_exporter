from django.contrib import admin
from .models import UserModel

# Register your models here.

from .models import Entity, Column, FluxxConfig, sftpConfig, s3Config

admin.site.register(Entity)
admin.site.register(Column)
admin.site.register(UserModel)
admin.site.register(FluxxConfig)
admin.site.register(sftpConfig)
admin.site.register(s3Config)