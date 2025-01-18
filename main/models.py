from django.db import models

class Batch(models.Model):
    from_year = models.CharField(max_length=4)
    to_year = models.CharField(max_length=4)
    batch_type = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.from_year} - {self.to_year} ({self.batch_type})"
