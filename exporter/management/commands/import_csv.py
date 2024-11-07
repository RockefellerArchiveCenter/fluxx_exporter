from django.core.management.base import BaseCommand, CommandError
from exporter.models import Column as Column
from exporter.models import Entity as Entity
import csv
from pathlib import Path
    
class Command(BaseCommand):
	help = "This command imports a fluxx entity csv and creates columns and entities from the Fluxx glossary csv file. The syntax is python manage.py input_csv path/to/filename"
	
	#require filename to be passed as an argument
	def add_arguments(self, parser):
		parser.add_argument('file_path', type=Path)

	#test for the attribute of Fluxx glossary csv having Fluxx Glossary in A1
	def test_csv(self, file_path):
		with open(file_path, newline='') as csvfile:
			csvreader = csv.reader(csvfile)	
			for row in csvreader:
				if row[0] == 'Fluxx Glossary':
					return True
				else:
					return False

	def handle(self, *args, **options):

		with open(options['file_path'], newline='') as csvfile:
			if self.test_csv(options['file_path']) == False:
				print("File does not appear to be a Fluxx glossary csv.")
				exit()

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

