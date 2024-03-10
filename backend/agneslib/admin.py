from django.contrib import admin
from .models import Article, Source, Category, NegotiationStream

class ArticleModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'summary')
    list_per_page = 20

admin.site.register(Article, ArticleModelAdmin)
admin.site.register(Source)
admin.site.register(Category)
admin.site.register(NegotiationStream)