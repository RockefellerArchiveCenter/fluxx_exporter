import json
from subprocess import run

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import Column, Entity

# Create your views here.


@csrf_exempt
def index(request):
    entities = Entity.objects.all()
    columns = Column.objects.all()
    return render(request, 'exporttool/index.html',
                  {'entities': entities, 'columns': columns})


def about(request):
    return render(request, 'exporttool/about.html')


def filterhelp(request):
    return render(request, 'exporttool/filterhelp.html')


@csrf_exempt
def export_data(request):
    if request.method == 'POST':
        # Parse JSON data from the request body
        data = json.loads(request.body)
        checked_columns = data.get('checkedColumns', [])
        filter_value = data.get('filter', '')
        format_value = data.get('format', '')
        relatedEntity = data.get('relatedEntity', [])

        # Process the checked columns and filter value as needed
        print("Checked Columns:", checked_columns)
        print("Filter Value:", filter_value)
        print("Format value:", format_value)
        print("Related Entity:", relatedEntity)

        # Call the exportScript.py script with the data
        run(["python", "exportScript.py", *checked_columns,
            filter_value, format_value, *relatedEntity])

        # Return a success JSON response
        return JsonResponse({'success': True})
    else:
        # Return a 400 Bad Request response if the request method is not POST
        return JsonResponse({'error': 'Invalid request'}, status=400)
