from pickle import FALSE
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.http import JsonResponse
from posApp.models import Category, Product, Sales, SalesItem
from django.db.models import Count, Sum
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
import json, sys
from datetime import date, datetime
from django.http import HttpResponse
from django.contrib import messages
from django.utils.timezone import now
from django.db import transaction
from .models import Sales, SalesItem, Product, Customer, Supplier, Category, Store, StockEntry
import json
import sys
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.views.decorators.http import require_POST
from django.db import models
from decimal import Decimal



def cashier_only(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != "cashier":
            return redirect("/")  # redirect admin/manager back home
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_manager_only(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ["admin", "manager"]:
            return redirect("/pos/")
        return view_func(request, *args, **kwargs)
    return wrapper



# Login
#def login_user(request):
#    logout(request)
#    resp = {"status": "failed", "msg": ""}
#
#    if request.method == "POST":
#        username = request.POST.get('username')
#        password = request.POST.get('password')
#
#        if not username or not password:
#            resp['msg'] = "Username and password are required."
#            return HttpResponse(json.dumps(resp), content_type='application/json')
#
#        user = authenticate(username=username, password=password)
#
#        if user is not None:
#            if user.is_active:
#                login(request, user)
#                resp['status'] = 'success'
#                resp['role'] = user.role  # Add role info
#                resp['username'] = user.username
#                # You can also add store info if needed
#                if hasattr(user, 'owned_stores'):
#                    stores = user.owned_stores.all()
#                    resp['stores'] = [store.name for store in stores]
#            else:
#                resp['msg'] = "User account is inactive."
#        else:
#            resp['msg'] = "Incorrect username or password."
#
#    else:
#        resp['msg'] = "Invalid request method."
#
#    return HttpResponse(json.dumps(resp), content_type='application/json')

def login_user(request):
    logout(request)
    resp = {"status": "failed", "msg": ""}

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            resp['msg'] = "Username and password are required."
            return HttpResponse(json.dumps(resp), content_type='application/json')

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status'] = 'success'
                resp['role'] = user.role
                resp['username'] = user.username


                if user.role == 'admin':
                    resp['redirect_url'] = '/system-admin/dashboard/'

                elif user.role == 'manager':
                    resp['redirect_url'] = '/'
                elif user.role == 'cashier':
                    resp['redirect_url'] = '/pos'
                else:
                    resp['redirect_url'] = '/'

                # Optional: Add store info if needed
                if hasattr(user, 'owned_stores'):
                    stores = user.owned_stores.all()
                    resp['stores'] = [store.name for store in stores]
            else:
                resp['msg'] = "User account is inactive."
        else:
            resp['msg'] = "Incorrect username or password."
    else:
        resp['msg'] = "Invalid request method."

    return HttpResponse(json.dumps(resp), content_type='application/json')


#Logout
def logoutuser(request):
    logout(request)
    return redirect('/')

# Create your views here.
@login_required
def home(request):
    now = datetime.now()
    current_year = now.strftime("%Y")
    current_month = now.strftime("%m")
    current_day = now.strftime("%d")

    stores = Store.objects.filter(owner=request.user)
    categories = Category.objects.filter(store__in=stores).count()
    product_count = Product.objects.filter(store__in=stores).count()

    today_sales_qs = Sales.objects.filter(
    store__in=stores,
           date_added__year=current_year,
        date_added__month=current_month,
        date_added__day=current_day
)

    transaction = today_sales_qs.count()
    today_sales = Sales.objects.filter(
        date_added__year=current_year,
        date_added__month=current_month,
        date_added__day=current_day
    )
    total_sales = sum(today_sales_qs.values_list('grand_total', flat=True))


    context = {
        'page_title': 'Home',
        'categories': categories,
        'product_count': product_count,
        'transaction': transaction,
        'total_sales': total_sales,
    }
    return render(request, 'posApp/home.html', context)


def about(request):
    context = {
        'page_title':'About',
    }
    return render(request, 'posApp/about.html',context)

#Categories
@admin_manager_only
def category(request):
    stores = Store.objects.filter(owner=request.user)

    category_list = Category.objects.filter(store__in=stores)
    # category_list = {}
    context = {
        'page_title':'Category List',
        'category':category_list,
    }
    return render(request, 'posApp/category.html',context)

#@login_required
@admin_manager_only
def manage_category(request):
    category = {}

    # Show all stores for admin, or only the assigned one for managers
   # if request.user.role == 'admin':
   #     stores = Store.objects.all()
   # elif hasattr(request.user, 'store') and request.user.store:
    stores = Store.objects.filter(owner=request.user)
   # else:
   #     stores = Store.objects.none()  # Or maybe redirect or show message

    if request.method == 'GET':
        id = request.GET.get('id', '')
        if id.isnumeric() and int(id) > 0:
            category = Category.objects.filter(id=id).first()

    context = {
        'category': category,
        'stores': stores,
    }
    return render(request, 'posApp/manage_category.html', context)



#@login_required
@admin_manager_only
def save_category(request):
    data = request.POST
    resp = {'status': 'failed'}
    try:
        # Get the store instance
        store_id = data.get('store_id')
        store = Store.objects.get(id=store_id)

        if data['id'].isnumeric() and int(data['id']) > 0:
            # Update existing category
            Category.objects.filter(id=data['id']).update(
                name=data['name'],
                description=data['description'],
                status=data['status'],
                store=store
            )
        else:
            # Create new category
            new_category = Category(
                name=data['name'],
                description=data['description'],
                status=data['status'],
                store=store
            )
            new_category.save()

        resp['status'] = 'success'
        messages.success(request, 'Category successfully saved.')

    except Exception as e:
        resp['status'] = 'failed'
        resp['error'] = str(e)
        print("Error saving category:", e)

    return HttpResponse(json.dumps(resp), content_type="application/json")

#@login_required
@admin_manager_only
def delete_category(request):
    data =  request.POST
    resp = {'status':''}
    try:
        Category.objects.filter(id = data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Category Successfully deleted.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


#   UNITS
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Unit, Store

@login_required
@admin_manager_only
def unit_page(request):
    user = request.user

    # Admins: See all stores & their units
    if user.is_superuser:
        units = Unit.objects.select_related("store").all()
        stores = Store.objects.all()

    else:
        # Normal users: Only see units belonging to their store
        store = Store.objects.filter(owner=user).first()

        if store:
            units = Unit.objects.filter(store=store)
            stores = Store.objects.filter(id=store.id)
        else:
            units = Unit.objects.none()
            stores = Store.objects.none()

    return render(request, "posApp/unit.html", {
        "units": units,
        "stores": stores
    })


def manage_unit(request):
    """Modal form for create/edit"""
    unit = None
    if request.GET.get("id"):
        unit = get_object_or_404(Unit, pk=request.GET["id"])

    stores = Store.objects.filter(owner=request.user)
    return render(request, "posApp/manage_unit.html", {"unit": unit, "stores": stores})


def save_unit(request):
    """Save new or edit existing"""
    data = request.POST
    unit_id = data.get("id")

    if unit_id and unit_id != "0":
        unit = get_object_or_404(Unit, pk=unit_id)
    else:
        unit = Unit()

    try:
        store = Store.objects.get(pk=data.get("store_id"))
        unit.store = store
        unit.name = data.get("name")
        unit.short_name = data.get("short_name")
        unit.status = int(data.get("status"))
        unit.save()
        return JsonResponse({"status": "success"})
    except Store.DoesNotExist:
        return JsonResponse({"status": "failed", "msg": "Invalid store"})
    except Exception as e:
        return JsonResponse({"status": "failed", "msg": str(e)})


def delete_unit(request):
    """Delete a unit"""
    try:
        unit = get_object_or_404(Unit, pk=request.POST.get("id"))
        unit.delete()
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "failed", "msg": str(e)})



# Product
@login_required
@admin_manager_only
def product_list_view(request):
    stores = Store.objects.filter(owner=request.user)

    product_list = Product.objects.filter(store__in=stores).annotate(
        total_remaining_quantity=Sum('stock_entries__remaining_quantity')
    )

    low_stock_products = product_list.filter(
        total_remaining_quantity__lte=F('low_stock_threshold')
    )


    context = {
        'page_title': 'Product List',
        'products': product_list,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'posApp/products.html', context)


@login_required
@admin_manager_only
def manage_Product(request):
    product = {}
    stores = Store.objects.filter(owner=request.user)
    store = stores.first()

    settings = StoreSettings.objects.filter(store=store).first()

    categories = Category.objects.filter(store__in=stores).all()
    units = Unit.objects.filter(store__in=stores).all()
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            product = Product.objects.filter(id=id).first()

    context = {
        'product' : product,
        'categories' : categories,
        'stores' : stores,
        'units': units,
        'settings': settings,
    }
    return render(request, 'posApp/manage_product.html',context)

def test(request):
    categories = Category.objects.all()
    context = {
        'categories' : categories
    }
    return render(request, 'posApp/test.html',context)

from datetime import datetime
import uuid


def generate_product_code():
    return f"PRD-{uuid.uuid4().hex[:8].upper()}"  # Example: PRD-5F3A2B1C
#def save_product(request):
#    data = request.POST
#    resp = {'status': 'failed'}
#    product_id = data.get('id', '').strip()
#
#    # --- Validate store ---
#    try:
#        store = Store.objects.get(id=data.get('store_id'))
#    except Store.DoesNotExist:
#        resp['msg'] = "Invalid store selected."
#        return HttpResponse(json.dumps(resp), content_type="application/json")
#
#    # --- Validate related models ---
#    category = Category.objects.filter(id=data.get('category_id')).first()
#    unit = Unit.objects.filter(id=data.get('unit')).first()
#
#    if not category:
#        resp['msg'] = "Invalid category."
#        return HttpResponse(json.dumps(resp), content_type="application/json")
#
#    if not unit:
#        resp['msg'] = "Invalid unit selected."
#        return HttpResponse(json.dumps(resp), content_type="application/json")
#
#    # --- Fix expiration date ---
#    expiration_date = data.get('expiration_date')
#    exp_date = None
#    if expiration_date:
#        try:
#            exp_date = datetime.strptime(expiration_date, "%Y-%m-%d").date()
#        except ValueError:
#            resp['msg'] = "Invalid expiration date format."
#            return HttpResponse(json.dumps(resp), content_type="application/json")
#
#    try:
#        quantity = int(data.get('stock', 0))
#        cost_price = Decimal(str(data.get('cost_price', 0)))
#        price = Decimal(str(data.get('price', 0)))
#
#        if quantity < 0:
#            resp['msg'] = "Quantity cannot be negative."
#            return HttpResponse(json.dumps(resp), content_type="application/json")
#
#    except (ValueError, Decimal.InvalidOperation):
#        resp['msg'] = "Invalid numeric value."
#        return HttpResponse(json.dumps(resp), content_type="application/json")
#
#    try:
#        # =======================================
#        # UPDATE PRODUCT
#        # =======================================
#        if product_id.isnumeric() and int(product_id) > 0:
#            try:
#                product = Product.objects.get(id=product_id)
#            except Product.DoesNotExist:
#                resp['msg'] = "Product not found."
#                return HttpResponse(json.dumps(resp), content_type="application/json")
#
#            # Optional: prevent updating a product from another store
#            if product.store != store:
#                resp['msg'] = "You cannot update product of another store."
#                return HttpResponse(json.dumps(resp), content_type="application/json")
#
#            # Update product fields
#            product.category = category
#            product.store = store
#            product.unit = unit
#            product.name = data['name']
#            product.description = data['description']
#            product.quantity = quantity
#            product.cost_price = cost_price
#            product.price = price
#            product.status = data['status']
#            product.expiry_date = exp_date
#            product.save()
#
#        # =======================================
#        # CREATE NEW PRODUCT
#        # =======================================
#        else:
#            # Validate duplicate product names per store
#            if Product.objects.filter(store=store, name=data['name']).exists():
#                resp['msg'] = "A product with this name already exists in this store."
#                return HttpResponse(json.dumps(resp), content_type="application/json")
#
#            # Generate unique product code
#            code = generate_product_code()
#            while Product.objects.filter(code=code).exists():
#                code = generate_product_code()
#
#            # Create the product
#            product = Product.objects.create(
#                code=code,
#                category=category,
#                store=store,
#                unit=unit,
#                name=data['name'],
#                description=data['description'],
#                quantity=quantity,
#                cost_price=cost_price,
#                price=price,
#                status=data['status'],
#                expiry_date=exp_date
#            )
#
#            # Create stock entry ONLY if quantity > 0
#            if quantity > 0:
#                StockEntry.objects.create(
#                    product=product,
#                    store=store,
#                    quantity=quantity,
#                    remaining_quantity=quantity,
#                    cost_price=cost_price,
#                    date_received=timezone.now().date()
#                )
#
#        resp['status'] = 'success'
#        messages.success(request, "Product saved successfully.")
#
#    except Exception as e:
#        resp['status'] = 'failed'
#        resp['msg'] = str(e)
#
#    return HttpResponse(json.dumps(resp), content_type="application/json")

from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime


def save_product(request):
    data = request.POST
    resp = {"status": "failed"}

    product_id = data.get("id", "").strip()

    try:
        store = Store.objects.get(id=data.get("store_id"))
    except Store.DoesNotExist:
        return JsonResponse({"status": "failed", "msg": "Invalid store selected."})

    settings = store.settings  # ⭐ IMPORTANT

    # =========================================
    # FEATURE-BASED VALIDATION
    # =========================================

    category = None
    unit = None
    exp_date = None

    # ---------- Category ----------
    if settings.enable_categories:
        category = Category.objects.filter(
            id=data.get("category_id"), store=store
        ).first()

        if not category:
            return JsonResponse({"status": "failed", "msg": "Invalid category."})

    # ---------- Unit ----------
    if settings.enable_units:
        unit = Unit.objects.filter(
            id=data.get("unit"), store=store
        ).first()

        if not unit:
            return JsonResponse({"status": "failed", "msg": "Invalid unit selected."})

    # ---------- Expiry ----------
    if settings.enable_expiry:
        expiration_date = data.get("expiration_date")
        if expiration_date:
            try:
                exp_date = datetime.strptime(expiration_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"status": "failed", "msg": "Invalid expiration date format."})

    # =========================================
    # Numeric validation
    # =========================================
    try:
        quantity = int(data.get("stock", 0))
        cost_price = Decimal(str(data.get("cost_price", 0)))
        price = Decimal(str(data.get("price", 0)))

        if quantity < 0:
            return JsonResponse({"status": "failed", "msg": "Quantity cannot be negative."})

    except (ValueError, InvalidOperation):
        return JsonResponse({"status": "failed", "msg": "Invalid numeric value."})

    try:

        # =========================================
        # UPDATE PRODUCT
        # =========================================
        if product_id.isnumeric() and int(product_id) > 0:

            product = Product.objects.filter(id=product_id, store=store).first()
            if not product:
                return JsonResponse({"status": "failed", "msg": "Product not found."})

            product.category = category
            product.unit = unit
            product.expiry_date = exp_date
            product.name = data.get("name")
            product.description = data.get("description")
            product.quantity = quantity
            product.cost_price = cost_price
            product.price = price
            product.status = data.get("status")

            product.save()

        # =========================================
        # CREATE PRODUCT
        # =========================================
        else:

            if Product.objects.filter(store=store, name=data.get("name")).exists():
                return JsonResponse({
                    "status": "failed",
                    "msg": "A product with this name already exists in this store."
                })

            # unique code per store
            code = generate_product_code()
            while Product.objects.filter(store=store, code=code).exists():
                code = generate_product_code()

            product = Product.objects.create(
                code=code,
                store=store,
                category=category,
                unit=unit,
                name=data.get("name"),
                description=data.get("description"),
                quantity=quantity,
                cost_price=cost_price,
                price=price,
                status=data.get("status"),
                expiry_date=exp_date
            )

            # FIFO stock entry
            if quantity > 0:
                StockEntry.objects.create(
                    product=product,
                    store=store,
                    quantity=quantity,
                    remaining_quantity=quantity,
                    cost_price=cost_price,
                    date_received=timezone.now().date()
                )

        messages.success(request, "Product saved successfully.")
        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "failed", "msg": str(e)})



