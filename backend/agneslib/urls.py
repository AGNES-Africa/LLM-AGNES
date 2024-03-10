from django.urls import path
from .views import ArticleListAPIView, GenderArticleListAPIView, AgricultureArticleListAPIView

urlpatterns = [
    path('articles', ArticleListAPIView.as_view(), name="articles"),
    path('gender/articles', GenderArticleListAPIView.as_view(), name="gender_articles"),
    path('agriculture/articles', AgricultureArticleListAPIView.as_view(), name="agriculture_articles")
]