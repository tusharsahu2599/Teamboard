from django.contrib import admin

from .models import Company, KBEntry, QueryLog

admin.site.register(Company)
admin.site.register(KBEntry)
admin.site.register(QueryLog)
