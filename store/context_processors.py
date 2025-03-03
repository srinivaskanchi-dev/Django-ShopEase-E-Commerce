from .models import Cart, Category

def cart_count(request):
    cart_items_count = 0
    categories = Category.objects.all()
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items_count = cart.total_items
        except Cart.DoesNotExist:
            pass
    
    return {
        'cart_items_count': cart_items_count,
        'categories': categories,
    } 