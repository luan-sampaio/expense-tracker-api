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


class SyncOperationLog(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied"
        FAILED = "failed"

    client_operation_id = models.CharField(max_length=100, unique=True)
    operation = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=20, blank=True, default="")
    payload_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=10, choices=Status.choices)
    message = models.CharField(max_length=255, blank=True, default="")
    fields = models.JSONField(default=dict, blank=True)
    server_synced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-server_synced_at"]
