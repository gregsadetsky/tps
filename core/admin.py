from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CallSession, Round, User

admin.site.register(User, UserAdmin)

admin.site.register(CallSession)
admin.site.register(Round)
