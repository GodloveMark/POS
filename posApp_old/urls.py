from . import views
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic.base import RedirectView

urlpatterns = [
    path('redirect-admin', RedirectView.as_view(url="/admin"),name="redirect-admin"),
    path('', views.home, name="home-page"),
    path('login', auth_views.LoginView.as_view(template_name = 'posApp/login.html',redirect_authenticated_user=True), name="login"),
    path('userlogin', views.login_user, name="login-user"),
    path('logout', views.logoutuser, name="logout"),
    path('category', views.category, name="category-page"),
    path('manage_category', views.manage_category, name="manage_category-page"),
    path('save_category', views.save_category, name="save-category-page"),
    path('delete_category', views.delete_category, name="delete-category"),
    
    path('products/', views.product_list_view, name='product-page'),

    path('manage_product', views.manage_Product, name="manage_product-page"),
    path('test', views.test, name="test-page"),
    path('save_product', views.save_product, name="save-product-page"),
    path('delete_product', views.delete_product, name="delete-product"),
    path('pos', views.pos, name="pos-page"),
    path('checkout-modal', views.checkout_modal, name="checkout-modal"),
    path('save-pos', views.save_pos, name="save-pos"),
    path('sales', views.salesList, name="sales-page"),
    path('receipt', views.receipt, name="receipt-modal"),
    path('delete_sale', views.delete_sale, name="delete-sale"),
    path('register/', views.register_user, name='register_user'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/register-cashier/', views.register_cashier_page, name='register_cashier'),
    path('system-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('system-admin/create_store/', views.create_store, name='create_store'),
    path('system-admin/users/', views.user_list, name='user_list'),
    path('system-admin/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('pos/', views.pos, name='cashier-dashboard'), 
    path('system-admin/create_store_and_manager/', views.create_store_and_manager, name='create_store_and_manager'),
    path('expenditures/', views.expenditure_list, name='expenditure_list'),
    path('expenditures/add/', views.add_expenditure, name='add_expenditure'),
    path('expenditures/report/', views.expenditure_report, name='expenditure-report'),
    path('stock/', views.stock_overview, name='stock-overview'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    path('customers/', views.customer_list, name='customer-list'),
    path('suppliers/', views.supplier_list, name='supplier-list'),
    path('stock/add/', views.add_stock_entry, name='add_stock_entry'),
    path('stock/list/', views.stock_entry_list, name='stock_entry_list'),
    path('report/', views.report_view, name='sales-report'),
    path('expenditure/delete/<int:pk>/', views.delete_expenditure, name='delete_expenditure'),
    path('credit-sales/', views.credit_sales, name='credit-sales'),
    path('credit-sales/report/', views.credit_sales_report, name='credit-sales-report')



    # path('employees', views.employees, name="employee-page"),
    # path('manage_employees', views.manage_employees, name="manage_employees-page"),
    # path('save_employee', views.save_employee, name="save-employee-page"),
    # path('delete_employee', views.delete_employee, name="delete-employee"),
    # path('view_employee', views.view_employee, name="view-employee-page"),
]