from django.contrib import admin
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Category, Product, Customer, Cart, CartItem, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'email_verified')
    search_fields = ('user__email', 'user__username', 'phone_number')
    list_filter = ('email_verified',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'get_total_amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'email', 'first_name', 'last_name']
    inlines = [OrderItemInline]

    def get_total_amount(self, obj):
        return obj.get_total_amount()
    get_total_amount.short_description = 'Total Amount'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('orderitem_set')

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # Send email notification when order status changes
            self.send_status_update_email(obj)
        super().save_model(request, obj, form, change)

    def send_status_update_email(self, order):
        try:
            subject = f'Order #{order.id} Status Update'
            message = render_to_string('store/email/order_status_update_email.html', {
                'order': order,
            })
            email = EmailMessage(
                subject,
                message,
                from_email='srisunny2001@gmail.com',  # Your verified email
                to=[order.user.email],
                reply_to=['srisunny2001@gmail.com'],  # Your support email
            )
            email.send(fail_silently=False)
        except Exception as e:
            # Log the error but don't stop the save process
            print(f"Error sending email: {e}")

class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'get_total_price']
    list_filter = ['created_at']
    search_fields = ['user__username']

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity']
    list_filter = ['cart__created_at']
    search_fields = ['cart__user__username', 'product__name']
