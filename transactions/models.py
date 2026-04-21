from django.db import models
from django.utils import timezone


class Transaction(models.Model):
    class Type(models.TextChoices):
        INCOME = "income"
        EXPENSE = "expense"

    class FinancialNature(models.TextChoices):
        SPENDING = "spending"
        SAVING = "saving"
        INVESTMENT = "investment"

    id = models.CharField(max_length=20, primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    category = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=Type.choices)
    description = models.CharField(max_length=255, blank=True, default="")
    financial_nature = models.CharField(
        max_length=20,
        choices=FinancialNature.choices,
        default=FinancialNature.SPENDING,
    )
    budget_group_id = models.CharField(max_length=100, null=True, blank=True)
    goal_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def financialNature(self):
        return self.financial_nature

    @property
    def budgetGroupId(self):
        return self.budget_group_id

    @property
    def goalId(self):
        return self.goal_id

    class Meta:
        ordering = ["-date"]


class FinancialGoal(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    is_archived = models.BooleanField(default=False)

    @property
    def targetAmount(self):
        return self.target_amount

    @property
    def createdAt(self):
        return self.created_at

    @property
    def isArchived(self):
        return self.is_archived

    class Meta:
        ordering = ["-created_at"]


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
