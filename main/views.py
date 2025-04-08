from django.shortcuts import render, get_object_or_404, redirect
from .models import Batch, Graduate, Account,  Yearbook
from django.db.models import Count
from itertools import groupby
from .forms import BatchForm, GraduateForm, GraduateEditForm
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric import padding
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
import bcrypt
import json
import csv
from django.contrib.auth import get_user_model  # Import this

def landing_page(request):
    return render(request, 'main/landing.html')  # Make sure the template exists


def student_login_view(request):
    if request.method == "GET":
        return render(request, 'main/student_login.html')

    if request.method == "POST":
        email = request.POST.get('email')
        decrypted_text = request.POST.get('decrypted_text')

        try:
            account = Account.objects.select_related('graduate').get(graduate__email=email)
        except Account.DoesNotExist:
            messages.error(request, "Email not found.")
            return redirect('student_login')

        # Compare decrypted text with stored challenge
        if decrypted_text == request.session.get('challenge'):
            request.session['student_id'] = account.graduate.id
            return redirect('student_dashboard')  # or wherever they should go
        else:
            messages.error(request, "Authentication failed. Invalid private key.")
            return redirect('student_login')
        
        
def get_encrypted_challenge(request):
    email = request.GET.get('email')
    try:
        account = Account.objects.select_related('graduate').get(graduate__email=email)
        pubkey_pem = f"-----BEGIN PUBLIC KEY-----\n{account.public_key}\n-----END PUBLIC KEY-----"
        public_key = serialization.load_pem_public_key(pubkey_pem.encode())

        challenge = base64.b64encode(os.urandom(32)).decode()
        encrypted = public_key.encrypt(
            challenge.encode(),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        request.session['challenge'] = challenge  # Store plain challenge in session

        return JsonResponse({'encrypted': base64.b64encode(encrypted).decode()})

    except Account.DoesNotExist:
        return JsonResponse({'error': 'Invalid email'}, status=400)
    
User = get_user_model()  # Get the User model

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)  # Fetch user by email
            user = authenticate(request, username=user.username, password=password)  # Authenticate using username
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect("dashboard")  # Redirect to dashboard
        else:
            messages.error(request, "Invalid email or password")

    return render(request, "main/login.html")

def form_page(request, account_id=None):
    # Fetch batch data
    batch_records = Batch.objects.values("id", "from_year", "to_year", "batch_type").distinct()
    batch_data = {}

    for record in batch_records:
        year_range = f"{record['from_year']} - {record['to_year']}"
        batch_id = record["id"]
        batch_type = record["batch_type"]
        if year_range not in batch_data:
            batch_data[year_range] = []
        batch_data[year_range].append({"id": batch_id, "type": batch_type})

    graduate_data = None
    graduate = None
    submitted = False

    if account_id:
        account = get_object_or_404(Account, id=account_id)
        graduate = account.graduate
        graduate_data = {
            "full_name": f"{graduate.first_name} {graduate.middle_name or ''} {graduate.last_name}".strip(),
            "mobile_number": graduate.contact,
            "address": graduate.address
        }
        submitted = Yearbook.objects.filter(graduate=graduate).exists()

    # Handle form submission
    if request.method == "POST" and graduate and not submitted:
        civil_status = request.POST.get("civil_status")
        birthday = request.POST.get("birthday")
        region = request.POST.get("region")
        sex = request.POST.get("sex")
        honors = request.POST.get("honors")
        grad_reasons = request.POST.getlist("grad_reasons")
        other_reason = request.POST.get("other_reason", "")
        employment_status = request.POST.get("employment_status")
        job_title = request.POST.get("job_title")
        company_name = request.POST.get("company_name")
        income = request.POST.get("income")
        agreed = bool(request.POST.get("data_privacy"))

        # Save to Yearbook model with status = pending
        Yearbook.objects.create(
            graduate=graduate,
            civil_status=civil_status,
            birthday=birthday,
            region=region,
            sex=sex,
            honors=honors,
            grad_reasons=json.dumps(grad_reasons),
            other_reason=other_reason,
            employment_status=employment_status,
            job_title=job_title,
            company_name=company_name,
            income=income,
            agreed_to_privacy=agreed,
            status="Pending"
        )
        submitted = True  # Prevent re-entry after saving

    context = {
        "batch_years": batch_data,
        "graduate_data": graduate_data,
        "account_id": account_id,
        "submitted": submitted
    }

    return render(request, "main/form.html", context)


@login_required
def dashboard_view(request):
    # Total counts
    total_batches = Batch.objects.count()
    total_graduates = Graduate.objects.count()
    total_records = Yearbook.objects.count()

    # Get most recent batch
    latest_batch = Batch.objects.order_by('-to_year').first()
    current_batch = f"{latest_batch.from_year}-{latest_batch.to_year}" if latest_batch else "N/A"

    # Recent submissions
    recent_submissions = Yearbook.objects.select_related('graduate').order_by('-id')[:5]

    # Submissions per batch (bar chart)
    batch_data = (
        Yearbook.objects
        .values('graduate__batch__from_year', 'graduate__batch__to_year')
        .annotate(count=Count('id'))
        .order_by('graduate__batch__from_year')
    )

    batch_labels = [f"{b['graduate__batch__from_year']}-{b['graduate__batch__to_year']}" for b in batch_data]
    batch_counts = [b['count'] for b in batch_data]

    # Status pie chart
    status_labels = ['pending', 'approved', 'rejected']
    status_counts = [
        Yearbook.objects.filter(status=label).count()
        for label in status_labels
    ]

    context = {
        "total_batches": total_batches,
        "total_graduates": total_graduates,
        "total_records": total_records,
        "current_batch": current_batch,
        "recent_submissions": recent_submissions,
        "batch_labels": json.dumps(batch_labels),
        "batch_counts": json.dumps(batch_counts),
        "status_counts": json.dumps(status_counts),
    }
    return render(request, 'main/dashboard.html', context)

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

