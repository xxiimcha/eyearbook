from django.shortcuts import render, get_object_or_404, redirect
from .models import Batch, Graduate, Account,  Yearbook, GraduateTracerForm
from django.db.models import Count
from itertools import groupby
from django.views.decorators.http import require_POST
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
from collections import defaultdict
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
from django.utils.timezone import now
from django.db.models.functions import TruncMonth

def landing_page(request):
    return render(request, 'main/landing.html')  # Make sure the template exists

def normalize_key(key):
    # Remove carriage returns and extra whitespace for consistent comparison
    return '\n'.join([line.strip() for line in key.replace('\r', '').strip().splitlines() if line.strip()])


def student_login_view(request):
    error = None

    if request.method == 'POST':
        pasted_key = request.POST.get('private_key', '')

        if not pasted_key.strip():
            error = "Please paste your RSA private key."
        else:
            pasted_clean = normalize_key(pasted_key)

            for account in Account.objects.select_related('graduate').all():
                db_key = normalize_key(account.private_key)

                if pasted_clean == db_key:
                    request.session['account_id'] = account.id
                    request.session['graduate_id'] = account.graduate.id
                    return redirect('profile_page', account_id=account.id)

            error = "Invalid RSA Private Key."

    return render(request, 'main/student_login.html', {'error': error})

def profile_view(request, account_id):
    account = get_object_or_404(Account.objects.select_related('graduate__batch'), id=account_id)
    graduate = account.graduate
    batch = graduate.batch

    batchmates = (
        Graduate.objects.filter(batch=batch)
        .exclude(id=graduate.id)
        .select_related("batch")
    )

    context = {
        "graduate": graduate,
        "batch": f"{batch.from_year}-{batch.to_year} ({batch.batch_type})",
        "photo_url": graduate.photo.url if graduate.photo else None,
        "batchmates": batchmates,
    }
    return render(request, "main/profile_page.html", context)

def update_profile(request):
    graduate_id = request.session.get('graduate_id')

    if not graduate_id:
        return redirect('student_login')  # or any error page

    graduate = get_object_or_404(Graduate, id=graduate_id)

    if request.method == 'POST':
        graduate.email = request.POST.get('email')
        graduate.contact = request.POST.get('contact')
        graduate.address = request.POST.get('address')
        graduate.ambition = request.POST.get('ambition')
        graduate.save()
        messages.success(request, 'Profile updated successfully.')

        return redirect('profile_page', account_id=graduate.account.id)

    return redirect('profile_page', account_id=graduate.account.id)

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
    batch_records = Batch.objects.values("id", "from_year", "to_year", "batch_type").distinct()
    batch_data = {}

    for record in batch_records:
        year_range = f"{record['from_year']} - {record['to_year']}"
        batch_data.setdefault(year_range, []).append({
            "id": record["id"],
            "type": record["batch_type"]
        })

    graduate_data = None
    graduate = None
    submitted = False
    selected_batch_list = []

    if account_id:
        account = get_object_or_404(Account, id=account_id)
        graduate = account.graduate
        batch_display = f"{graduate.batch.from_year} - {graduate.batch.to_year}"
        full_name_combined = f"{graduate.first_name} {graduate.middle_name or ''} {graduate.last_name}".strip()

        submitted = GraduateTracerForm.objects.filter(
            full_name__icontains=full_name_combined,
            mobile_number=graduate.contact
        ).exists()

        graduate_data = {
            "full_name": full_name_combined,
            "mobile_number": graduate.contact,
            "address": graduate.address,
            "course": graduate.course,
            "batch_id": graduate.batch.id,
            "batch_display": batch_display
        }

        selected_batch_list = batch_data.get(batch_display, [])

    if request.method == "POST" and graduate and not submitted:
        data = request.POST

        GraduateTracerForm.objects.create(
            full_name=data.get('full_name'),
            address=data.get('address'),
            mobile_number=data.get('mobile_number'),
            civil_status=data.get('civil_status'),
            birthday=data.get('birthday'),
            region=data.get('region'),
            sex=data.get('sex'),
            province=data.get('province'),
            residence_location=data.get('residence_location'),
            degree=data.get('degree'),
            specialization=data.get('specialization'),
            college_name=data.get('college_name'),
            year_graduated=data.get('year_graduated'),
            honors=data.get('honors'),
            exam_passed=data.get('exam_passed'),
            exam_date=data.get('exam_date') or None,
            exam_rating=data.get('exam_rating'),
            undergrad_reasons=','.join(data.getlist('undergrad_reasons')),
            grad_reasons=','.join(data.getlist('grad_reasons')),
            grad_reasons_other=data.get('grad_reasons_other'),
            trainings=data.get('trainings'),
            advance_reason=data.get('advance_reason'),
            employment_status=data.get('employment_status'),
            unemployed_reasons=','.join(data.getlist('unemployed_reasons')),
            occupation=data.get('occupation'),
            business_line=data.get('business_line'),
            work_location=','.join(data.getlist('work_location')),
            first_job=data.get('first_job'),
            stay_reasons=','.join(data.getlist('stay_reasons')),
            job_course_relation=data.get('job_course_relation'),
            job_finding_time=data.get('job_finding_time'),
            job_accept_reasons=','.join(data.getlist('job_accept_reasons[]')),
            job_change_reasons=','.join(data.getlist('job_change_reasons[]')),
            first_job_duration=data.get('first_job_duration'),
            first_job_position=data.get('first_job_position'),
            current_job_position=data.get('current_job_position'),
            current_employer_name=data.get('current_employer_name'),
            current_employer_address=data.get('current_employer_address'),
            current_supervisor_name=data.get('current_supervisor_name'),
            current_employer_contact=data.get('current_employer_contact'),
            initial_salary=data.get('initial_salary'),
            curriculum_relevance=data.get('curriculum_relevance'),
            college_competencies=','.join(data.getlist('college_competencies[]')),
            other_skills_specified=data.get('other_skills_specified'),
            data_privacy=bool(data.get('data_privacy')),
            batch_type=data.get('batch_type')
        )

        submitted = True

    context = {
        "batch_years": batch_data,
        "graduate_data": graduate_data,
        "account_id": account_id,
        "submitted": submitted,
        "selected_batch_list": selected_batch_list,
    }

    return render(request, "main/form.html", context)

