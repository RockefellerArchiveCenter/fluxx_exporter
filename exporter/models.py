from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse

from .clients import FluxxClient


class User(AbstractUser):
    pass


class FluxxConfig(models.Model):
    name = models.CharField(max_length=100)
    base_url = models.CharField(max_length=255)
    client_id = models.CharField(max_length=100)
    client_secret = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('fluxxconfig_detail', kwargs={'pk': self.pk})

    def save(self):
        """Adds custom logic to fetch document types for Fluxx instance."""
        response = super().save()
        client = FluxxClient(
            self.base_url,
            self.client_id,
            self.client_secret)
        document_types = client.list_rows('model_document_type', field_names=['name', 'id'])

        DocumentType.objects.all().delete()
        for document_type in document_types:
            DocumentType.objects.create(
                fluxx_config=self,
                name=document_type['name'],
                document_id=document_type['id'])
        return response


class SFTPConfig(models.Model):
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=100)
    port = models.IntegerField(default=22)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    remote_dir = models.CharField(max_length=250, default='.')

    def __str__(self):
        return self.name


class AmazonS3Config(models.Model):
    name = models.CharField(max_length=100)
    bucket = models.CharField(max_length=100)
    access_key_id = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=100)
    region = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('amazons3config_detail', kwargs={'pk': self.pk})


class ExportJob(models.Model):
    name = models.CharField(max_length=255)
    fluxx_config = models.ForeignKey(FluxxConfig, on_delete=models.CASCADE)
    export_location = models.CharField(max_length=255)
    export_format = models.CharField(max_length=10, choices=[('json', 'JSON'), ('xml', 'XML'), ('csv', 'CSV')])
    grant_ids = models.TextField(null=True, blank=True)
    amazon_s3_config = models.ForeignKey(AmazonS3Config, on_delete=models.SET_NULL, null=True, blank=True)
    sftp_config = models.ForeignKey(SFTPConfig, on_delete=models.SET_NULL, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('exportjob_detail', kwargs={'pk': self.pk})

    @property
    def grant_request_table(self):
        try:
            return Table.objects.get(export_job=self, name='grant_request')
        except ObjectDoesNotExist:
            return None

    @property
    def related_tables(self):
        return Table.objects.filter(export_job=self).exclude(name='grant_request')


class Table(models.Model):
    name = models.CharField(max_length=100)
    include_in_export = models.BooleanField(default=False)
    export_job = models.ForeignKey(
        ExportJob,
        null=True,
        blank=True,
        on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Field(models.Model):
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='fields')
    name = models.CharField(max_length=100)
    include_in_export = models.BooleanField(default=False)
    related_table = models.ForeignKey(
        Table,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='related_tables')

    def __str__(self):
        return self.name


class Filter(models.Model):
    RELATORS = [
        ("eq", "Equals"),
        ("not-eq", "Is Not Equal"),
        ("lt", "Less Than"),
        ("lte", "Less Than or Equal"),
        ("gt", "Greater Than"),
        ("gte", "Greater Than or Equal"),
        ("null", "Is Null"),
        ("not-null", "Is Not Null"),
        ("range", "Between"),
        ("range-year-cal", "Between Calendar Years"),
        ("yesterday", "Yesterday"),
        ("today", "Today"),
        ("tomorrow", "Tomorrow"),
        ("last-n-days", "Last N Days"),
        ("next-n-days", "Next N Days"),
        ("days-n-ago", "N Days Ago"),
        ("last-week", "Last Week"),
        ("this-week", "This Week"),
        ("next-week", "Next Week"),
        ("last-n-weeks", "Last N Weeks"),
        ("next-n-weeks", "Next N Weeks"),
        ("weeks-n-ago", "N Weeks Ago"),
        ("last-month", "Last Month"),
        ("this-month", "This Month"),
        ("next-month", "Next Month"),
        ("last-n-months", "Last N Months"),
        ("next-n-months", "Next N Months"),
        ("months-n-ago", "N Months Ago"),
        ("last-quarter", "Last Quarter"),
        ("this-quarter", "This Quarter"),
        ("next-quarter", "Next Quarter"),
        ("last-n-quarters", "Last N Quarters"),
        ("next-n-quarters", "Next N Quarters"),
        ("quarters-n-ago", "N Quarters Ago"),
        ("last-year", "Last Year"),
        ("this-year", "This Year"),
        ("next-year", "Next Year"),
        ("last-n-years", "Last N Years"),
        ("next-n-years", "Next N Years"),
        ("years-n-ago", "N Years Ago"),
    ]
    export_job = models.ForeignKey(
        ExportJob,
        on_delete=models.CASCADE,
        related_name='filters')
    field_name = models.CharField(max_length=255)
    relator = models.CharField(max_length=255, choices=RELATORS)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.field_name} {self.relator} {self.value}'


class DocumentType(models.Model):
    name = models.CharField(max_length=255)
    document_id = models.IntegerField()
    fluxx_config = models.ForeignKey(FluxxConfig, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
