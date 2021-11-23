from django.contrib import admin

from categories.models import Categories


class CategoriesAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "date",
        "order",
        "title",
        "description",
        "image_src",
        "method",
        "is_public",
        "is_active",
    ]
    search_fields = ["order"]


admin.site.register(Categories, CategoriesAdmin)
