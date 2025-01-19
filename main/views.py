from django.shortcuts import render, get_object_or_404, redirect
from .models import Batch, Graduate
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
            return redirect('configure')
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
        return redirect("configure")

    return render(request, "update_batch.html", {"batch": batch})


def graduate_list(request, batch_id=None):
    if batch_id:
        graduates = Graduate.objects.filter(batch__id=batch_id) 
    else:
        graduates = Graduate.objects.all()

    return render(request, 'main/graduates/graduate_list.html', {'graduates': graduates, 'batch_id': batch_id})

def add_graduate(request, batch_id):
    # Ensure the batch exists
    batch = get_object_or_404(Batch, id=batch_id)
    
    if request.method == 'POST':
        # Process the form submission
        Graduate.objects.create(
            first_name=request.POST['first_name'],
            middle_name=request.POST.get('middle_name', ''),
            last_name=request.POST['last_name'],
            course=request.POST['course'],
            email=request.POST['email'],
            contact=request.POST['contact'],
            address=request.POST['address'],
            batch=batch,  # Link the graduate to the batch via ForeignKey
            photo=request.FILES.get('photo')  # Handle the uploaded photo
        )
        # Redirect to the graduate list page for the batch
        return redirect('batch_graduates', batch_id=batch_id)
    
    # Render the add graduate form
    return render(request, 'main/graduates/add_graduate.html', {'batch': batch})

def edit_graduate(request, pk):
    graduate = get_object_or_404(Graduate, pk=pk)
    if request.method == 'POST':
        graduate.first_name = request.POST['first_name']
        graduate.middle_name = request.POST.get('middle_name', '')
        graduate.last_name = request.POST['last_name']
        graduate.course = request.POST['course']
        graduate.school_year = request.POST['school_year']
        graduate.email = request.POST['email']
        graduate.contact = request.POST['contact']
        graduate.address = request.POST['address']
        graduate.batch_type = request.POST['batch_type']
        if 'photo' in request.FILES:
            graduate.photo = request.FILES['photo']
        graduate.save()
        messages.success(request, "Graduate updated successfully!")
        return redirect('graduate_list')
    return render(request, 'graduates/edit_graduate.html', {'graduate': graduate})

def delete_graduate(request, pk):
    graduate = get_object_or_404(Graduate, pk=pk)
    graduate.delete()
    messages.success(request, "Graduate deleted successfully!")
    return redirect('graduate_list')

def batch_graduates(request, batch_id):
    graduates = Graduate.objects.filter(batch_id=batch_id)
    batch = get_object_or_404(Batch, id=batch_id)
    return render(request, 'main/graduates/graduate_list.html', {'graduates': graduates, 'batch': batch})
