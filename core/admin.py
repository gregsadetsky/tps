from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Caller, Round, User

admin.site.register(User, UserAdmin)

admin.site.register(Caller)
admin.site.register(Round)
