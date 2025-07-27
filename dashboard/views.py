from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Branch, Sale, Customer,Sale, SaleItem, Expense, BranchProduct, Product
from django.db.models import Sum  # Ensure Expense model is defined
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from decimal import Decimal
from django.views.decorators.http import require_POST, require_http_methods
from django.utils.dateparse import parse_date
from datetime import datetime, date, timedelta
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate
from django.contrib.auth.hashers import make_password
from django.db import transaction
from dashboard.utils.stock_alert import notify_low_stock
from django.db.models import Q
from django.utils.dateparse import parse_date
from math import ceil
from decimal import Decimal, ROUND_HALF_UP
from django.core.paginator import Paginator


REFERRAL_CODE = "UNIQUE2025"

def create_admin_view(request):
    if request.method == "POST":
        ref_code = request.POST.get("ref_code")
        phone = request.POST.get("phone")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if ref_code != REFERRAL_CODE:
            return render(request, 'dashboard/create_admin.html', {'error': 'Invalid referral code'})

        if User.objects.filter(username=username).exists():
            return render(request, 'dashboard/create_admin.html', {'error': 'Username already exists'})
        
        if Profile.objects.filter(phone=phone).exists():
            return render(request, 'dashboard/create_admin.html', {'error': 'Phone number already used'})

        user = User.objects.create(username=username, password=make_password(password))
        Profile.objects.create(user=user, phone=phone, role='admin')

        return render(request, 'dashboard/create_admin.html', {'success': 'Admin created successfully!'})

    return render(request, 'dashboard/create_admin.html')

@login_required
def neworder(request):
    profile = Profile.objects.select_related('branch').get(user=request.user)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Determine branch
            if profile.role == 'admin':
                branch_id = data.get('branch_id')
                if not branch_id:
                    return JsonResponse({'error': 'Admin must select a branch.'}, status=400)
                branch = Branch.objects.get(id=branch_id)
            else:
                if not profile.branch:
                    return JsonResponse({'error': 'Your profile has no branch assigned.'}, status=400)
                branch = profile.branch

            # Customer info
            customer_id = data.get('customer_id')
            customer_name = data.get('customer_name')
            customer_phone = data.get('customer_phone')
            customer_gst = data.get('customer_gst', '')

            if customer_id:
                customer = Customer.objects.get(id=customer_id)
            else:
                if not customer_name or not customer_phone:
                    return JsonResponse({'error': 'Customer name and phone are required.'}, status=400)
                customer, _ = Customer.objects.get_or_create(
                    phone=customer_phone,
                    defaults={'name': customer_name, 'gst_number': customer_gst, 'branch': None}
                )

            items = data.get('items', [])
            if not items:
                return JsonResponse({'error': 'No items provided.'}, status=400)

            product_ids = [int(item['product_id']) for item in items]
            products = Product.objects.in_bulk(product_ids)

            total = float(data.get('total', 0))
            paid = float(data.get('paid', 0))
            payment_method = data.get('payment_method', 'Cash')
            gst_number = customer.gst_number or profile.gst_number or ''

            with transaction.atomic():
                branch_products = {
                    bp.product_id: bp for bp in BranchProduct.objects.select_for_update()
                    .filter(branch=branch, product_id__in=product_ids)
                }

                # ✅ Check stock, fallback for services
                for item in items:
                    product_id = int(item['product_id'])
                    quantity = item['quantity']
                    product = products.get(product_id)

                    if not product:
                        return JsonResponse({'error': f"Product with ID {product_id} not found."}, status=400)

                    # Skip stock check for services
                    if product.is_service:
                        continue

                    bp = branch_products.get(product_id)
                    if not bp:
                        return JsonResponse({'error': f"Product '{product.name}' not available in selected branch."}, status=400)

                    if bp.stock is None or bp.stock < quantity:
                        return JsonResponse({'error': f"Insufficient stock for {product.name}."}, status=400)

                # Create Sale
                sale = Sale.objects.create(
                    customer=customer,
                    branch=branch,
                    staff=profile,
                    amount_paid=paid,
                    gst_number=gst_number,
                    date=timezone.now(),
                    payment_method=payment_method,
                    total_override=total if total > 0 else None
                )

                # Create SaleItems and update stock
                for item in items:
                    product_id = int(item['product_id'])
                    quantity = item['quantity']
                    product = products[product_id]

                    gst_percent = product.gst_percent
                    gst_amount = product.price * gst_percent / 100
                    price_with_gst = product.price + gst_amount

                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        price=price_with_gst,
                        gst_percent=gst_percent,
                        gst_amount=gst_amount
                    )

                    # Only reduce stock if not a service
                    if not product.is_service:
                        bp = branch_products[product_id]
                        bp.stock = F('stock') - quantity
                        bp.save()
                        bp.refresh_from_db()
                        notify_low_stock(bp)

                # 🔢 Compute override subtotal & GST for receipt
                if sale.total_override:
                    override_total = sale.total_override
                    override_subtotal = round(override_total / 1.18, 2)
                    override_gst = round(override_total - override_subtotal, 2)
                else:
                    override_subtotal = None
                    override_gst = None

                return JsonResponse({
                    'message': 'Order placed successfully.',
                    'sale_id': sale.id,
                    'gst_number': sale.gst_number,
                    'date': sale.date.isoformat(),
                    'override_subtotal': override_subtotal,
                    'override_gst': override_gst
                })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # For GET (render page)
    if profile.role == 'admin':
        branches = Branch.objects.all()
        selected_branch_id = None
        customers = Customer.objects.all()
        products = Product.objects.all()
    else:
        branches = []
        selected_branch_id = profile.branch.id if profile.branch else None
        customers = Customer.objects.filter(Q(branch=profile.branch) | Q(branch__isnull=True))
        products = Product.objects.filter(branchproduct__branch=profile.branch).distinct()

    customer_data = [
        {'id': c.id, 'name': c.name, 'phone': c.phone, 'gst': c.gst_number or ''}
        for c in customers
    ]
    product_data = [
        {
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'gst_percent': float(p.gst_percent)
        }
        for p in products
    ]

    return render(request, 'dashboard/new-order.html', {
        'customers': customer_data,
        'products': product_data,
        'branch_id': selected_branch_id,
        'branches': branches,
        'profile': profile
    })

