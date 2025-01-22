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
