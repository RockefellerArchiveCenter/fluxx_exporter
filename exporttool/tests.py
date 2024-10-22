from django.test import TestCase

# Create your tests here.


class ExportTests(TestCase):

    def test_parse_data(self):
        pass

    def test_parse_related_entity(self):
        pass

    def test_parse_filter(self):
        pass

    def test_local_data_export(self):
        pass

    def test_sftp_upload(self):
        pass

    def test_s3_upload(self):
        pass


class FluxxClientTests(TestCase):

    def test_init(self):
        pass

    def test_list_rows(self):
        pass

    def test_download_document(self):
        pass


class FormTests(TestCase):

    def test_export_form(self):
        pass


class ViewTests(TestCase):

    def test_create_export_job(self):
        pass
