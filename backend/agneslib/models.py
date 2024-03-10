from django.db import models
from django.template.defaultfilters import slugify

class NegotiationStream(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    slug = models.SlugField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign = slugify(self.title)

        if NegotiationStream.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(NegotiationStream.objects.all().count())

        self.slug = to_assign
        super(NegotiationStream, self).save(*args, **kwargs)


class Source(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    slug = models.SlugField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign = slugify(self.title)

        if Source.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(Source.objects.all().count())

        self.slug = to_assign
        super(Source, self).save(*args, **kwargs)


class Category(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    slug = models.SlugField(max_length=255, blank=True, null=True)
    source_id = models.ForeignKey(to=Source, on_delete=models.DO_NOTHING, default=0)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign = slugify(self.title)

        if Category.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(Category.objects.all().count())

        self.slug = to_assign
        super(Category, self).save(*args, **kwargs)


class Article(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    slug = models.SlugField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    url = models.URLField()
    category_id = models.ForeignKey(to=Category, on_delete=models.DO_NOTHING)
    source_id = models.ForeignKey(to=Source, on_delete=models.DO_NOTHING)
    negotiation_stream_id = models.ForeignKey(to=NegotiationStream, on_delete=models.DO_NOTHING, default=0)

    class Meta:
        ordering=("-created_at",)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign = slugify(self.title)

        if Article.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(Article.objects.all().count())

        self.slug = to_assign
        super(Article, self).save(*args, **kwargs)