def form_page_success(request):
    return render(request, 'main/form_success.html')  # You can name the template anything

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

# Account Module
def account_list(request):
    accounts = Account.objects.select_related('graduate')  # Use select_related for efficiency
    return render(request, 'main/accounts/account_list.html', {'accounts': accounts})

# QR Generation
def get_qr_code_data(request, account_id):
    account = get_object_or_404(Account, id=account_id)
    
    # Generate a short URL containing the public key
    qr_url = request.build_absolute_uri(reverse('view_public_key', args=[account_id]))

    return JsonResponse({"qr_url": qr_url})

# Yearbook Module
def select_batch(request):
    all_batches = Batch.objects.all().order_by('from_year', 'to_year')
    # Use groupby to deduplicate based on `from_year` and `to_year`
    unique_batches = []
    seen = set()
    for batch in all_batches:
        identifier = (batch.from_year, batch.to_year)
        if identifier not in seen:
            unique_batches.append(batch)
            seen.add(identifier)

    return render(request, 'main/yearbook/select_batch.html', {'batches': unique_batches})

# Batch Courses View
def batch_courses(request, from_year, to_year):
    batches = Batch.objects.filter(from_year=from_year, to_year=to_year)
    courses = Graduate.objects.filter(batch__in=batches).values_list('course', flat=True).distinct()
    return render(request, 'main/yearbook/select_course.html', {
        'batches': batches,
        'courses': courses,
        'from_year': from_year,
        'to_year': to_year
    })

# Course Graduates View
def course_graduates(request, from_year, to_year, course):
    batches = Batch.objects.filter(from_year=from_year, to_year=to_year)
    graduates = Graduate.objects.filter(batch__in=batches, course=course)
    return render(request, 'main/yearbook/graduates.html', {'graduates': graduates, 'course': course})


@login_required
def analytics_view(request):
    total_graduates = Graduate.objects.count()
    total_submitted = Yearbook.objects.count()
    total_pending = Yearbook.objects.filter(status="pending").count()

    # Chart data
    batch_labels = []
    batch_counts = []
    batches = Batch.objects.all()
    for batch in batches:
        count = Yearbook.objects.filter(graduate__batch=batch).count()
        if count > 0:
            batch_labels.append(f"{batch.from_year}-{batch.to_year} {batch.batch_type}")
            batch_counts.append(count)

    status_counts = [
        Yearbook.objects.filter(status="pending").count(),
        Yearbook.objects.filter(status="approved").count(),
        Yearbook.objects.filter(status="rejected").count()
    ]

    recent_submissions = Yearbook.objects.select_related("graduate").order_by('-id')[:5]

    context = {
        "total_graduates": total_graduates,
        "total_submitted": total_submitted,
        "total_pending": total_pending,
        "batch_labels": batch_labels,
        "batch_counts": batch_counts,
        "status_counts": status_counts,
        "recent_submissions": recent_submissions,
    }
    return render(request, "main/analytics.html", context)


def add_student_view(request):
    batches = Batch.objects.all()

    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name') or ''
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        course = request.POST.get('course')
        ambition = request.POST.get('ambition', '')
        photo = request.FILES.get('photo')
        batch_id = request.POST.get('batch_id')

        batch = get_object_or_404(Batch, id=batch_id)

        # Save Graduate
        graduate = Graduate.objects.create(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            contact=contact,
            address=address,
            course=course,
            ambition=ambition,
            photo=photo,
            batch=batch
        )

        # Generate RSA keys
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
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

        # Clean public key for storage
        public_key_clean = public_key_pem.decode().replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").replace("\n", "")
        hashed_private_key = bcrypt.hashpw(private_key_pem, bcrypt.gensalt()).decode()

        # Save Account
        Account.objects.create(
            graduate=graduate,
            public_key=public_key_clean,
            private_key=hashed_private_key
        )

        return redirect('account_list')

    return render(request, 'main/accounts/add_student.html', {'batches': batches})


def import_student_view(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect("import_student")

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            graduate = Graduate.objects.create(
                first_name=row['first_name'],
                middle_name=row.get('middle_name', ''),
                last_name=row['last_name'],
                course=row['course'],
                email=row['email'],
                contact=row['contact'],
                address=row['address'],
                batch_id=row['batch_id'],
            )

            private_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
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

            Account.objects.create(
                graduate=graduate,
                public_key=public_key_pem.decode(),
                private_key=bcrypt.hashpw(private_key_pem, bcrypt.gensalt()).decode()
            )

        messages.success(request, "Students successfully imported.")
        return redirect("account_list")

    return render(request, "main/accounts/import_student.html")