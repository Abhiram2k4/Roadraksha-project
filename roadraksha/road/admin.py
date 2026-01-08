from django.contrib import admin

# Register your models here.
from .models import AuthorityProfile, AdminUser, Report

admin.site.register(AuthorityProfile)
admin.site.register(AdminUser)
admin.site.register(Report)