from rest_framework import serializers

from categories.models import Categories, CategoryEmail


class CategoryEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryEmail
        fields = ["category", "email"]


class CategoriesSerializer(serializers.ModelSerializer):
    emails = CategoryEmailSerializer(read_only=True)

    class Meta:
        model = Categories
        fields = "__all__"
