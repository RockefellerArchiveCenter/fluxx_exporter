from django.core.management.base import BaseCommand, CommandError
from exporter.models import Column as Column
from exporter.models import Entity as Entity
import csv
    
class Command(BaseCommand):
	help = "This command imports a fluxx entity csv and creates columns and entities from the Fluxx glossary csv file. The syntax is python manage.py input_csv filename"
	
	#require filename to be passed as an argument
	#todo - allow paths as well
	def add_arguments(self, parser):
		parser.add_argument('file', type=str)

	def test_csv(self, file):
		try:
			#todo - put a real csv test/validation here
			dialect = csv.Sniffer().sniff(csvfile.read(1024))
		except:
			print("File does not appear to be a csv.")

	def handle(self, *args, **options):

		with open(options['file'], newline='') as csvfile:
			self.test_csv(options['file']
				)

			csvreader = csv.reader(csvfile)
		    
		    #skip first three rows of Fluxx glossary report csv
			next(csvreader)
			next(csvreader)
			next(csvreader)
		    
		    #this creates two lists; one of all the Entities, and one of all the Entities and Columns with the Entities formatted lower case and with underscores
			EntitiesList = []
		 
			EntitiesAndColumnsList = []
			for row in csvreader:
				EntitiesAndColumnsList.append([row[0].lower().replace(" ", "_"), row[1]])
				if row[0] not in EntitiesList:
					EntitiesList.append(row[0])
		            
		    #print(EntitiesList)
			print(EntitiesAndColumnsList)
		    
		    #to do: get this into the database

