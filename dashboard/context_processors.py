from .models import Branch, Profile, Sale, Customer
from itertools import chain
from operator import attrgetter
from django.utils.timezone import make_aware
from datetime import datetime
from datetime import timedelta
from django.utils import timezone
from .models import Branch, Sale, SaleItem

def sales_analytics(request):
    now = timezone.now()
    last_24_hours = now - timedelta(hours=24)

    analytics_data = []

    branches = Branch.objects.all()
    for branch in branches:
        # Get sales in last 24h for this branch
        sales = Sale.objects.filter(branch=branch, date__gte=last_24_hours)
        sale_ids = sales.values_list('id', flat=True)
        sale_items = SaleItem.objects.filter(sale_id__in=sale_ids)

        total = sum(item.total_price() for item in sale_items)
        # You can customize growth logic; for now it's dummy + or -
        growth = "+39%" if total > 0 else "-9%"
        trend = "success" if total > 0 else "danger"

        analytics_data.append({
            'branch': branch.name,
            'growth': growth,
            'trend': trend,
            'amount': total,
        })

    return {
        'sales_analytics': analytics_data
    }

def recent_updates(request):
    recent_sales = Sale.objects.select_related('customer').order_by('-date')[:3]
    recent_customers = Customer.objects.order_by('-id')[:3]

    # Annotate all items with a common datetime field for sorting
    sale_updates = [{'type': 'sale', 'name': s.customer.name, 'datetime': s.date} for s in recent_sales]
    customer_updates = [{'type': 'customer', 'name': c.name, 'datetime': c.created_at } for c in recent_customers]

    all_updates = sorted(
        chain(sale_updates, customer_updates),
        key=lambda x: x['datetime'],
        reverse=True
    )[:3]

    return {'recent_updates': all_updates}

def user_role(request):
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            return {'role': profile.role}
        except Profile.DoesNotExist:
            return {'role': None}
    return {'role': None}

def branch_list(request):
    return {
        'branches': Branch.objects.all()
    }

def sidebar_context(request):
    if not request.user.is_authenticated:
        return {}

    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return {}

    role = profile.role
    user_branch = profile.branch

    if role == 'manager':
        branches = Branch.objects.filter(id=user_branch.id)
    elif role == 'admin':
        branches = Branch.objects.all()
    else:
        branches = []

    return {
        'role': role,
        'user_branch': user_branch,
        'branches': branches
    }