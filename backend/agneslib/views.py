from django.shortcuts import render
from django.db.models import Count
from rest_framework import generics
from .models import Article, Category, NegotiationStream, Resource
from .serializers import ArticleSerializer, ArticleDetailSerializer, FrontendSerializer

class ArticleListAPIView(generics.ListAPIView):

    serializer_class = ArticleSerializer
    paginate_by = 100

    def get_queryset(self):
        return Article.objects\
            .filter(negotiation_stream_id=self.kwargs["stream_id"])\
            .filter(category_id=self.kwargs["category_id"])


class ArticleListAllAPIView(generics.ListAPIView):

    serializer_class = ArticleSerializer
    paginate_by = 100

    def get_queryset(self):
        return Article.objects\
            .order_by("-created_at")
    

class FrontendGroupView(generics.ListCreateAPIView):
    
    serializer_class = FrontendSerializer

    def get_queryset(self):
        return NegotiationStream.objects.all().order_by('-name')
    

class ArticleDetailAPIView(generics.RetrieveAPIView):

    serializer_class = ArticleDetailSerializer

    def get_queryset(self):
        queryset = Article.objects.all()
        return queryset


# serializer_class = PostSerializer
#     model = serializer_class.Meta.model
#     paginate_by = 100
#     def get_queryset(self):
#         poster_id = self.kwargs['poster_id']
#         queryset = self.model.objects.filter(poster_id=poster_id)
#         return queryset.order_by('-post_time')