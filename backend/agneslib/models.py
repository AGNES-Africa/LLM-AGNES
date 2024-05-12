from django.db import models
from django.template.defaultfilters import slugify


class NegotiationStream(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    slug = models.SlugField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "NegotiationStream"

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

    class Meta:
        db_table = "Source"

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign = slugify(self.title)

        if Source.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(Source.objects.all().count())

        self.slug = to_assign
        super(Source, self).save(*args, **kwargs)


class Resource(models.Model):
    title = models.CharField(max_length=200)
    name = models.CharField(max_length=200, blank=True, null=True)
    slug = models.SlugField(max_length=255, blank=True, null=True)
    negotiation_stream_id = models.ForeignKey(to=NegotiationStream, on_delete=models.DO_NOTHING, related_name="children")
    source_id = models.ForeignKey(to=Source, on_delete=models.DO_NOTHING, related_name="linked")

    class Meta:
        db_table = "Resource"

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign = slugify(self.title)

        if Resource.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(Resource.objects.all().count())

        self.slug = to_assign
        super(Resource, self).save(*args, **kwargs)


class Category(models.Model):
    title = models.CharField(max_length=200)
    name = models.CharField(max_length=200, blank=True, null=True)
    summary = models.TextField()
    slug = models.SlugField(max_length=255, blank=True, null=True)
    source_id = models.ForeignKey(to=Source, on_delete=models.DO_NOTHING,  blank=True, null=True, related_name="children")
    
    class Meta:
        db_table = "Category"

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
    crawled_at = models.DateTimeField(blank=True, null=True)
    url = models.URLField()
    negotiation_stream_id = models.ForeignKey(to=NegotiationStream, on_delete=models.DO_NOTHING)
    source_id = models.ForeignKey(to=Source, on_delete=models.DO_NOTHING)
    resource_id = models.ForeignKey(to=Resource, on_delete=models.DO_NOTHING, related_name="articles", blank=True, null=True)
    category_id = models.ForeignKey(to=Category, on_delete=models.DO_NOTHING, related_name="children", blank=True, null=True)


    class Meta:
        db_table = "Article"
        ordering=("-created_at",)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        to_assign = slugify(self.title)

        if Article.objects.filter(slug=to_assign).exists():
            to_assign = to_assign + str(Article.objects.all().count())

        self.slug = to_assign
        super(Article, self).save(*args, **kwargs)