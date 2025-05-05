import pandas as pd
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.http import HttpResponse
from .forms import UploadFileForm
from .models import UploadedFile

def index(request):
    form = UploadFileForm()
    files = UploadedFile.objects.all().order_by('-uploaded_at')
    data = None
    summary = ""

    # Handle file upload
    if request.method == 'POST':
        if 'upload' in request.POST:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                UploadedFile.objects.create(file=request.FILES['file'])

        elif 'display' in request.POST:
            file_id = request.POST.get('file_id')
            try:
                selected_file = UploadedFile.objects.get(id=file_id)
                df = pd.read_csv(selected_file.file.path)
                data = df.to_html(classes="table table-bordered", index=False)
            except Exception as e:
                data = f"<p style='color:red;'>Error reading file: {e}</p>"

        elif 'download' in request.POST:
            file_id = request.POST.get('file_id')
            try:
                selected_file = UploadedFile.objects.get(id=file_id)
                df = pd.read_csv(selected_file.file.path)
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{selected_file.file.name}"'
                df.to_csv(response, index=False)
                return response
            except Exception as e:
                return HttpResponse(f"Error downloading file: {e}", content_type="text/plain")

        elif 'email' in request.POST:
            latest = UploadedFile.objects.last()
            if latest:
                df = pd.read_csv(latest.file.path)
                if 'Date' in df.columns:
                    summary = df.groupby('Date').size().to_string()
                    send_mail(
                        "Datewise Summary",
                        summary,
                        'youremail@example.com',
                        ['youremail@example.com']
                    )
                    summary = "Summary emailed successfully."

        elif 'delete' in request.POST:
            date = request.POST.get('date', '').strip()
            restaurant = request.POST.get('restaurant', '').strip().lower()
            latest = UploadedFile.objects.last()
            if latest:
                df = pd.read_csv(latest.file.path)
                df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce', utc=True)
                df['Restaurant Name'] = df['Restaurant Name'].astype(str).str.strip().str.lower()
                df = df[~((df['Order Date'].dt.date == pd.to_datetime(date).date()) &
                          (df['Restaurant Name'] == restaurant))]
                df.to_csv(latest.file.path, index=False)

        elif 'filtered_download' in request.POST:
            date = request.POST.get('date', '').strip()
            restaurant = request.POST.get('restaurant', '').strip().lower()
            latest = UploadedFile.objects.last()
            if latest:
                df = pd.read_csv(latest.file.path)
                df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
                df['Restaurant Name'] = df['Restaurant Name'].astype(str).str.strip().str.lower()
                filtered = df[(df['Order Date'].dt.date == pd.to_datetime(date).date()) &
                              (df['Restaurant Name'] == restaurant)]
                if filtered.empty:
                    return HttpResponse("No matching data found for download.", content_type="text/plain")
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="filtered_data.csv"'
                filtered.to_csv(response, index=False)
                return response

    return render(request, 'dashboard/index.html', {
        'form': form,
        'files': files,
        'data': data,
        'summary': summary
    })
