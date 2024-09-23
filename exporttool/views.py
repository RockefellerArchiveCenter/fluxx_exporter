
import os
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Entity, Column, ExportedFile
from subprocess import run
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@csrf_exempt
def index(request):
    entities = Entity.objects.all()
    columns = Column.objects.all()
    return render(request, 'exporttool/index.html', {'entities': entities, 'columns': columns})

def about(request):
    return render(request, 'exporttool/about.html')

def filterhelp(request):
    return render(request, 'exporttool/filterhelp.html')

@csrf_exempt
def export_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        folder_path = data.get('folderPath', '')

        if not os.path.exists(folder_path):
            return JsonResponse({'error': 'Invalid folder path'}, status=400)

        # Process the rest of the form data
        checked_columns = data.get('checkedColumns', [])
        filter_value = data.get('filter', '')
        format_value = data.get('format', '')

        print("Checked Columns:", checked_columns)
        print("Filter Value:", filter_value)
        print("Format value:", format_value)
        print(f"Output folder: {folder_path}")

        # Call the exportScript.py script with the data
        run(["python", "exportScript.py", *checked_columns, filter_value, format_value, folder_path])

        return JsonResponse({'success': True, 'folder_path': folder_path})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
