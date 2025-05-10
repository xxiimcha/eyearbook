from django.db import models

class Batch(models.Model):
    from_year = models.IntegerField()
    to_year = models.IntegerField()
    batch_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.from_year}-{self.to_year} ({self.batch_type})"


class Graduate(models.Model):
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    email = models.EmailField()
    contact = models.CharField(max_length=15)
    address = models.TextField()
    ambition = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='graduates/photos/', blank=True, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)  # Link to Batch

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Account(models.Model):
    graduate = models.OneToOneField(Graduate, on_delete=models.CASCADE)  # One-to-One relationship with Graduate
    public_key = models.TextField()  # Public Key
    private_key = models.TextField()  # Private Key

    def __str__(self):
        return f"Account for {self.graduate.first_name} {self.graduate.last_name}"
    
from django.utils import timezone

class Yearbook(models.Model):
    graduate = models.OneToOneField(Graduate, on_delete=models.CASCADE)

    civil_status = models.CharField(max_length=20)
    birthday = models.DateField()
    region = models.CharField(max_length=100)
    sex = models.CharField(max_length=20)

    honors = models.CharField(max_length=255, blank=True, null=True)
    grad_reasons = models.TextField(blank=True, null=True)
    other_reason = models.CharField(max_length=255, blank=True, null=True)

    employment_status = models.CharField(max_length=30)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    income = models.CharField(max_length=100, blank=True, null=True)

    agreed_to_privacy = models.BooleanField(default=False)

    # Status of yearbook form
    status = models.CharField(max_length=20, default='Pending')

    # ✅ Add this
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Yearbook Entry for {self.graduate.first_name} {self.graduate.last_name}"