def deduct_stock_fifo(product, quantity_needed):
    stock_entries = StockEntry.objects.filter(
        product=product,
        remaining_quantity__gt=0
    ).order_by('date_received')

    remaining_qty = quantity_needed

    for entry in stock_entries:
        if remaining_qty <= 0:
            break

        deduct_qty = min(remaining_qty, entry.remaining_quantity)
        entry.remaining_quantity -= deduct_qty
        entry.save()

        # You can log or track which entry fulfilled which quantity
        remaining_qty -= deduct_qty

    if remaining_qty > 0:
        raise ValueError("Not enough stock available to fulfill the request.")


@login_required
@admin_manager_only
def delete_product(request):
    data =  request.POST
    resp = {'status':''}
    try:
        Product.objects.filter(id = data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Product Successfully deleted.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def pos(request):
    user = request.user

    # Admin / Manager: stores they own
    if user.role in ["admin", "manager"]:
        stores = user.owned_stores.all()

    # Cashier: stores assigned to them
    elif user.role == "cashier":
        stores = user.stores.all()

    # If user has no store
    if not stores.exists():
        return render(request, "posApp/pos.html", {
            "products": [],
            "low_stock_products": [],
            "product_json": "[]",
            "msg": "You are not assigned to any store."
        })

    # Load products for all stores this user has access to
    products = Product.objects.filter(
        store__in=stores
    ).annotate(
        total_remaining_quantity=Sum("stock_entries__remaining_quantity")
    )

    # Serialize for JS
    product_json = json.dumps([
        {
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "stock": float(p.total_remaining_quantity or 0)
        } for p in products
    ])

    return render(request, "posApp/pos.html", {
        "products": products,
        "product_json": product_json,
        "stores": stores
    })
 

@login_required
def checkout_modal(request):
    grand_total = 0
    if 'grand_total' in request.GET:
        grand_total = request.GET['grand_total']
    context = {
        'grand_total' : grand_total,
    }
    return render(request, 'posApp/checkout.html',context)

#@login_required
#def save_pos(request):
#    resp = {'status': 'failed', 'msg': ''}
#
#    if request.method != 'POST':
#        resp['msg'] = "Invalid request method"
#        return HttpResponse(json.dumps(resp), content_type="application/json")
#
#    data = request.POST
#
#    try:
#        # Grab store from the first product in the POST data
#        product_ids = data.getlist('product_id[]')
#        if not product_ids:
#            resp['msg'] = "No products provided"
#            return HttpResponse(json.dumps(resp), content_type="application/json")
#
#        first_product = Product.objects.select_related('store').filter(id=product_ids[0]).first()
#        if not first_product:
#            resp['msg'] = "Invalid product selected"
#            return HttpResponse(json.dumps(resp), content_type="application/json")
#
#        store = first_product.store
#
#        prefix = str(now().year)
#        i = 1
#
#        while True:
#            code = f'{i:05d}'
#            full_code = prefix + code
#            if not Sales.objects.filter(code=full_code).exists():
#                break
#            i += 1
#
#        with transaction.atomic():
#            # Create main sales record
#            sales = Sales.objects.create(
#                code=full_code,
#                store=store,
#                sub_total=data['sub_total'],
#                tax=data['tax'],
#                tax_amount=data['tax_amount'],
#                grand_total=data['grand_total'],
#                tendered_amount=data['tendered_amount'],
#                amount_change=data['amount_change']
#            )
#
#            qtys = data.getlist('qty[]')
#            prices = data.getlist('price[]')
#
#            for idx, product_id in enumerate(product_ids):
#                product = Product.objects.select_for_update().filter(id=product_id).first()
#                if not product:
#                    raise ValueError(f"Product with ID {product_id} not found")
#
#                qty = float(qtys[idx])
#                price = float(prices[idx])
#                total = qty * price
#
#                if product.stock < qty:
#                    raise ValueError(f"Insufficient stock for product '{product.name}'")
#
#                product.stock -= qty
#                product.save()
#
#                SalesItem.objects.create(
#                    #sale_id=sales,
#                    sale=sales,
#                    #product_id=product,
#                    product=product,
#                    qty=qty,
#                    price=price,
#                    total=total
#                )
#
#            resp['status'] = 'success'
#            resp['sale_id'] = sales.pk
#            messages.success(request, "Sale Record has been saved.")
#
#    except ValueError as ve:
#        resp['msg'] = str(ve)
#    except Exception as e:
#        resp['msg'] = "An unexpected error occurred"
#        print("Unexpected error:", sys.exc_info())
#
#    return HttpResponse(json.dumps(resp), content_type="application/json")


from decimal import Decimal
from datetime import datetime
from django.db.models import Sum, F
from django.http import JsonResponse
from .models import Product, Sales, SalesItem, StockEntry, Store, Customer
@login_required
@require_POST

@transaction.atomic
def save_pos(request):
    try:
        # --- Get posted data ---
        product_ids = request.POST.getlist('product_id[]')
        qtys = request.POST.getlist('qty[]')
        tendered_amount = Decimal(request.POST.get('tendered_amount', '0'))
        amount_paid = Decimal(request.POST.get('amount_paid', '0'))
        is_credit = request.POST.get('is_credit') == 'true'
        customer_id = request.POST.get('customer_id')
        due_date = request.POST.get('due_date')

        user = request.user

        # --- Identify user store ---
        if user.role == "cashier":
            current_store = user.assigned_stores.first()
        else:
            current_store = Store.objects.filter(owner=user).first()

        if not current_store:
            return JsonResponse({'status': 'failed', 'msg': 'No store assigned to this user.'})

        if not product_ids:
            return JsonResponse({'status': 'failed', 'msg': 'No products selected.'})

        # --- Build cart with validation ---
        cart_items = []
        sub_total = Decimal('0.00')

        for idx, pid in enumerate(product_ids):
            product = Product.objects.filter(id=pid, store=current_store).first()
            if not product:
                raise ValueError(f"Product ID {pid} does not belong to your store.")

            qty = Decimal(qtys[idx])
            if qty <= 0:
                raise ValueError(f"Invalid quantity for product {product.name}.")

            price = Decimal(product.price)

            cart_items.append({
                'product': product,
                'qty': qty,
                'price': price,
            })

            sub_total += price * qty

        # --- Calculate totals ---
        tax_rate = Decimal('0.18')
        tax_amount = sub_total * tax_rate
        grand_total = sub_total + tax_amount
        tendered = amount_paid if is_credit else tendered_amount
        amount_change = 0 if is_credit else tendered - grand_total

        # --- Customer handling ---
        customer = Customer.objects.filter(id=customer_id).first() if customer_id else None
        parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d").date() if due_date and is_credit else None

        # --- Save Sale ---
        sale = Sales.objects.create(
            store=current_store,
            user=user,
            cashier=user,
            sub_total=sub_total,
            tax=tax_rate,
            tax_amount=tax_amount,
            grand_total=grand_total,
            tendered_amount=tendered,
            amount_change=amount_change,
            is_credit=is_credit,
            customer=customer,
            due_date=parsed_due_date,
            amount_paid=tendered if is_credit else tendered_amount
        )

        
        # --- Save Sale Items + FIFO Stock ---
        for item in cart_items:
           product = item['product']
           qty_to_deduct = item['qty']
           price = item['price']
        
           # Save SaleItem
           SalesItem.objects.create(
               sale=sale,
               product=product,
               qty=qty_to_deduct,
               price=price,
               unit=product.unit if product.unit else None
           )
        
           original_qty = qty_to_deduct  # keep for ledger
        
           # FIFO stock deduction
           stock_entries = StockEntry.objects.select_for_update().filter(
               product=product,
               store=current_store,
               remaining_quantity__gt=0
           ).order_by('date_received')
        
           for entry in stock_entries:
               if qty_to_deduct <= 0:
                   break
        
               deduct = min(entry.remaining_quantity, qty_to_deduct)
               entry.remaining_quantity -= deduct
               entry.save()
               qty_to_deduct -= deduct
        
           if qty_to_deduct > 0:
               raise ValueError(f"Insufficient stock for {product.name}.")
        
           # ✅🔥 CREATE LEDGER ENTRY (THIS WAS MISSING)
           StockMovement.objects.create(
               product=product,
               store=current_store,
               movement_type="SALE",
               quantity=-original_qty,
               reference=f"SALE-{sale.id}",
               created_by=user
           )
        
           # ✅ update product stock cache
           new_stock = StockEntry.objects.filter(
               product=product,
               store=current_store
           ).aggregate(total=Sum('remaining_quantity'))['total'] or 0
        
           product.stock = new_stock
           product.save()


        return JsonResponse({'status': 'success', 'sale_id': sale.id})

    except Exception as e:
        return JsonResponse({'status': 'failed', 'msg': str(e)})




@login_required
@admin_manager_only
def salesList(request):
    stores = Store.objects.filter(owner=request.user)

    sales = Sales.objects.filter(store__in=stores)
    sale_data = []
    for sale in sales:
        data = {}
        for field in sale._meta.get_fields(include_parents=False):
            if field.related_model is None:
                data[field.name] = getattr(sale,field.name)
        data['items'] = SalesItem.objects.filter(sale_id = sale).all()
        data['item_count'] = len(data['items'])
        if 'tax_amount' in data:
            data['tax_amount'] = format(float(data['tax_amount']),'.2f')
        # print(data)
        sale_data.append(data)
    # print(sale_data)
    context = {
        'page_title':'Sales Transactions',
        'sale_data':sale_data,
    }
    # return HttpResponse('')
    return render(request, 'posApp/sales.html',context)

@login_required
@admin_manager_only
def receipt(request):
    id = request.GET.get('id')
    sales = Sales.objects.filter(id = id).first()
    transaction = {}
    for field in Sales._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales,field.name)
    if 'tax_amount' in transaction:
        transaction['tax_amount'] = format(float(transaction['tax_amount']))
    ItemList = SalesItem.objects.filter(sale_id = sales).all()
    context = {
        "transaction" : transaction,
        "SalesItem" : ItemList
    }

    return render(request, 'posApp/receipt.html',context)
    # return HttpResponse('')

