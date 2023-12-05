from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Caller, Game, User

admin.site.register(User, UserAdmin)

admin.site.register(Caller)
admin.site.register(Game)
