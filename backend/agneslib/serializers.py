from rest_framework import serializers
from .models import Article, Source, Category

class ArticleSerializer(serializers.ModelSerializer):

    class Meta:
        model=Article
        fields="__all__"


class SourceSerializer(serializers.ModelSerializer):

    class Meta:
        model=Source
        fields="__all__"


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model=Category
        fields="__all__"