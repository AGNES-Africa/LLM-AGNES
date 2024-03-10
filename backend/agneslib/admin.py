from django.contrib import admin
from .models import Article, Source, Category, NegotiationStream

admin.site.register(Article)
admin.site.register(Source)
admin.site.register(Category)
admin.site.register(NegotiationStream)