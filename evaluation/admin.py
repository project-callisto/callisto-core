from django.contrib import admin
from .models import EvalField

class EvalFieldInline(admin.StackedInline):
    model = EvalField