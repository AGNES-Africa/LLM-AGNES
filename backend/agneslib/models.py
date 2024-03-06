from django.db import models
from django.template.defaultfilters import slugify


class Category(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    slug = models.SlugField(max_length=255)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign=slugify(self.title)

        if Category.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(Category.objects.all().count())

        self.slug=to_assign()
        super.save(*args, **kwargs)


class Source(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    slug = models.SlugField(max_length=255)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign=slugify(self.title)

        if Source.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(Source.objects.all().count())

        self.slug=to_assign()
        super.save(*args, **kwargs)


class Article(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    slug = models.SlugField(max_length=255)
    created_at = models.DateTimeField()
    url = models.URLField()
    category_id = models.ForeignKey(to=Category, on_delete=models.DO_NOTHING)
    source_id = models.ForeignKey(to=Source, on_delete=models.DO_NOTHING)

    class Meta:
        ordering=("-created_at",)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign=slugify(self.title)

        if Article.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(Article.objects.all().count())

        self.slug=to_assign()
        super.save(*args, **kwargs)