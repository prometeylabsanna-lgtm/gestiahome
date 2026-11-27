from django.contrib import admin

from src.core import admin_auth  # noqa: F401

admin.site.site_header = "Адміністрування сайту"
admin.site.site_title = "Адміністрування сайту"
admin.site.index_title = "Адміністрування сайту"
