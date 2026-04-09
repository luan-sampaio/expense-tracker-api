from django.db import models


class Transaction(models.Model):
    class Type(models.TextChoices):
        INCOME = "income"
        EXPENSE = "expense"

    id = models.CharField(max_length=20, primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    category = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=Type.choices)
    description = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
