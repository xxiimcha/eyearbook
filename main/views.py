from django.shortcuts import render, get_object_or_404, redirect
from .models import Batch, Graduate, Account
from .forms import BatchForm, GraduateForm, GraduateEditForm
from django.contrib import messages
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric import padding
import bcrypt

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
        batch = get_object_or_404(Batch, id=batch_id)  # Fetch the batch details
    else:
        graduates = Graduate.objects.all()
        batch = None

    return render(request, 'main/graduates/graduate_list.html', {'graduates': graduates, 'batch_id': batch_id, 'batch': batch})


def add_graduate(request, batch_id):
    # Ensure the batch exists
    batch = get_object_or_404(Batch, id=batch_id)
    
    if request.method == 'POST':
        # Create the graduate
        graduate = Graduate.objects.create(
            first_name=request.POST['first_name'],
            middle_name=request.POST.get('middle_name', ''),
            last_name=request.POST['last_name'],
            course=request.POST['course'],
            email=request.POST['email'],
            contact=request.POST['contact'],
            address=request.POST['address'],
            ambition=request.POST.get('ambition', ''),
            batch=batch,  # Link the graduate to the batch via ForeignKey
            photo=request.FILES.get('photo')  # Handle the uploaded photo
        )

        # Generate RSA keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=1024  # Minimum key size is 1024 bits
        )
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Shorten the public key (removing headers and newlines)
        public_key_clean = public_key_pem.decode().replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").replace("\n", "")

        # Hash the private key
        hashed_private_key = bcrypt.hashpw(private_key_pem, bcrypt.gensalt()).decode()

        # Create an account record
        Account.objects.create(
            graduate=graduate,
            public_key=public_key_clean,
            private_key=hashed_private_key
        )

        # Redirect to the graduate list page for the batch
        return redirect('batch_graduates', batch_id=batch_id)
    
    # Render the add graduate form
    return render(request, 'main/graduates/add_graduate.html', {'batch': batch})

def edit_graduate(request, pk):
    graduate = get_object_or_404(Graduate, pk=pk)

    if request.method == 'POST':
        form = GraduateForm(request.POST, request.FILES, instance=graduate, exclude_batch=True)
        if form.is_valid():
            form.save()
            return redirect('batch_graduates', batch_id=graduate.batch.id)
    else:
        form = GraduateForm(instance=graduate, exclude_batch=True)

    return render(request, 'main/graduates/edit_graduate.html', {'form': form, 'graduate': graduate})

def delete_graduate(request, pk):
    # Get the graduate
    graduate = get_object_or_404(Graduate, pk=pk)
    batch_id = graduate.batch.id if graduate.batch else request.GET.get('batch_id')
    
    # Delete the associated account
    account = Account.objects.filter(graduate=graduate).first()  # Check if the account exists
    if account:
        account.delete()
    
    # Delete the graduate
    graduate.delete()
    messages.success(request, "Graduate and associated account deleted successfully!")
    
    # Redirect to batch-specific graduates page
    return redirect('batch_graduates', batch_id=batch_id)

def batch_graduates(request, batch_id):
    graduates = Graduate.objects.filter(batch_id=batch_id)
    batch = get_object_or_404(Batch, id=batch_id)
    return render(request, 'main/graduates/graduate_list.html', {'graduates': graduates, 'batch': batch})

def account_list(request):
    accounts = Account.objects.select_related('graduate')  # Use select_related for efficiency
    return render(request, 'main/accounts/account_list.html', {'accounts': accounts})
