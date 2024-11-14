from django.contrib import admin

from .models import AmazonS3Config, Field, FluxxConfig, Table, User

admin.site.register(Table)
admin.site.register(Field)
admin.site.register(User)
admin.site.register(FluxxConfig)
admin.site.register(AmazonS3Config)
