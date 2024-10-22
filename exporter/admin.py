from django.contrib import admin

from .models import Column, Entity, FluxxConfig, User, s3Config, sftpConfig

# Register your models here.


class EntityAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "related_entity":
            kwargs["queryset"] = Entity.objects.all()
            kwargs["empty_label"] = "Base"
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Entity, EntityAdmin)
admin.site.register(Column)
admin.site.register(User)
admin.site.register(FluxxConfig)
admin.site.register(sftpConfig)
admin.site.register(s3Config)