@login_required
@admin_manager_only
def delete_sale(request):
    resp = {'status':'failed', 'msg':''}
    id = request.POST.get('id')
    try:
        delete = Sales.objects.filter(id = id).delete()
        resp['status'] = 'success'
        messages.success(request, 'Sale Record has been deleted.')
    except:
        resp['msg'] = "An error occured"
        print("Unexpected error:", sys.exc_info()[0])
    return HttpResponse(json.dumps(resp), content_type='application/json')


from django.contrib.auth import get_user_model
User = get_user_model()
#
#def register_user(request):
#    if request.method != "POST":
#        return JsonResponse({"status": "failed", "msg": "Invalid request method."})
#
#    current_user = request.user
#    data = request.POST
#    username = data.get("username")
#    password = data.get("password")
#    role = data.get("role")
#
#    # Validate role based on who is creating
#    if current_user.role == 'admin' and role != 'manager':
#        return JsonResponse({"status": "failed", "msg": "Admin can only create managers."})
#    elif current_user.role == 'manager' and role != 'cashier':
#        return JsonResponse({"status": "failed", "msg": "Manager can only create cashiers."})
#    elif current_user.role == 'cashier':
#        return JsonResponse({"status": "failed", "msg": "Cashiers cannot create users."})
#
#    if User.objects.filter(username=username).exists():
#        return JsonResponse({"status": "failed", "msg": "Username already exists."})
#
#    try:
#        user = User.objects.create_user(username=username, password=password, role=role)
#        user.save()
#        return JsonResponse({"status": "success", "msg": f"{role.capitalize()} account created."})
#    except Exception as e:
#        return JsonResponse({"status": "failed", "msg": str(e)})

