from django.utils import timezone
from django.db import models
from datetime import datetime
from .models import Order, Product, Customer

def get_admin_stats(request):
    today = timezone.now().date()
    
    orders_today = Order.objects.filter(
        created_at__date=today
    ).count()
    
    revenue_today = Order.objects.filter(
        created_at__date=today
    ).aggregate(
        total=models.Sum('total_amount')
    )['total'] or 0
    
    total_products = Product.objects.count()
    total_customers = Customer.objects.count()
    
    return {
        'orders_today': orders_today,
        'revenue_today': revenue_today,
        'total_products': total_products,
        'total_customers': total_customers,
    } 