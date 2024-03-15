from django.shortcuts import render
from django.db.models import Count
from rest_framework import generics
from .models import Article, Category, NegotiationStream
from .serializers import ArticleSerializer, FrontendSerializer#, SourceSerializer, 

class ArticleListAPIView(generics.ListAPIView):

    serializer_class = ArticleSerializer
    paginate_by = 100

    def get_queryset(self):
        return Article.objects\
            .filter(negotiation_stream_id=self.kwargs["stream_id"])\
            .filter(category_id=self.kwargs["category_id"])
    

class FrontendGroupView(generics.ListCreateAPIView):
    
    serializer_class = FrontendSerializer

    def get_queryset(self):
        return NegotiationStream.objects.all()
    
    

class ArticleDetailAPIView(generics.RetrieveAPIView):

    serializer_class = ArticleSerializer

    def get_queryset(self):
        queryset = Article.objects.all()
        return queryset
    

class GenderArticleListAPIView(generics.ListAPIView):

    serializer_class = ArticleSerializer
    paginate_by = 100
    
    def get_queryset(self):
        queryset = Article.objects.filter(negotiation_stream_id=2)
        return queryset.order_by("created_at")
    
    
class AgricultureArticleListAPIView(generics.ListAPIView):

    serializer_class = ArticleSerializer
    paginate_by = 100
    
    def get_queryset(self):
        queryset = Article.objects.filter(negotiation_stream_id=1)
        return queryset.order_by("created_at")
    
# serializer_class = PostSerializer
#     model = serializer_class.Meta.model
#     paginate_by = 100
#     def get_queryset(self):
#         poster_id = self.kwargs['poster_id']
#         queryset = self.model.objects.filter(poster_id=poster_id)
#         return queryset.order_by('-post_time')