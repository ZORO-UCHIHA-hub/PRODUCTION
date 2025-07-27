from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# -----------------------------
# Branch and Roles
# -----------------------------

class Branch(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=150)

    def __str__(self):
        return self.name

ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('manager', 'Manager'),
    ('staff', 'Staff'),
)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL)
    gst_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# -----------------------------
# Products
# -----------------------------



class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # GST-excluded
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    is_service = models.BooleanField(default=False)

    def gst_amount(self):
        return self.price * self.gst_percent / 100

    def price_with_gst(self):
        from decimal import Decimal, ROUND_HALF_UP
        price = self.price * (1 + self.gst_percent / 100)
        return price.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


    def __str__(self):
        return self.name

# -----------------------------
# Customers
# -----------------------------

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    gst_number = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"

# -----------------------------
# Sales
# -----------------------------

class Sale(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    staff = models.ForeignKey(
        Profile,
        limit_choices_to={'role__in': ['manager', 'staff']},
        on_delete=models.CASCADE
    )
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ✅ ADD THIS
    date = models.DateTimeField(auto_now_add=True)
    previous = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='edits')
    parent_sale = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='child_sales')
    is_archived = models.BooleanField(default=False)
    memo_pdf = models.FileField(upload_to='memos/', null=True, blank=True)
    payment_method = models.CharField(max_length=20, default="Cash")
    total_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def total_amount(self):
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        return f"Sale to {self.customer.name} on {self.date.strftime('%Y-%m-%d')}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # base price
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def total_price(self):
        base = self.price * self.quantity
        gst = self.gst_amount * self.quantity
        return base + gst



# -----------------------------
# Staff Tasks (Manager/Admin)
# -----------------------------

class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    assigned_by = models.ForeignKey(Profile, related_name="assigned_tasks", on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(Profile, related_name="tasks", limit_choices_to={'role': 'staff'}, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} → {self.assigned_to}"
    
class Expense(models.Model):
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    date = models.DateField()
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE)  # Optional, if using branches

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"

class BranchProduct(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('branch', 'product')

    def __str__(self):
        return f"{self.product.name} @ {self.branch.name}"
