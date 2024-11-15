from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    pass


class FluxxConfig(models.Model):
    name = models.CharField(max_length=100)
    base_url = models.CharField(max_length=255)
    client_id = models.CharField(max_length=100)
    client_secret = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SFTPConfig(models.Model):
    name = models.CharField(max_length=100, default='SFTP Config')
    host = models.CharField(max_length=100)
    port = models.IntegerField(default=22)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    remote_dir = models.CharField(max_length=250, default='.')

    def __str__(self):
        return self.name


class AmazonS3Config(models.Model):
    name = models.CharField(max_length=100, default='S3 Config')
    bucket = models.CharField(max_length=100)
    access_key_id = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=100)
    region = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ExportJob(models.Model):
    name = models.CharField(max_length=255)
    fluxx_config = models.ForeignKey(FluxxConfig, on_delete=models.CASCADE)
    export_location = models.CharField(max_length=255)
    export_format = models.CharField(max_length=10, choices=[('json', 'JSON'), ('xml', 'XML'), ('csv', 'CSV')])
    filter_string = models.CharField(max_length=1000, null=True, blank=True)
    amazon_s3_config = models.ForeignKey(AmazonS3Config, on_delete=models.SET_NULL, null=True, blank=True)
    sftp_config = models.ForeignKey(SFTPConfig, on_delete=models.SET_NULL, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('exportjob_detail', kwargs={'pk': self.pk})


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