from .models import Store, StoreUser, CustomUser
from django.contrib.auth.hashers import make_password

@login_required
@admin_manager_only
def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']

        # Create user
        user = CustomUser.objects.create(
            username=username,
            password=make_password(password),
            role=role,
            is_active=True
        )

        # Assign store based on who is creating
        if role == 'manager' and request.user.role == 'admin':
            # Admin creates manager and assigns store
            store_id = request.POST.get('store_id')
            store = Store.objects.get(id=store_id)
            StoreUser.objects.create(user=user, store=store)

        elif role == 'cashier' and request.user.role == 'manager':
            # Manager creates cashier, assign to their own store
            manager_store = StoreUser.objects.get(user=request.user).store
            StoreUser.objects.create(user=user, store=manager_store)

        messages.success(request, f"{role.capitalize()} account for '{username}' created successfully.")
        return redirect('manager_dashboard' if request.user.role == 'manager' else 'admin_dashboard')

    # GET request
    stores = Store.objects.all() if request.user.role == 'admin' else None
    return render(request, 'posApp/register_user.html', {'stores': stores})



@login_required
def reset_password(request):
    if request.method != "POST":
        return JsonResponse({"status": "failed", "msg": "Invalid request method."})

    current_user = request.user
    username = request.POST.get("username")
    new_password = request.POST.get("new_password")

    try:
        user = User.objects.get(username=username)

        if current_user.role == 'manager' and user.role != 'cashier':
            return JsonResponse({"status": "failed", "msg": "Managers can only reset cashier passwords."})
        elif current_user.role == 'cashier':
            return JsonResponse({"status": "failed", "msg": "Cashiers cannot reset passwords."})

        user.set_password(new_password)
        user.save()
        return JsonResponse({"status": "success", "msg": "Password updated successfully."})
    except User.DoesNotExist:
        return JsonResponse({"status": "failed", "msg": "User not found."})


