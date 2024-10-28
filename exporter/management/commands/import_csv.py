from django.core.management.base import BaseCommand, CommandError
from exporter.models import Column as Column
import csv

class Command(BaseCommand):
	help = "This command imports a fluxx entity csv and creates columns and entities."
	def handle(self, *args, **options):

	#add input for csv file, and/or ability to enter file path and file name

	#define method to check csv format before import

	#test method that prints the csv

		with open('example.csv', newline='') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				print(row)

	#define method to parse csv into proper data structure
	
	#define logging and error reporting

