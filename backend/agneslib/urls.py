from django.urls import path
from .views import ArticleListAPIView, FrontendGroupView, ArticleListAllAPIView, ArticleDetailAPIView

urlpatterns = [
    path('db_hierarchy', FrontendGroupView.as_view(), name="db_hierarchy"),
    path('category/<stream_id>/<category_id>', ArticleListAPIView.as_view(), name="article_list"),
    path('articles', ArticleListAllAPIView.as_view(), name="article_list_all"),
    path('article/<pk>', ArticleDetailAPIView.as_view(), name="article_detailed")
]