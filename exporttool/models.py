
from django.db import models
from django.contrib.auth.models import User
import os

# Existing models

class UserModel(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content = models.TextField()

    def __str__(self):
        return self.title

class Entity(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Column(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class FluxxConfig(models.Model):
    name = models.CharField(max_length=100)
    instance = models.CharField(max_length=100)
    clientId = models.CharField(max_length=100)
    clientSecret = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class sftpConfig(models.Model):
    name = models.CharField(max_length=100, default='SFTP Config')
    host = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    directory = models.CharField(max_length=250, default='.')

    def __str__(self):
        return self.name

class s3Config(models.Model):
    name = models.CharField(max_length=100, default='S3 Config')
    bucket = models.CharField(max_length=100)
    accessKey = models.CharField(max_length=100)
    secretKey = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# New model for handling file uploads

def user_directory_path(instance, filename):
    # Files will be uploaded to MEDIA_ROOT/uploads/user_<id>/<filename>
    return 'uploads/user_{0}/{1}'.format(instance.user.id, filename)

class ExportedFile(models.Model):
    file = models.FileField(upload_to=user_directory_path)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