from .models import CustomUser, StoreUser
@login_required
def manager_dashboard(request):
    if request.user.role != 'manager':
        return redirect('login_user')  # Or show "Unauthorized" page

    # Get store linked to manager
    try:
        store = StoreUser.objects.get(user=request.user).store
        cashiers = CustomUser.objects.filter(role='cashier', storeuser__store=store)
    except StoreUser.DoesNotExist:
        cashiers = []

    return render(request, 'posApp/manager_dashboard.html', {'cashiers': cashiers})

@login_required
def register_cashier_page(request):
    if request.user.role != 'manager':
        return redirect('login_user')
    return render(request, 'posApp/register_cashier.html')

@login_required
def cashier_pos(request):
    if request.user.role != 'cashier':
        return redirect('login_user')
    Product = Product.objects.filter(status=1)
    return render(request, 'posApp/cashier_pos.html', {'Product': Product})

@login_required
def sales_history(request):
    if request.user.role not in ['cashier', 'manager']:
        return redirect('login_user')
    sales = Sales.objects.order_by('-date_added')[:50]  # limit recent
    return render(request, 'posApp/sales_history.html', {'sales': sales})


#@login_required
#def admin_dashboard(request):
#    if request.user.role != 'admin':
#        return redirect('login_user')
#
#    stores = Store.objects.all()
#    print("Stores:", stores)
#
#    return render(request, 'posApp/admin_dashboard.html', {
#        'stores': stores,
#        'managers': CustomUser.objects.filter(role='manager'),
#        'test': stores
#    })
from django.conf import settings
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('login_user')

    stores = Store.objects.all()
    print("Stores:", stores)
    print("Database in use:", settings.DATABASES['default']['NAME'])
    managers = CustomUser.objects.filter(role='manager')

    return render(request, 'posApp/admin_dashboard.html', {
        'stores': stores,
        'managers': managers
    })




@login_required
def create_store(request):
    if request.user.role != 'admin':
        return redirect('login_user')

    if request.method == 'POST':
        name = request.POST['name']
        location = request.POST.get('location', '')
        Store.objects.create(name=name, location=location, owner=None)  # ← Explicitly set owner
        messages.success(request, f"Store '{name}' created successfully.")

    return redirect('admin_dashboard')


@login_required
def user_list(request):
    if request.user.role != 'admin':
        return redirect('login_user')

    users = CustomUser.objects.exclude(role='admin')
    return render(request, 'posApp/user_list.html', {'users': users})


from django.shortcuts import get_object_or_404


@login_required
def edit_user(request, user_id):
    if request.user.role != 'admin':
        return redirect('login_user')

    user = get_object_or_404(CustomUser, id=user_id)
    stores = Store.objects.all()

    if request.method == 'POST':
        user.username = request.POST['username']
        user.role = request.POST['role']

        # Optional password change
        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)

        user.save()

        # Update or create store assignment
        store_id = request.POST.get('store_id')
        if store_id:
            store = Store.objects.get(id=store_id)
            StoreUser.objects.update_or_create(user=user, defaults={'store': store})

        messages.success(request, f"User '{user.username}' updated successfully.")
        return redirect('user_list')

    # For GET requests
    try:
        assigned_store = StoreUser.objects.get(user=user).store
    except StoreUser.DoesNotExist:
        assigned_store = None

    return render(request, 'posApp/edit_user.html', {
        'user_obj': user,
        'stores': stores,
        'assigned_store': assigned_store,
    })



#@login_required
#def admin_dashboard(request):
#    return render(request, 'posApp/admin_dashboard.html', {'page_title': 'Admin Dashboard'})

@login_required
def manager_dashboard(request):
    return render(request, 'posApp/manager_dashboard.html', {'page_title': 'Manager Dashboard'})


from django.contrib import messages
from django.contrib.auth.hashers import make_password

def create_store_and_manager(request):
    if request.user.role != 'admin':
        return redirect('login_user')

    if request.method == 'POST':
        store_name = request.POST['store_name']
        store_location = request.POST.get('store_location', '')
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']

        # Create the store (no owner yet)
        store = Store.objects.create(name=store_name, location=store_location, owner=None)

        # Create the manager and assign the store
        manager = CustomUser.objects.create(
            username=username,
            password=make_password(password),
            role=role
        )
        store.owner = manager
        store.save()

        messages.success(request, f"Store '{store.name}' and Manager '{manager.username}' created successfully.")
        return redirect('admin_dashboard')





from django.utils import timezone
from datetime import datetime
from .models import Sales, SalesItem, Expenditure, Product
from django.core.paginator import Paginator

