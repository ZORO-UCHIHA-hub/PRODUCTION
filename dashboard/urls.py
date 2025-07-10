from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # Login page
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.branch_dashboard, name='dashboard'),  # Admin/Manager view
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),  # Staff only

    path('orders/', views.orders, name='orders'),
    path('orders/new/', views.neworder, name='neworder'),
    path('orders/<int:sale_id>/edit/', views.edit_order_page, name='edit_order_page'),
    path('orders/<int:sale_id>/update/', views.update_order_data, name='update_order_data'),
    path('orders/thermal-receipt/<int:sale_id>/', views.print_thermal_receipt, name='print_thermal_receipt'),


    path('customers/save/', views.create_or_update_customer, name='save_customer'),
    path('customers/delete/<int:id>/', views.delete_customer, name='delete_customer'),
    path('customer/', views.customer, name='customer'),



    path('employees/', views.employees, name='employees'),
    path('employees/delete/<int:user_id>/', views.delete_employee, name='delete_employee'),
    path('staff/', views.staff, name='staff'),

    path('expense/', views.expenses_view, name='expense'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('expenses/delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    
    path('analytics/', views.analytics_view, name='analytics'),
    path('settings/', views.settings, name='settings'),


    path('products/', views.products, name='products'),
    path('add-product/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.add_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),


    path('ajax/create-branch/', views.create_branch_ajax, name='create_branch_ajax'),

    path("orders/thermal-receipt/<int:sale_id>/", views.print_thermal_receipt, name="print_thermal_receipt"),
    path('orders/print/<int:sale_id>/', views.print_receipt, name='print_receipt'),
    path('orders/delete/<int:sale_id>/', views.delete_order, name='delete_order'),

    path('customers/add/', views.add_customer_ajax, name='add_customer_ajax'),

    path('create-admin/', views.create_admin_view, name='create_admin'),

]
