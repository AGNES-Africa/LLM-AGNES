from django.urls import path
from .views import ArticleListAPIView, FrontendGroupView, GenderArticleListAPIView, AgricultureArticleListAPIView, ArticleDetailAPIView

urlpatterns = [
    path('db_hierarchy', FrontendGroupView.as_view(), name="db_hierarchy"),
    path('category/<category_id>', ArticleListAPIView.as_view(), name="article_list"),
    path('article/<pk>', ArticleDetailAPIView.as_view(), name="article_detailed")
]