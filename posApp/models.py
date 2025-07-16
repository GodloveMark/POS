from datetime import datetime
from unicodedata import category
from django.db import models
from django.utils import timezone



# Create your models here.

# class Employees(models.Model):
#     code = models.CharField(max_length=100,blank=True) 
#     firstname = models.TextField() 
#     middlename = models.TextField(blank=True,null= True) 
#     lastname = models.TextField() 
#     gender = models.TextField(blank=True,null= True) 
#     dob = models.DateField(blank=True,null= True) 
#     contact = models.TextField() 
#     address = models.TextField() 
#     email = models.TextField() 
#     department_id = models.ForeignKey(Department, on_delete=models.CASCADE) 
#     position_id = models.ForeignKey(Position, on_delete=models.CASCADE) 
#     date_hired = models.DateField() 
#     salary = models.FloatField(default=0) 
#     status = models.IntegerField() 
#     date_added = models.DateTimeField(default=timezone.now) 
#     date_updated = models.DateTimeField(auto_now=True) 

    # def __str__(self):
    #     return self.firstname + ' ' +self.middlename + ' '+self.lastname + ' '

from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date
from django.conf import settings
from django.db.models import Sum

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='cashier')
    store = models.ForeignKey('Store', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"



class Store(models.Model):
    name = models.CharField(max_length=150)
    location = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_stores'
    )
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name



class Category(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    status = models.IntegerField(default=1)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    code = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Selling price
    quantity = models.IntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # New field
    low_stock_threshold = models.PositiveIntegerField(default=10)
    status = models.IntegerField(default=1)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def get_remaining_quantity(self, store):
        return self.stock_entries.filter(
            store=store,
            remaining_quantity__gt=0
        ).aggregate(total=Sum('remaining_quantity'))['total'] or 0

    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    def __str__(self):
        return f"{self.code} - {self.name}"

from django.db.models import F
import uuid
from django.contrib.auth import get_user_model
User = get_user_model()

class Sales(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_as_user')
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    code = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    tendered_amount = models.FloatField(default=0)  # What the customer gave you at the counter
    amount_change = models.FloatField(default=0)    # Change given back
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # NEW: Paid so far
    is_credit = models.BooleanField(default=False)  # NEW: Flag if it's a credit sale
    due_date = models.DateField(null=True, blank=True)  # Optional: Due date for payment
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_as_cashier')
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    payment_status = models.CharField(max_length=20, choices=[
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('unpaid', 'Unpaid')
    ], default='paid')

    def balance(self):
        return Decimal(self.grand_total) - self.amount_paid

    def is_fully_paid(self):
        return self.amount_paid >= Decimal(self.grand_total)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"S-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class SalesItem(models.Model):
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.FloatField(default=0)
    qty = models.FloatField(default=0)
    total = models.FloatField(default=0)

    def __str__(self):
        return f"{self.product.name} x {self.qty}"


class StoreUser(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
    ]
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ('store', 'user')

    def __str__(self):
        return f"{self.user.username} ({self.role}) - {self.store.name}"



class ProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    quantity = models.FloatField(default=0)
    expiry_date = models.DateField()
    purchase_date = models.DateField(default=timezone.now)
    source = models.CharField(max_length=255, blank=True, null=True)  # e.g., supplier name or PO number

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units expiring on {self.expiry_date}"



class Expenditure(models.Model):
    store = models.ForeignKey('Store', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_spent = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.amount}"

    

class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    location = models.CharField(max_length=150)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name




class StockEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_entries')
    quantity = models.PositiveIntegerField()
    remaining_quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_received = models.DateField(default=date.today)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.remaining_quantity = self.quantity
        super().save(*args, **kwargs)
