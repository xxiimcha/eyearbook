from django.shortcuts import render, get_object_or_404, redirect
from .models import Batch
from .forms import BatchForm

def login_view(request):
    if request.method == 'POST':
        return redirect('dashboard')
    return render(request, 'main/login.html')

def dashboard_view(request):
    context = {
        "total_batches": 12,
        "total_graduates": 2500,
        "current_batch": "2025",
        "total_records": 3000,
    }
    return render(request, 'main/dashboard.html')

def configure(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('configure')  # Redirect to the same page after saving
    else:
        form = BatchForm()

    batches = Batch.objects.all()
    return render(request, 'main/configure.html', {'form': form, 'batches': batches})

def update_batch(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)

    if request.method == "POST":
        batch.from_year = request.POST.get("from_year")
        batch.to_year = request.POST.get("to_year")
        batch.batch_type = request.POST.get("batch_type")
        batch.save()
        return redirect("configure")  # Redirect back to the configure page after updating

    return render(request, "update_batch.html", {"batch": batch})