@login_required
def dashboard_view(request):
    selected_batch_id = request.GET.get('batch_id')
    batches = Batch.objects.all().order_by('-to_year')

    total_batches = batches.count()
    total_graduates = Graduate.objects.count()
    total_records = Yearbook.objects.count()
    current_batch = f"{batches.first().from_year}-{batches.first().to_year}" if batches else "N/A"

    recent_submissions = Yearbook.objects.select_related('graduate').order_by('-id')[:5]

    # Batch summary for bar chart
    batch_data = (
        Yearbook.objects
        .values('graduate__batch__from_year', 'graduate__batch__to_year')
        .annotate(count=Count('id'))
        .order_by('graduate__batch__from_year')
    )
    batch_labels = [f"{b['graduate__batch__from_year']}-{b['graduate__batch__to_year']}" for b in batch_data]
    batch_counts = [b['count'] for b in batch_data]

    # Course-wise breakdown
    course_labels = []
    course_counts = []

    if selected_batch_id:
        selected_batch = Batch.objects.get(id=selected_batch_id)
        course_data = (
            Graduate.objects
            .filter(batch_id=selected_batch_id)
            .values('course')
            .annotate(count=Count('id'))
            .order_by('course')
        )
        course_labels = [c['course'] for c in course_data]
        course_counts = [c['count'] for c in course_data]
    else:
        selected_batch = None

    status_counts = [
        Yearbook.objects.filter(status="pending").count(),
        Yearbook.objects.filter(status="approved").count(),
        Yearbook.objects.filter(status="rejected").count()
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
        "course_labels": json.dumps(course_labels),
        "course_counts": json.dumps(course_counts),
        "batches": batches,
        "selected_batch_id": int(selected_batch_id) if selected_batch_id else None,
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


def graduate_list(request):
    batches = Batch.objects.all().order_by('-to_year')
    graduates_by_batch_course = {}

    for batch in batches:
        courses = defaultdict(list)
        graduates = Graduate.objects.filter(batch=batch)

        for grad in graduates:
            # Try to attach related yearbook data if it exists
            try:
                grad.yearbook = grad.yearbook  # Access OneToOne relation
            except Yearbook.DoesNotExist:
                grad.yearbook = None
            courses[grad.course].append(grad)

        graduates_by_batch_course[batch] = dict(courses)

    return render(request, 'main/graduates/graduate_list.html', {
        'graduates_by_batch_course': graduates_by_batch_course
    })

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
        plain_private_key = private_key_pem.decode()

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


@require_POST
def delete_graduate(request, graduate_id):
    graduate = get_object_or_404(Graduate, id=graduate_id)
    
    # Optionally delete the account record too, if it's a OneToOne or FK
    try:
        account = Account.objects.get(graduate=graduate)
        account.delete()
    except Account.DoesNotExist:
        pass

    graduate.delete()
    messages.success(request, "Graduate and account deleted successfully.")
    return redirect('account_list')  # Change this to your actual list view name

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

    # Chart 1: Submissions per Batch
    batch_labels = []
    batch_counts = []
    batches = Batch.objects.all()
    for batch in batches:
        count = Yearbook.objects.filter(graduate__batch=batch).count()
        if count > 0:
            label = f"{batch.from_year}-{batch.to_year} {batch.batch_type}"
            batch_labels.append(label)
            batch_counts.append(count)

    # Chart 2: Graduates per Course
    course_data = Graduate.objects.values('course').annotate(count=Count('id')).order_by('course')
    course_labels = [entry['course'] for entry in course_data]
    course_counts = [entry['count'] for entry in course_data]

    # Chart 3: Monthly Submission Trends (based on submitted_at)
    current_year = now().year
    monthly_data = (
        Yearbook.objects
        .filter(submitted_at__year=current_year)
        .annotate(month=TruncMonth('submitted_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    month_labels = [entry['month'].strftime('%b') for entry in monthly_data]
    monthly_submission_counts = [entry['count'] for entry in monthly_data]

    context = {
        "total_graduates": total_graduates,
        "total_submitted": total_submitted,
        "total_pending": total_pending,
        "batch_labels": batch_labels,
        "batch_counts": batch_counts,
        "course_labels": course_labels,
        "course_counts": course_counts,
        "month_labels": month_labels,
        "monthly_submission_counts": monthly_submission_counts,
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

        # Clean public key (strip headers for DB)
        public_key_clean = public_key_pem.decode().replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").replace("\n", "")
        private_key_plain = private_key_pem.decode()  # Plaintext private key

        # Save Account with plaintext private key
        Account.objects.create(
            graduate=graduate,
            public_key=public_key_clean,
            private_key=private_key_plain
        )

        # Send email with keys
        subject = 'Your eYearbook Access Keys'
        message = f"""
Hello {first_name} {last_name},

Thank you for registering in the eYearbook system.

Below are your RSA access keys. Keep them safe:

------------------------------
🔑 Public Key:
{public_key_pem.decode()}

🔒 Private Key:
{private_key_plain}
------------------------------

The private key is confidential and will be required for secure access.

Best regards,  
eYearbook Admin Team
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False
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

        imported = 0
        skipped = []

        for index, row in enumerate(reader, start=1):
            batch_id = row.get('batch_id')

            try:
                batch = Batch.objects.get(id=batch_id)
            except Batch.DoesNotExist:
                skipped.append(f"Row {index} skipped (batch_id {batch_id} does not exist).")
                continue

            graduate = Graduate.objects.create(
                first_name=row['first_name'],
                middle_name=row.get('middle_name', ''),
                last_name=row['last_name'],
                course=row['course'],
                email=row['email'],
                contact=row['contact'],
                address=row['address'],
                batch=batch,
            )

            # RSA key generation (plaintext storage as per your request)
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
                private_key=private_key_pem.decode()
            )

            imported += 1

        messages.success(request, f"{imported} students successfully imported.")
        if skipped:
            messages.warning(request, "Some rows were skipped:\n" + "\n".join(skipped))

        return redirect("account_list")

    return render(request, "main/accounts/import_student.html")

def records_view(request):
    graduates = Graduate.objects.filter(yearbook__isnull=False).select_related('yearbook').order_by('-yearbook__submitted_at')
    return render(request, 'main/records.html', {'graduates': graduates})

def user_management(request):
    users = User.objects.filter(is_staff=True)
    return render(request, 'main/admin/user_management.html', {'users': users})

def add_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST.get('email', '')
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_staff = True
            user.save()
            messages.success(request, 'Admin user added successfully.')
    return redirect('user_management')


def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        if request.POST.get('password'):
            user.set_password(request.POST.get('password'))
        user.save()
        messages.success(request, 'User updated successfully.')
        return redirect('user_management')
    
    return render(request, 'edit_user.html', {'user': user})


def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.delete()
        messages.success(request, 'User deleted successfully.')
    else:
        messages.error(request, 'Invalid request method.')
    
    return redirect('user_management')