@login_required
@admin_manager_only
def report_view(request):
    store = Store.objects.filter(owner=request.user).first()

    # Handle date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    include_tax = request.GET.get('include_tax') == 'on'
    include_expense = request.GET.get('include_expense') == 'on'

    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = end_date = today

    # Get current year for monthly expenditure breakdown
    year = timezone.now().year
    months = []
    monthly_expenses = []
    for month in range(1, 13):
        total = Expenditure.objects.filter(
            store=store,
            date_spent__year=year,
            date_spent__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        monthly_expenses.append(total)
        months.append(calendar.month_name[month])

    # Get sales within date range
    sales = Sales.objects.filter(
        store=store,
        date_added__date__range=[start_date, end_date]
    )

    total_sales = sum(Decimal(s.grand_total) for s in sales)
    tax_amount = sum(Decimal(s.tax_amount) for s in sales) if include_tax else Decimal(0)

    # Get related sale items
    sale_items = SalesItem.objects.filter(sale__in=sales)

    # Show 10 transactions per page
    paginator = Paginator(sales, 10) 
    page_number = request.GET.get('page')
    sales_page_obj = paginator.get_page(page_number)

    # Compute total cost of products sold
    total_cost = sum(
        Decimal(item.qty) * Decimal(item.product.cost_price)
        for item in sale_items
    )

    # Optional expense inclusion
    if include_expense:
        expenses = Expenditure.objects.filter(
            store=store,
            date_spent__range=[start_date, end_date]
        )
        total_expense = sum(Decimal(e.amount) for e in expenses)
    else:
        total_expense = Decimal(0)

    # Final profit calculation
    profit = total_sales - total_cost - tax_amount - total_expense

    context = {
        'sales': sales,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_cost': total_cost,
        'tax_amount': tax_amount,
        'total_expense': total_expense,
        'profit': profit,
        'include_tax': include_tax,
        'include_expense': include_expense,
        'months': months,
        'monthly_expenses': monthly_expenses,
        'sales': sales_page_obj,
    }

    return render(request, 'posApp/report.html', context)


import calendar

from .models import Expenditure
from .forms import ExpenditureForm,  CreateCashierForm, ChangeUserPasswordForm


def expenditure_list(request):

    store = Store.objects.filter(owner=request.user).first()
    expenditures = Expenditure.objects.filter(store=store).order_by('-date_spent')
    total_expense = expenditures.aggregate(models.Sum('amount'))['amount__sum'] or 0
    return render(request, 'expenditures/list.html', {
        'expenditures': expenditures,
        'total_expense': total_expense,
    })

def add_expenditure(request):
    store = Store.objects.filter(owner=request.user).first()
    if request.method == 'POST':
        form = ExpenditureForm(request.POST)
        if form.is_valid():
            expenditure = form.save(commit=False)
            expenditure.store = store
            expenditure.added_by = request.user
            expenditure.save()
            return redirect('expenditure_list')
    else:
        form = ExpenditureForm()

    return render(request, 'expenditures/add.html', {
        'form': form,
        'today_date': date.today().isoformat()
    })


@admin_manager_only
def delete_expenditure(request, pk):
    expenditure = get_object_or_404(Expenditure, pk=pk, store__owner=request.user)
    expenditure.delete()
    messages.success(request, "Expenditure deleted successfully.")
    return redirect('expenditure_list')



def stock_view(request):
    store = Store.objects.filter(owner=request.user).first()

    current_stock = Product.objects.filter(quantity__gt=0, store=store)
    sold_out = Product.objects.filter(quantity=0, store=store)
    new_stock = Product.objects.filter(
        date_added__gte=timezone.now() - timedelta(days=7),
        store=store
    )

    context = {
        'current_stock': current_stock,
        'sold_out': sold_out,
        'new_stock': new_stock,
    }
    return render(request, 'stock_list.html', context)


def stock_overview(request):
    recent_threshold = now() - timedelta(days=7)  # Define 'new' stock as last 7 days

    current_stock = Product.objects.filter(quantity__gt=0)
    sold_out = Product.objects.filter(quantity=0)
    new_stock = Product.objects.filter(date_added__gte=recent_threshold)

    context = {
        'current_stock': current_stock,
        'sold_out': sold_out,
        'new_stock': new_stock,
    }
    return render(request, 'stock/overview.html', context)


def expenditure_report(request):
    expenditures = Expenditure.objects.all()
    type_filter = request.GET.get('type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if type_filter:
        expenditures = expenditures.filter(type=type_filter)

    if start_date:
        expenditures = expenditures.filter(date__gte=parse_date(start_date))

    if end_date:
        expenditures = expenditures.filter(date__lte=parse_date(end_date))

    total_spent = expenditures.aggregate(Sum('amount'))['amount__sum'] or 0

    # Data for chart
    chart_data = expenditures.values('date').annotate(total=Sum('amount')).order_by('date')

    context = {
        'expenditures': expenditures,
        'total_spent': total_spent,
        'chart_data': list(chart_data),
    }
    return render(request, 'expenditures/report.html', context)

from .forms import CustomerForm, SupplierForm
def get_user_store(user):
    if hasattr(user, 'store'):
        return user.store
    return Store.objects.filter(owner=user).first()

@login_required
def add_customer(request):
    #store = get_user_store(request.user)
    store= Store.objects.filter(owner=request.user).first()
    # Ensure user has an assigned store
    if not store:
        messages.error(request, "You must be assigned to a store to add customers.")
        return redirect('customer-list')

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.store = store  # Use the retrieved store
            customer.save()
            return redirect('customer-list')
    else:
        form = CustomerForm()

    return render(request, 'posApp/add_customer.html', {'form': form})

@login_required
def add_supplier(request):
    store= Store.objects.filter(owner=request.user).first()
    # Ensure user has an assigned store
    if not store:
        messages.error(request, "You must be assigned to a store to add customers.")
        return redirect('supplier-list')

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.store = store
            supplier.save()
            return redirect('supplier-list')
    else:
        form = SupplierForm()
    return render(request, 'posApp/add_supplier.html', {'form': form})

from django.db.models import Q

def customer_list(request):
    stores = Store.objects.filter(owner=request.user)
    customers = Customer.objects.filter(store__in=stores).all()
    return render(request, 'posApp/customer_list.html', {'customers': customers})


def supplier_list(request):
    stores = Store.objects.filter(owner=request.user)
    suppliers = Supplier.objects.filter(store__in=stores).all()
    return render(request, 'posApp/supplier_list.html', {'suppliers': suppliers})





from .models import StockEntry
from .forms import StockEntryForm

@admin_manager_only
def add_stock_entry(request):
    if request.method == 'POST':
        form = StockEntryForm(request.POST, user=request.user)
        if form.is_valid():
            stock_entry = form.save(commit=False)
            stock_entry.remaining_quantity = stock_entry.quantity
            stock_entry.save()
            return redirect('stock_entry_list')
    else:
        form = StockEntryForm(user=request.user)

    return render(request, 'stock/add_stock_entry.html', {'form': form})


def stock_entry_list(request):
    stores = Store.objects.filter(owner=request.user)
    entries = StockEntry.objects.filter(product__store__in=stores).order_by('-date_received')

   # entries = StockEntry.objects.select_related('product').order_by('-date_received')
    return render(request, 'posApp/stock_entry_list.html', {'entries': entries})



from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Product, StockEntry, SalesItem, Sales, Unit

from django.db import transaction
from django.shortcuts import get_object_or_404
#from .models import Sales, SalesItem, Product, StockEntry
#
#
#
#@transaction.atomic
#def process_checkout(cart_items, store, user, sub_total, tax, tax_amount, grand_total, tendered_amount, amount_change):
#    # Create the main Sales record
#    sale = Sales.objects.create(
#        store=store,
#        cashier=user,
#        sub_total=sub_total,
#        tax=tax,
#        tax_amount=tax_amount,
#        grand_total=grand_total,
#        tendered_amount=tendered_amount,
#        amount_change=amount_change
#    )
#
#    for item in cart_items:
#        product_id = item['product_id']
#        qty_to_deduct = Decimal(str(item['qty']))
#
#        try:
#            product = Product.objects.get(id=product_id, store=store)
#        except Product.MultipleObjectsReturned:
#            raise ValueError(f"Multiple products found for ID {product_id} in store '{store.name}'")
#        except Product.DoesNotExist:
#            raise ValueError(f"Product ID {product_id} does not exist in store '{store.name}'")
#
#        price = Decimal(str(product.price))
#
#        # Get FIFO stock entries
#        stock_entries = StockEntry.objects.select_for_update().filter(
#            product=product,
#            store=store,
#            remaining_quantity__gt=0
#        ).order_by('date_received')
#
#        total_available = sum(entry.remaining_quantity for entry in stock_entries)
#        if total_available < qty_to_deduct:
#            raise ValueError(f"Not enough stock for '{product.name}' in store '{store.name}'")
#
#        # Deduct stock using FIFO
#        remaining_qty = qty_to_deduct
#        for entry in stock_entries:
#            if remaining_qty <= 0:
#                break
#            used_qty = min(entry.remaining_quantity, remaining_qty)
#            entry.remaining_quantity -= used_qty
#            entry.save()
#            remaining_qty -= used_qty
#
#        # Record the sale item
#        SalesItem.objects.create(
#            product=product,
#            qty=qty_to_deduct,
#            price=price,
#            total=qty_to_deduct * price,
#            sale=sale
#        )
#
#        # Recalculate product stock from StockEntry
#        new_total_stock = StockEntry.objects.filter(
#            product=product,
#            store=store
#        ).aggregate(total_remaining=Sum('remaining_quantity'))['total_remaining'] or 0
#
#        product.stock = new_total_stock
#        product.save()
#
#return sale


from .models import Product, StockEntry, Sales, SalesItem, StockMovement


@transaction.atomic
def process_checkout(cart_items, store, user, sub_total, tax, tax_amount, grand_total, tendered_amount, amount_change):

    sale = Sales.objects.create(
        store=store,
        cashier=user,
        sub_total=sub_total,
        tax=tax,
        tax_amount=tax_amount,
        grand_total=grand_total,
        tendered_amount=tendered_amount,
        amount_change=amount_change
    )

    for item in cart_items:
        product_id = item['product_id']
        qty_to_deduct = Decimal(str(item['qty']))

        product = Product.objects.get(id=product_id, store=store)
        price = Decimal(str(product.price))

        stock_entries = StockEntry.objects.select_for_update().filter(
            product=product,
            store=store,
            remaining_quantity__gt=0
        ).order_by('date_received')

        total_available = sum(e.remaining_quantity for e in stock_entries)
        if total_available < qty_to_deduct:
            raise ValueError(f"Not enough stock for '{product.name}'")

        # FIFO deduction
        remaining_qty = qty_to_deduct
        for entry in stock_entries:
            if remaining_qty <= 0:
                break

            used_qty = min(entry.remaining_quantity, remaining_qty)
            entry.remaining_quantity -= used_qty
            entry.save()
            remaining_qty -= used_qty

        # create sale item
        SalesItem.objects.create(
            product=product,
            qty=qty_to_deduct,
            price=price,
            total=qty_to_deduct * price,
            sale=sale
        )

        # 🔥 create ledger movement (VERY IMPORTANT)
        StockMovement.objects.create(
            product=product,
            store=store,
            movement_type="SALE",
            quantity=-qty_to_deduct,
            reference=f"SALE-{sale.id}",
            created_by=user
        )

        # update product stock
        new_total_stock = StockEntry.objects.filter(
            product=product,
            store=store
        ).aggregate(total_remaining=Sum('remaining_quantity'))['total_remaining'] or 0

        product.stock = new_total_stock
        product.save()

    return sale




def get_current_stock(product):
    return sum(entry.remaining_quantity for entry in StockEntry.objects.filter(product=product))


@login_required
def credit_sales(request):
    store = Store.objects.filter(owner=request.user).first()
    products = Product.objects.filter(store=store)
    customers = Customer.objects.filter(store=store)

    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        due_date = request.POST.get('due_date')
        amount_paid = Decimal(request.POST.get('amount_paid') or 0)
        product_ids = request.POST.getlist('product_id[]')
        qtys = request.POST.getlist('qty[]')

        if not customer_id or not due_date or not product_ids:
            messages.error(request, "Missing fields.")
            return redirect('credit-sale')

        sub_total = Decimal('0.00')
        cart_items = []

        for i, pid in enumerate(product_ids):
            product = Product.objects.get(id=pid)
            qty = Decimal(qtys[i])
            cart_items.append({'product': product, 'qty': qty})
            sub_total += product.price * qty

        tax = Decimal('0.18')
        tax_amount = sub_total * tax
        grand_total = sub_total + tax_amount
        amount_change = amount_paid - grand_total

        # Save the sale
        sale = Sales.objects.create(
            store=store,
            user=request.user,
            cashier=request.user,
            sub_total=sub_total,
            tax=tax,
            tax_amount=tax_amount,
            grand_total=grand_total,
            tendered_amount=amount_paid,
            amount_change=amount_change,
            date_added=timezone.now()
        )

        # Save each product in SalesItem
        for item in cart_items:
            SalesItem.objects.create(
                sale=sale,
                product=item['product'],
                qty=item['qty'],
                price=item['product'].price
            )

        # Optional: Record credit metadata if needed (e.g., due_date, customer)
        sale.customer = Customer.objects.get(id=customer_id)
        sale.due_date = due_date  # Add `due_date` to your Sales model if needed
        sale.save()

        messages.success(request, "Credit sale recorded.")
        return redirect('sales-page')

    return render(request, 'posApp/credit_sales.html', {
        'products': products,
        'customers': customers,
    })


@login_required
def credit_sale_view(request):
    store = Store.objects.filter(owner=request.user).first()
    customers = Customer.objects.filter(store=store)
    return render(request, 'posApp/credit_sale.html', {'customers': customers})

@login_required
def credit_sales_report(request):
    store = Store.objects.filter(owner=request.user).first()
    credit_sales = Sales.objects.filter(
        store=store,
        tendered_amount__lt=F('grand_total')
    ).select_related('user', 'cashier').order_by('-date_added')

    return render(request, 'posApp/credit_sales_report.html', {
        'credit_sales': credit_sales
    })



from decimal import Decimal

@login_required
@require_POST
def save_credit_sale(request):
    store = Store.objects.filter(owner=request.user).first()
    customer_id = request.POST.get('customer')
    customer = Customer.objects.filter(id=customer_id, store=store).first()
    amount_paid = Decimal(request.POST.get('amount_paid', 0))

    # Simulated for now: You'd typically receive products via JS/AJAX
    # For now assume it's predefined or hardcoded for example purposes
    cart_items = [
        {'product_id': 1, 'qty': 2},
        {'product_id': 2, 'qty': 1}
    ]

    sub_total = Decimal(0)
    for item in cart_items:
        product = Product.objects.get(id=item['product_id'], store=store)
        sub_total += Decimal(product.price) * Decimal(item['qty'])

    tax = Decimal('0.18')
    tax_amount = sub_total * tax
    grand_total = sub_total + tax_amount
    balance = grand_total - amount_paid

    if amount_paid >= grand_total:
        status = 'paid'
    elif amount_paid > 0:
        status = 'partial'
    else:
        status = 'unpaid'

    sale = Sales.objects.create(
        store=store,
        user=request.user,
        cashier=request.user,
        sub_total=sub_total,
        tax=tax,
        tax_amount=tax_amount,
        grand_total=grand_total,
        tendered_amount=amount_paid,
        amount_change=Decimal('0.00'),
        customer=customer,
        payment_status=status
    )

    # Add SalesItems and deduct from FIFO stock here

    return redirect('credit-sales')




User = get_user_model()

# ----------------- CREATE CASHIER -----------------
@admin_manager_only
def create_cashier(request):
    if request.method == "POST":
        form = CreateCashierForm(request.POST, user=request.user)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            store = form.cleaned_data["store"]  # Already validated store

            # Create cashier
            cashier = CustomUser.objects.create_user(
                username=username,
                password=password,
                role="cashier"
            )

            # Assign cashier to store
            store.cashiers.add(cashier)

            messages.success(request, "Cashier created successfully.")
            return redirect("create-cashier")
        else:
            return render(request, "posApp/create_cashier.html", {"form": form})

    form = CreateCashierForm(user=request.user)
    return render(request, "posApp/create_cashier.html", {"form": form})



# ----------------- CHANGE USER PASSWORD -----------------
@admin_manager_only
@login_required
def change_user_password(request):
    manager = request.user  # logged-in manager

    if request.method == "POST":
        form = ChangeUserPasswordForm(request.POST, manager=manager)
        if form.is_valid():
            user = form.cleaned_data['user']
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            messages.success(request, "Password changed successfully!")
            return redirect("change_user_password")
    else:
        form = ChangeUserPasswordForm(manager=manager)

    return render(request, "posApp/change_user_password.html", {"form": form})






from .forms import StoreSettingsForm
from .models import StoreUser, StoreSettings


@login_required
def store_settings(request):

    # -----------------------------------
    # SAFE store access
    # -----------------------------------
    store = Store.objects.filter(owner=request.user).first()

    if not store:
        messages.error(request, "No store assigned to your account.")
        return redirect("pos-page")  # change if needed


    # -----------------------------------
    # SAFE settings access (important)
    # -----------------------------------
    settings, _ = StoreSettings.objects.get_or_create(store=store)


    # -----------------------------------
    # Form handling
    # -----------------------------------
    if request.method == "POST":
        form = StoreSettingsForm(request.POST, instance=settings)

        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated successfully")
            return redirect("store-settings")

    else:
        form = StoreSettingsForm(instance=settings)


    return render(request, "posApp/settings.html", {
        "form": form,
        "settings": settings,  # optional if template needs it
    })



def stock_ledger(request, product_id, store_id):
    product = get_object_or_404(Product, id=product_id)
    store = get_object_or_404(Store, id=store_id)

    movements = product.movements.filter(store=store)

    balance = 0
    rows = []

    for m in movements:
        balance += m.quantity
        rows.append((m, balance))

    return render(request, "posApp/stock_ledger.html", {
        "product": product,
        "rows": rows,
        "store": store
    })




import pandas as pd
from django.http import HttpResponse

def export_products_excel(request):
    store = Store.objects.filter(owner=request.user).first()

    qs = Product.objects.filter(store=store).select_related('category', 'unit')

    data = []
    for p in qs:
        data.append({
            "code": p.code,
            "name": p.name,
            "category": p.category.name if p.category else "",
            "price": p.price,
            "cost_price": p.cost_price,
            "unit": p.unit.short_name if p.unit else "",
            "low_stock_threshold": p.low_stock_threshold,
        })

    df = pd.DataFrame(data)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=products.xlsx"

    df.to_excel(response, index=False)
    return response


def download_product_template(request):
    df = pd.DataFrame(columns=[
        "code",
        "name",
        "category",
        "price",
        "cost_price",
        "unit",
        "low_stock_threshold",
        "opening_stock"   # ✅ NEW
    ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=product_template.xlsx"

    df.to_excel(response, index=False)
    return response



from decimal import Decimal, InvalidOperation
import pandas as pd
from django.contrib import messages
from django.shortcuts import redirect
from .models import Product, Category, Unit, Store
from decimal import Decimal, InvalidOperation
import pandas as pd
from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction

@transaction.atomic
def import_products_excel(request):
    if request.method != "POST":
        return redirect("product-page")

    file = request.FILES.get("file")
    store = Store.objects.filter(owner=request.user).first()

    if not file or not store:
        messages.error(request, "Invalid import request")
        return redirect("product-page")

    df = pd.read_excel(file)
    df.columns = df.columns.str.lower()  # ✅ normalize headers

    REQUIRED_COLUMNS = {"name", "price", "cost_price"}
    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        messages.error(
            request,
            f"Missing required columns: {', '.join(missing)}"
        )
        return redirect("product-page")

    for _, row in df.iterrows():

        # ---------- REQUIRED ----------
        name = str(row.get("name", "")).strip()
        if not name:
            continue

        try:
            price = Decimal(row.get("price"))
            cost_price = Decimal(row.get("cost_price"))
        except (InvalidOperation, TypeError):
            continue

        # ---------- OPTIONAL ----------
        code = str(row.get("code")).strip() if not pd.isna(row.get("code")) else None

        category = None
        if "category" in df.columns and not pd.isna(row.get("category")):
            category, _ = Category.objects.get_or_create(
                name=str(row["category"]).strip(),
                store=store
            )

        unit = None
        if "unit" in df.columns and not pd.isna(row.get("unit")):
            unit, _ = Unit.objects.get_or_create(
                short_name=str(row["unit"]).strip(),
                store=store
            )

        low_stock = Decimal("10")
        if "low_stock_threshold" in df.columns and not pd.isna(row.get("low_stock_threshold")):
            try:
                low_stock = Decimal(row["low_stock_threshold"])
            except InvalidOperation:
                pass

        # ---------- OPENING STOCK ----------
        opening_stock = Decimal("0")
        if "opening_stock" in df.columns and not pd.isna(row.get("opening_stock")):
            try:
                opening_stock = Decimal(row["opening_stock"])
            except InvalidOperation:
                opening_stock = Decimal("0")

        # ---------- AUTO CODE ----------
        if not code:
            code = f"PRD-{store.id}-{Product.objects.count() + 1}"

        product, created = Product.objects.update_or_create(
            code=code,
            store=store,
            defaults={
                "name": name,
                "category": category,
                "price": price,
                "cost_price": cost_price,
                "unit": unit,
                "low_stock_threshold": low_stock,
            }
        )

        # ---------- CREATE STOCK ENTRY ----------
        if opening_stock > 0:
            StockEntry.objects.create(
                product=product,
                store=store,
                quantity=opening_stock,
                remaining_quantity=opening_stock,
                cost_price=cost_price
            )
            # 🔥 StockMovement(IN) auto-created in StockEntry.save()

    messages.success(request, "Products and opening stock imported successfully")
    return redirect("product-page")


def download_stock_template(request):
    df = pd.DataFrame(columns=[
        "product_code","product_name", "quantity", "cost_price", "date_received"
    ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=stock_template.xlsx"

    df.to_excel(response, index=False)
    return response



import pandas as pd
from django.db import transaction
from django.shortcuts import redirect
from django.contrib import messages
from datetime import date

@transaction.atomic
def import_stock_excel(request):
    if request.method == "POST":
        file = request.FILES.get('file')
        if not file:
            messages.error(request, "No file uploaded.")
            return redirect(request.META.get('HTTP_REFERER'))

        df = pd.read_excel(file)

        user = request.user
        store = user.assigned_stores.first() if user.role == "cashier" else Store.objects.filter(owner=user).first()

        for _, row in df.iterrows():
            product = Product.objects.filter(
                code=row['product_code'],
                store=store
            ).first()

            if not product:
                continue  # skip invalid products

            qty = int(row['quantity'])
            cost = float(row['cost_price'])
            received = row.get('date_received', date.today())

            StockEntry.objects.create(
                product=product,
                store=store,
                quantity=qty,
                remaining_quantity=qty,
                cost_price=cost,
                date_received=received
            )

        messages.success(request, "Stock imported successfully.")
        return redirect(request.META.get('HTTP_REFERER'))



import pandas as pd
from django.http import HttpResponse

def export_stock_excel(request):
    user = request.user
    store = user.assigned_stores.first() if user.role == "cashier" else Store.objects.filter(owner=user).first()

    data = []
    products = Product.objects.filter(store=store)

    for p in products:
        data.append({
            "product_code": p.code,
            "product_name": p.name,
            "current_stock": p.get_remaining_quantity(store),
            "selling_price": p.price,
            "unit": p.unit.short_name if p.unit else ""
        })

    df = pd.DataFrame(data)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=current_stock.xlsx'

    df.to_excel(response, index=False)
    return response



#def edit_stock_entry(request, pk):
#    store = Store.objects.filter(owner=request.user).first()
#    entry = get_object_or_404(StockEntry, pk=pk, store=store)
#
#    if request.method == "POST":
#        form = StockEntryForm(request.POST, instance=entry)
#        if form.is_valid():
#            form.save()
#            messages.success(request, "Stock entry updated successfully.")
#            return redirect("stock_entry_list")
#    else:
#        form = StockEntryForm(instance=entry)
#
#    # Pass to stock_entry_list template for modal
#    entries = StockEntry.objects.all().order_by('-date_received')  # existing list
#    return render(request, "posApp/stock_entry_list.html", {
#        "entries": entries,
#        "form": form,
#        "edit_entry": entry,
#        "title": "Edit Stock Entry"
#    })


@require_POST
def delete_stock_entry(request, pk):
    entry = get_object_or_404(StockEntry, pk=pk)
    entry.delete()
    messages.success(request, "Stock entry deleted successfully.")
    return redirect("stock_entry_list")