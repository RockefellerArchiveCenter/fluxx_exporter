from django.core.management.base import BaseCommand, CommandError
from exporter.models import Column as Column
from exporter.models import Entity as Entity
import csv
    
class Command(BaseCommand):
	help = "This command imports a fluxx entity csv and creates columns and entities."
	
	#to do: complete the test function
	def add_arguments(self, parser):
	    parser.add_argument(
            "--test",
            #action="store_true",
            help="Display which Entities and Columns would be written to the db",
        )
	def handle(self, *args, **options):
	    #to do: improve this; path, error handling
	    filename = input("Enter filename in current directory: ")
	    
	    with open(filename, newline='') as csvfile:
		    #test if the file resembles a csv file
		    try: 
		        dialect = csv.Sniffer().sniff(csvfile.read(1024))
		    except:
		        print("File does not appear to be a csv.")
		    else:

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

