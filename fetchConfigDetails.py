# fetch_config.py
import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exporttool.settings')
django.setup()

from exporttool.models import FluxxConfig, sftpConfig, s3Config

def fetch_fluxx_configs(fluxx_config_name):
    try:
        fluxx_config = FluxxConfig.objects.get(name=fluxx_config_name)
        return fluxx_config.instance, fluxx_config.clientId, fluxx_config.clientSecret
    except FluxxConfig.DoesNotExist:
        raise ValueError(f"Config '{fluxx_config_name}' not found")

def fetch_sftp_configs(sftp_config_name):
    try:
        sftp_config = sftpConfig.objects.get(name=sftp_config_name)
        return sftp_config.host, sftp_config.username, sftp_config.password, sftp_config.directory
    except sftpConfig.DoesNotExist:
        raise ValueError(f"Config '{sftp_config_name}' not found")

def fetch_s3_configs(s3_config_name):
    try:
        s3_config_name = s3Config.objects.get(name=s3_config_name)
        return s3_config_name.bucket, s3_config_name.accessKey, s3_config_name.secretKey
    except s3Config.DoesNotExist:
        raise ValueError(f"Config '{s3_config_name}' not found")