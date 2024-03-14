from rest_framework import serializers
from .models import Article, Source, Category, NegotiationStream, Resource

class ArticleSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="title")
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d")

    class Meta:
        model = Article
        fields = ["name","summary","size","category_id","created_at","url"]


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id","name","size"]


class SourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Source
        fields = "__all__"


class ResourceSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = ["name","size","children"]

    def get_children(self, obj):
        qs = Category.objects.filter(source_id=obj.source_id)
        return CategorySerializer(qs, many=True, read_only=True).data


class FrontendSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="title")
    children = ResourceSerializer(many=True)

    class Meta:
        model = NegotiationStream
        fields = ["name", "children"]