@login_required
def edit_order_page(request, sale_id):
    profile = Profile.objects.select_related('branch').get(user=request.user)
    sale = get_object_or_404(Sale, id=sale_id)

    if profile.role not in ['admin', 'manager']:
        return redirect('dashboard')

    # Only fetch products for the branch
    if profile.role == 'admin':
        products = Product.objects.all()
    else:
        products = Product.objects.filter(branchproduct__branch=profile.branch).distinct()

    items = [
        {
            'product_id': item.product.id,
            'name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.price),
        }
        for item in sale.items.all()
    ]

    context = {
        'sale': sale,
        'items': items,
        'products': [
            {'id': p.id, 'name': p.name, 'price': float(p.price), 'gst_percent': float(p.gst_percent)} for p in products
        ],
        'profile': profile,
    }

    return render(request, 'dashboard/edit-order.html', context)


@require_POST
@login_required
def update_order_data(request, sale_id):
    try:
        profile = request.user.profile
        original_sale = get_object_or_404(Sale, id=sale_id)

        data = json.loads(request.body)
        items = data.get('items', [])
        paid = Decimal(data.get('paid', 0))

        if not items:
            return JsonResponse({'error': 'No items provided.'}, status=400)

        # Archive the original
        original_sale.is_archived = True
        original_sale.save()

        # Calculate subtotal and GST-inclusive total
        product_ids = [int(i['product_id']) for i in items]
        products = Product.objects.in_bulk(product_ids)

        subtotal = Decimal(0)
        total_gst = Decimal(0)

        for item in items:
            product = products[int(item['product_id'])]
            qty = int(item['quantity'])
            base_price = product.price
            gst_percent = product.gst_percent
            gst_amount = (base_price * gst_percent / 100).quantize(Decimal("0.01"))

            subtotal += base_price * qty
            total_gst += gst_amount * qty

        grand_total = subtotal + total_gst

        # Create new sale
        new_sale = Sale.objects.create(
            customer=original_sale.customer,
            branch=original_sale.branch,
            staff=profile,
            amount_paid=paid,
            gst_number=original_sale.gst_number,
            date=timezone.now(),
            previous=original_sale
        )

        for item in items:
            product = products[int(item['product_id'])]
            qty = int(item['quantity'])
            gst_percent = product.gst_percent
            gst_amount = (product.price * gst_percent / 100).quantize(Decimal("0.01"))
            price_with_gst = product.price + gst_amount

            SaleItem.objects.create(
                sale=new_sale,
                product=product,
                quantity=qty,
                price=price_with_gst,
                gst_percent=gst_percent,
                gst_amount=gst_amount
            )

        generate_pdf(new_sale)

        return JsonResponse({
            'message': 'Order updated successfully.',
            'sale_id': new_sale.id,
            'subtotal': str(subtotal),
            'gst_total': str(total_gst),
            'grand_total': str(grand_total)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
@login_required
def print_thermal_receipt(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    items = sale.items.all()

    subtotal = Decimal("0.00")
    gst_total = Decimal("0.00")
    item_totals = []

    # Calculate totals using stored price (inclusive of GST)
    for item in items:
        qty = item.quantity
        gst_percent = item.gst_percent
        price_incl_gst = item.price  # already includes GST

        divisor = Decimal(1) + (gst_percent / 100)
        price_excl_gst = (price_incl_gst / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gst_unit = (price_incl_gst - price_excl_gst).quantize(Decimal("0.01"))

        line_subtotal = price_excl_gst * qty
        line_gst_total = gst_unit * qty
        line_total = price_incl_gst * qty

        item.unit_base = price_excl_gst
        item.unit_gst = gst_unit
        item.line_subtotal = line_subtotal
        item.line_gst = line_gst_total
        item.line_total = line_total

        subtotal += line_subtotal
        gst_total += line_gst_total

        item_totals.append(item)

    total = subtotal + gst_total

    # If offer/override is used, proportionally adjust subtotal and gst_total
    if sale.total_override:
        total = sale.total_override
        ratio = total / (subtotal + gst_total) if (subtotal + gst_total) else Decimal(1)
        subtotal = (subtotal * ratio).quantize(Decimal("0.01"))
        gst_total = (gst_total * ratio).quantize(Decimal("0.01"))

    return render(request, "dashboard/receipt_thermal.html", {
        "sale": sale,
        "items": item_totals,
        "subtotal": subtotal,
        "gst_total": gst_total,
        "total": total,
    })



def generate_pdf(sale):
    items = sale.items.select_related('product').all()

    subtotal = Decimal('0.00')
    gst_total = Decimal('0.00')
    grand_total = Decimal('0.00')

    for item in items:
        product = item.product
        qty = item.quantity
        base_price = product.price
        gst_percent = product.gst_percent
        gst_amount = (base_price * gst_percent / 100).quantize(Decimal("0.01"))

        item.unit_price = base_price
        item.unit_gst = gst_amount
        item.subtotal = base_price * qty
        item.total_gst = gst_amount * qty
        item.total = item.subtotal + item.total_gst

        subtotal += item.subtotal
        gst_total += item.total_gst
        grand_total += item.total

    html = render_to_string("dashboard/receipt_pdf.html", {
        'sale': sale,
        'items': items,
        'subtotal': subtotal,
        'gst_total': gst_total,
        'total': grand_total,
        'branch': sale.branch,
    })

    result = BytesIO()
    pdf_status = pisa.CreatePDF(html, dest=result)

    if not pdf_status.err:
        sale.memo_pdf.save(f"receipt_{sale.id}.pdf", ContentFile(result.getvalue()))
    result.close()


@login_required
def print_receipt(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    printed_on = timezone.now()
    items = sale.items.select_related('product').all()

    subtotal = Decimal('0.00')
    gst_total = Decimal('0.00')
    grand_total = Decimal('0.00')

    for item in items:
        product = item.product
        qty = item.quantity
        base_price = product.price
        gst_percent = product.gst_percent
        gst_amount = (base_price * gst_percent / 100).quantize(Decimal("0.01"))

        item.subtotal = base_price * qty
        item.total_gst = gst_amount * qty
        item.total = item.subtotal + item.total_gst
        item.unit_price = base_price
        item.unit_gst = gst_amount

        subtotal += item.subtotal
        gst_total += item.total_gst
        grand_total += item.total

    # Auto-generate PDF if missing
    if not sale.memo_pdf:
        generate_pdf(sale)

    original_sale = sale.previous if sale.previous else sale
    edit_history = original_sale.edits.exclude(id=sale.id).order_by('-date')

    return render(request, 'dashboard/receipt.html', {
        'sale': sale,
        'items': items,
        'subtotal': subtotal,
        'gst_total': gst_total,
        'total': grand_total,
        'printed_on': printed_on,
        'history': edit_history,
        'original': original_sale if sale != original_sale else None,
        'branch': sale.branch
    })


@login_required
def order_history(request, sale_id):
    original = get_object_or_404(Sale, id=sale_id)
    edits = original.edits.all().order_by('-date')
    return render(request, 'dashboard/order_history.html', {
        'original': original,
        'edits': edits,
    })


@login_required
def delete_order(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    sale.delete()
    messages.success(request, "Order deleted.")
    return redirect('orders')

@login_required
def add_customer_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            phone = data.get('phone')
            gst = data.get('gst', '')

            if not name or not phone:
                return JsonResponse({'error': 'Missing name or phone.'}, status=400)

            customer, created = Customer.objects.get_or_create(
                phone=phone,
                defaults={
                    'name': name,
                    'gst_number': gst,
                    'branch': None  # ✅ Global customer
                }
            )

            return JsonResponse({
                'success': True,
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'gst_number': customer.gst_number
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=405)



@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('products')


def login_view(request):
    if request.method == 'POST':
        input_value = request.POST.get('identifier')
        password = request.POST.get('password')

        user = None

        # Try phone
        try:
            profile = Profile.objects.select_related('user').get(phone=input_value)
            user = profile.user
        except Profile.DoesNotExist:
            # Try username
            try:
                user = User.objects.get(username=input_value)
            except User.DoesNotExist:
                user = None

        if user:
            authenticated_user = authenticate(request, username=user.username, password=password)
            if authenticated_user is not None:
                login(request, authenticated_user)

                # ✅ Only try to get profile *after* login
                try:
                    profile = Profile.objects.get(user=authenticated_user)
                    role = profile.role
                    if role in ['admin', 'manager']:
                        return redirect('dashboard')
                    elif role == 'staff':
                        return redirect('staff_dashboard')
                except Profile.DoesNotExist:
                    # Handle gracefully
                    return render(request, 'dashboard/login.html', {
                        'error': 'User exists but profile not found. Please contact admin.'
                    })

        return render(request, 'dashboard/login.html', {
            'error': 'Invalid phone number / username or password'
        })

    return render(request, 'dashboard/login.html')



def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def branch_dashboard(request):
    profile = Profile.objects.get(user=request.user)

    # Handle selected date and branch
    selected_date_str = request.GET.get('date')
    branch_id = request.GET.get('branch')

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else date.today()
    start_of_month = selected_date.replace(day=1)

    if profile.role == 'staff':
        return redirect('staff_dashboard')

    if profile.role == 'manager':
        branch = profile.branch
    else:
        branch = Branch.objects.filter(id=branch_id).first() if branch_id else None

    # Filter sales/expenses based on role + selected date
    date_sales = Sale.objects.filter(date__date=selected_date)
    month_sales = Sale.objects.filter(date__date__gte=start_of_month)
    date_expenses = Expense.objects.filter(date=selected_date)
    month_expenses = Expense.objects.filter(date__gte=start_of_month)

    if branch:
        date_sales = date_sales.filter(branch=branch)
        month_sales = month_sales.filter(branch=branch)
        date_expenses = date_expenses.filter(branch=branch)
        month_expenses = month_expenses.filter(branch=branch)

    # Totals
    sale_ids = date_sales.values_list('id', flat=True)
    sale_items = SaleItem.objects.filter(sale_id__in=sale_ids)
    total_sales = sum(item.quantity * item.price for item in sale_items)

    total_expenses = date_expenses.aggregate(total=Sum('amount'))['total'] or 0

    month_sale_ids = month_sales.values_list('id', flat=True)
    month_items = SaleItem.objects.filter(sale_id__in=month_sale_ids)
    monthly_sales = sum(item.quantity * item.price for item in month_items)
    monthly_expenses = month_expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_income = monthly_sales - monthly_expenses

    # Progress bars
    max_val = max(total_sales + total_expenses + total_income, 1)
    sales_percent = (Decimal(total_sales) / Decimal(max_val)) * 100
    expense_percent = (Decimal(total_expenses) / Decimal(max_val)) * 100
    income_percent = (Decimal(total_income) / Decimal(max_val)) * 100

    base = Decimal("226.2")
    sales_progress = base * (1 - sales_percent / 100)
    expense_progress = base * (1 - expense_percent / 100)
    income_progress = base * (1 - income_percent / 100)

    # Recent sales
    recent_sales = date_sales.order_by('-id')[:5]

    context = {
        'today': selected_date,
        'branch': branch,
        'branches': Branch.objects.all() if profile.role == 'admin' else None,
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'sales_percent': sales_percent,
        'expense_percent': expense_percent,
        'income_percent': income_percent,
        'sales_progress': sales_progress,
        'expense_progress': expense_progress,
        'income_progress': income_progress,
        'recent_sales': recent_sales,
    }

    return render(request, 'dashboard/index.html', context)


def total_amount(self):
    return sum(item.total_price() for item in self.items.all())


@login_required
def staff_dashboard(request):
    return render(request, 'dashboard/staff_dashboard.html')


from django.db.models import F, Sum, FloatField, ExpressionWrapper

@login_required
def orders(request):
    profile = Profile.objects.get(user=request.user)

    if profile.role not in ['admin', 'manager']:
        return redirect('staff_dashboard')

    date_str = request.GET.get('date')
    filter_date = parse_date(date_str) if date_str else None

    # Base filters
    sale_filter = {'is_archived': False}
    history_filter = {'is_archived': True}

    if profile.role == 'manager':
        sale_filter['branch'] = profile.branch
        history_filter['branch'] = profile.branch

    if filter_date:
        sale_filter['date__date'] = filter_date
        history_filter['date__date'] = filter_date

    # Load current and historical sales
    current_sales = Sale.objects.filter(**sale_filter).prefetch_related('items', 'customer', 'branch')
    history_sales = Sale.objects.filter(**history_filter).prefetch_related('items', 'customer', 'branch')

    # Annotate total price for each sale manually
    for sale in current_sales:
        sale.total_price = sum(item.quantity * item.price for item in sale.items.all())

    for sale in history_sales:
        sale.total_price = sum(item.quantity * item.price for item in sale.items.all())

    return render(request, 'dashboard/orders.html', {
        'sales': current_sales,
        'order_history': history_sales,
        'is_admin': profile.role == 'admin',
        'selected_date': date_str
    })


@login_required
def products(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role not in ['admin', 'manager']:
        return redirect('staff_dashboard')

    branch_id = request.GET.get('branch')

    if profile.role == 'manager':
        branch = profile.branch
    elif branch_id == 'all' or branch_id is None:
        branch = None
    else:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            branch = None

    if branch:
        branch_products = BranchProduct.objects.filter(branch=branch)
    else:
        branch_products = BranchProduct.objects.all()

    # Add pagination
    paginator = Paginator(branch_products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard/products.html', {
        'branch_products': page_obj,
        'branch': branch,
        'page_obj': page_obj,
    })

@login_required
def employees(request):
    if request.method == 'POST':
        name = request.POST.get('empName', '').strip()
        phone = request.POST.get('empPhone', '').strip()
        password = request.POST.get('empPassword', '').strip()
        gst = request.POST.get('empGST', '').strip()
        role = request.POST.get('empRole', 'manager')

        branch_name = request.POST.get('branchName', '').strip()
        branch_location = request.POST.get('new_branch_location', '').strip()

        if not branch_name:
            messages.error(request, "Please enter a branch name.")
            return redirect('employees')

        if Profile.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already exists.")
            return redirect('employees')

        if not password:
            password = get_random_string(8)

        # Create user
        try:
            user = User.objects.create_user(username=phone, first_name=name, password=password)
        except Exception as e:
            messages.error(request, f"User creation failed: {str(e)}")
            return redirect('employees')

        # Branch logic
        try:
            # Try to find existing branch
            branch = Branch.objects.filter(name__iexact=branch_name).first()

            # If not found, create new (only if location is provided)
            if not branch:
                if not branch_location:
                    user.delete()
                    messages.error(request, "Location required for new branch.")
                    return redirect('employees')
                branch = Branch.objects.create(name=branch_name, location=branch_location)

        except Exception as e:
            user.delete()
            messages.error(request, f"Branch error: {str(e)}")
            return redirect('employees')

        # Create profile
        try:
            Profile.objects.create(
                user=user,
                phone=phone,
                role=role,
                gst_number=gst,
                branch=branch
            )
            messages.success(request, f"Employee '{name}' added. Password: {password}")
        except Exception as e:
            user.delete()
            messages.error(request, f"Profile creation failed: {str(e)}")

        return redirect('employees')

    # GET request
    employees = Profile.objects.filter(role__in=['manager', 'staff']).select_related('user', 'branch')
    branches = Branch.objects.all()
    return render(request, 'dashboard/employees.html', {
        'employees': employees,
        'branches': branches
    })

@csrf_exempt
@login_required
def create_branch_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            location = data.get('location', '').strip()

            if not name or not location:
                return JsonResponse({'success': False, 'error': 'Both name and location are required.'})

            branch, created = Branch.objects.get_or_create(name__iexact=name, defaults={'name': name, 'location': location})
            return JsonResponse({'success': True, 'name': branch.name})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid method'})

from django.db.models import Sum, F, DecimalField, ExpressionWrapper

@login_required
def customer(request):
    profile = Profile.objects.get(user=request.user)

    if profile.role not in ['admin', 'manager']:
        return redirect('staff_dashboard')

    if profile.role == 'admin':
        customers = Customer.objects.all()
    else:
        customers = Customer.objects.all()

    customer_data = []

    for customer in customers:
        # Only count active sales (exclude archived)
        sales = Sale.objects.filter(customer=customer, is_archived=False)

        total_amount = 0
        for sale in sales:
            total_sale = sum(item.quantity * item.price for item in sale.items.all())
            total_amount += total_sale

        total_paid = sales.aggregate(paid=Sum('amount_paid'))['paid'] or 0
        credit = total_amount - total_paid

        customer_data.append({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'credit': round(credit, 2),
        })

    return render(request, 'dashboard/customer.html', {
        'customers': customer_data
    })

@require_POST
def create_or_update_customer(request):
    data = json.loads(request.body)
    customer_id = data.get('id')
    name = data.get('name')
    phone = data.get('phone')
    gst = data.get('gst')

    if customer_id:
        customer = get_object_or_404(Customer, id=customer_id)
        customer.name = name
        customer.phone = phone
        customer.gst_number = gst
        customer.save()
    else:
        customer = Customer.objects.create(
            name=name,
            phone=phone,
            gst_number=gst
        )
    
    return JsonResponse({
        'success': True,
        'customer': {
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'gst': customer.gst_number or '',
            'credit': float(customer.credit)
        }
    })

@require_http_methods(["DELETE"])
def delete_customer(request, id):
    customer = get_object_or_404(Customer, id=id)
    customer.delete()
    return JsonResponse({'success': True})

@login_required
def staff(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role not in ['admin', 'manager']:
        return redirect('staff_dashboard')
    return render(request, 'dashboard/staff.html')

@login_required
def analytics_view(request):
    profile = Profile.objects.get(user=request.user)

    # Get selected date from GET or default today
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    # Calculate start date for 7-day range (including selected_date)
    start_date = selected_date - timedelta(days=6)

    # Filter sales & expenses by role and branch for the date range
    if profile.role == 'manager':
        branch = profile.branch
        sales_qs = Sale.objects.filter(branch=branch, date__date__range=[start_date, selected_date])
        expenses_qs = Expense.objects.filter(branch=branch, date__range=[start_date, selected_date])
    else:
        sales_qs = Sale.objects.filter(date__date__range=[start_date, selected_date])
        expenses_qs = Expense.objects.filter(date__range=[start_date, selected_date])

    # Annotate daily sales totals (sum of quantity * price) grouped by date
    sale_items = SaleItem.objects.filter(sale__in=sales_qs).annotate(
        sale_date=TruncDate('sale__date')
    ).annotate(
        total_price=ExpressionWrapper(F('quantity') * F('price'), output_field=DecimalField())
    ).values('sale_date').annotate(
        daily_total=Sum('total_price')
    ).order_by('sale_date')

    # Map daily sales totals
    sales_trend = {item['sale_date']: item['daily_total'] for item in sale_items}

    # Prepare labels (dates) and data (sales totals) for the last 7 days
    dates = [start_date + timedelta(days=i) for i in range(7)]
    sales_trend_data = [float(sales_trend.get(d, 0)) for d in dates]
    sales_trend_labels = [d.strftime('%b %d') for d in dates]

    # Total sales, expenses, and net income on the selected date
    sales_on_date = sales_qs.filter(date__date=selected_date)
    expenses_on_date = expenses_qs.filter(date=selected_date)

    # Calculate total sales on selected date (sum of quantity * price)
    sale_ids_on_date = sales_on_date.values_list('id', flat=True)
    sale_items_on_date = SaleItem.objects.filter(sale_id__in=sale_ids_on_date).annotate(
        total_price=ExpressionWrapper(F('quantity') * F('price'), output_field=DecimalField())
    )
    total_sales = sale_items_on_date.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

    # Total expenses on selected date
    total_expenses = expenses_on_date.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Net income is sum of amount_paid on sales on selected date
    net_income = sales_on_date.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

    context = {
        'selected_date': selected_date,
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'sales_trend_labels': sales_trend_labels,
        'sales_trend_data': sales_trend_data,
    }

    return render(request, 'dashboard/analytics.html', context)


@login_required
def expenses_view(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role == 'admin':
        expenses = Expense.objects.all().order_by('-date')
    else:
        expenses = Expense.objects.filter(branch=profile.branch).order_by('-date')
    
    return render(request, 'dashboard/expenses.html', {'expenses': expenses})


@csrf_exempt
@login_required
def add_expense(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            profile = Profile.objects.get(user=request.user)
            branch = profile.branch

            if not branch:
                return JsonResponse({'error': 'No branch assigned to user'}, status=400)

            Expense.objects.create(
                title=data['title'],
                amount=data['amount'],
                category=data['category'],
                date=parse_date(data['date']),
                branch=branch
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        data = json.loads(request.body)
        expense.title = data['title']
        expense.amount = data['amount']
        expense.category = data['category']
        expense.date = parse_date(data['date'])
        expense.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def delete_expense(request, expense_id):
    if request.method == 'DELETE':
        expense = get_object_or_404(Expense, id=expense_id)
        expense.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def settings(request):
    return render(request, 'dashboard/settings.html')

@login_required
def add_product(request, product_id=None):
    profile = Profile.objects.get(user=request.user)
    editing = product_id is not None
    product = get_object_or_404(Product, id=product_id) if editing else None

    if request.method == 'POST':
        name = request.POST.get('name')
        raw_inclusive_price = Decimal(request.POST.get('price') or '0.00')
        gst_percent = Decimal(request.POST.get('gst_percent') or '1.00')
        is_service = request.POST.get('is_service') == 'on'

        # Round off GST-included price to unit
        gst_inclusive_price = raw_inclusive_price.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        divisor = Decimal(1) + (gst_percent / 100)
        base_price = (gst_inclusive_price / divisor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Get the branch (always needed now)
        branch = profile.branch if profile.role == 'manager' else Branch.objects.get(id=request.POST.get('branch'))

        if editing:
            product.name = name
            product.price = base_price
            product.gst_percent = gst_percent
            product.is_service = is_service
            product.save()

            # Ensure branch-product relation exists if missing
            bp, created = BranchProduct.objects.get_or_create(branch=branch, product=product)
            if not is_service:
                bp.stock = request.POST.get('stock') or 0
                bp.save()

            messages.success(request, f"Product '{product.name}' updated successfully.")
        else:
            product = Product.objects.create(
                name=name,
                price=base_price,
                gst_percent=gst_percent,
                is_service=is_service
            )

            stock_value = None if is_service else request.POST.get('stock')
            BranchProduct.objects.create(
                branch=branch,
                product=product,
                stock=stock_value
            )

            if is_service:
                messages.success(request, f"Service '{product.name}' added to {branch.name}.")
            else:
                messages.success(request, f"Product '{product.name}' added to {branch.name} with stock {stock_value}.")

        return redirect('products')

    context = {
        'editing': editing,
        'product': product,
        'branches': Branch.objects.all() if profile.role == 'admin' else [profile.branch],
        'is_admin': profile.role == 'admin'
    }
    return render(request, 'dashboard/add_product.html', context)

@login_required
def delete_employee(request, user_id):
    if request.user.profile.role != 'admin':
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    # Optional: Prevent deleting self
    if request.user == user:
        messages.warning(request, "You cannot delete your own account.")
        return redirect('employees')

    user.delete()
    messages.success(request, "Employee deleted successfully.")
    return redirect('employees')
