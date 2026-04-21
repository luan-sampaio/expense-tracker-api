from datetime import datetime
from decimal import Decimal

from django.db.models import Count, Q, Sum

from .models import Transaction

ZERO = Decimal("0")


def filter_by_month(queryset, month):
    if not month:
        return queryset

    year, month_number = [int(part) for part in month.split("-")]
    return queryset.filter(date__year=year, date__month=month_number)


def previous_month(month):
    month_date = datetime.strptime(month, "%Y-%m")
    if month_date.month == 1:
        return f"{month_date.year - 1}-12"
    return f"{month_date.year}-{month_date.month - 1:02d}"


def sum_amount(queryset):
    return queryset.aggregate(total=Sum("amount"))["total"] or ZERO


def expense_change_percentage(current_expense, previous_expense):
    if previous_expense == ZERO:
        return None

    change = ((current_expense - previous_expense) / previous_expense) * Decimal("100")
    return change.quantize(Decimal("0.01"))


def list_transactions(filters):
    queryset = filter_by_month(Transaction.objects.all(), filters.month)

    if filters.type:
        queryset = queryset.filter(type=filters.type)

    if filters.category:
        queryset = queryset.filter(category=filters.category)

    if filters.search:
        queryset = queryset.filter(
            Q(description__icontains=filters.search)
            | Q(category__icontains=filters.search)
        )

    count = queryset.count()
    limit = filters.limit
    offset = filters.offset
    results = list(queryset[offset : offset + limit])
    next_offset = offset + limit if offset + limit < count else None
    previous_offset = max(offset - limit, 0) if offset > 0 else None

    return {
        "count": count,
        "limit": limit,
        "offset": offset,
        "next_offset": next_offset,
        "previous_offset": previous_offset,
        "results": results,
    }


def get_transactions_summary(filters):
    queryset = filter_by_month(Transaction.objects.all(), filters.month)
    income_queryset = queryset.filter(type=Transaction.Type.INCOME)
    expense_queryset = queryset.filter(type=Transaction.Type.EXPENSE)

    income = sum_amount(income_queryset)
    expense = sum_amount(expense_queryset)
    biggest_expense = expense_queryset.order_by("-amount", "-date").first()
    top_category = (
        expense_queryset.values("category")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total", "category")
        .first()
    )

    previous_month_comparison = None
    if filters.month:
        previous_expense = sum_amount(
            filter_by_month(Transaction.objects.all(), previous_month(filters.month))
            .filter(type=Transaction.Type.EXPENSE)
        )
        previous_month_comparison = expense_change_percentage(
            expense,
            previous_expense,
        )

    return {
        "balance": income - expense,
        "income": income,
        "expense": expense,
        "biggest_expense": biggest_expense,
        "top_category": top_category,
        "previous_month_comparison": previous_month_comparison,
    }
