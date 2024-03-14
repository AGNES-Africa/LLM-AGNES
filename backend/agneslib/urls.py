from django.urls import path
from .views import ArticleListAPIView, FrontendGroupView, GenderArticleListAPIView, AgricultureArticleListAPIView, ArticleDetailAPIView

urlpatterns = [
    path('articles', ArticleListAPIView.as_view(), name="articles"),
    path('db_hierarchy', FrontendGroupView.as_view(), name="db_hierarchy"),
    path('article/<pk>', ArticleDetailAPIView.as_view(), name="article_detailed"),
    path('gender/articles', GenderArticleListAPIView.as_view(), name="gender_articles"),
    path('agriculture/articles', AgricultureArticleListAPIView.as_view(), name="agriculture_articles")
]