from rest_framework import serializers
from .models import Article, Source, Category, NegotiationStream, Resource
from django.db.models import Count, F


class ArticleDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="title")
    category = serializers.CharField(read_only=True, source="category_id")
    negotiation_stream = serializers.CharField(read_only=True, source="negotiation_stream_id")
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d")

    class Meta:
        model = Article
        fields = ["name","summary",
                  "category_id","category",
                  "negotiation_stream_id", "negotiation_stream",
                  "created_at","url"]

class ArticleSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="title")
    category = serializers.CharField(read_only=True, source="category_id")
    negotiation_stream = serializers.CharField(read_only=True, source="negotiation_stream_id")
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d")

    class Meta:
        model = Article
        fields = ["name","condensed_summary","category","negotiation_stream",
                  "created_at","url"]

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id","name"]


class SourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Source
        fields = "__all__"


class ResourceSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = ["name","children"]

    def get_children(self, obj):
        return Article.objects\
            .filter(source_id=obj.source_id)\
            .filter(resource_id=obj.id)\
            .values('category_id','category_id__name')\
            .annotate(size=Count('category_id'))\
            .annotate(id=F('category_id'), name=F('category_id__name'))\
            .values('id','name','size')


class FrontendSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="title")
    children = ResourceSerializer(many=True)

    class Meta:
        model = NegotiationStream
        fields = ["name", "children"]