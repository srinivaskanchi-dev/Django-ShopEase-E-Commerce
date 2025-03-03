from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Product, Category, Customer, Cart, CartItem, Order, OrderItem, EmailVerificationToken
from .forms import CustomUserCreationForm, CheckoutForm, UserUpdateForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage, send_mail
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseRedirect
from decimal import Decimal
from django.db.models import Q, Sum, F
from django.core.paginator import Paginator
from .utils import send_verification_email
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie, requires_csrf_token
import logging
import json
from django.db import transaction
from django.conf import settings
from django.utils.html import strip_tags
from django.urls import reverse, reverse_lazy
import uuid
from django.utils.decorators import method_decorator
from django.views.generic.edit import FormView
import time
from django.utils import timezone
from django.db.models import Prefetch
from django.contrib.auth.tokens import default_token_generator

logger = logging.getLogger(__name__)

# Create your views here.

def get_common_context(request):
    """Helper function to get common context data"""
    context = {
        'categories': Category.objects.all()
    }
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            # Use cart_items instead of cartitem_set
            cart_count = cart.cart_items.all().count()
            context['cart_count'] = cart_count
        except Cart.DoesNotExist:
            context['cart_count'] = 0
    else:
        context['cart_count'] = 0
        
    return context

def home(request):
    products = Product.objects.all()
    featured_products = Product.objects.filter(is_featured=True)
    latest_products = Product.objects.order_by('-created_at')[:8]
    categories = Category.objects.all()
    
    # Debug prints
    print("Total products:", products.count())
    print("Featured products:", featured_products.count())
    print("Latest products:", latest_products.count())
    
    context = {
        'products': products,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    }
    
    return render(request, 'store/home.html', context)

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False  # Deactivate user until email is verified
            user.save()
            
            # Create verification token
            verification_token = EmailVerificationToken.objects.create(user=user)
            
            # Send verification email with request parameter
            send_verification_email(request, user, verification_token.token)
            
            messages.success(request, 'Please check your email to verify your account.')
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect to the stored URL or home
            next_url = request.session.get('next', 'home')
            if 'next' in request.session:
                del request.session['next']
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'store/login.html', {
        'categories': Category.objects.all()
    })

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('home')

@login_required
def profile(request):
    user = request.user
    try:
        # Get user's orders
        orders = Order.objects.filter(user=user).order_by('-created_at')
        
        context = {
            'user': user,
            'orders': orders,
            'categories': Category.objects.all()
        }
        return render(request, 'store/profile.html', context)
    except Exception as e:
        messages.error(request, f'Error loading profile: {str(e)}')
        return redirect('home')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        try:
            user = request.user
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return redirect('profile')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        
        # Update customer profile
        customer = Customer.objects.get(user=user)
        customer.email_verified = True
        customer.save()
        
        messages.success(request, 'Thank you for confirming your email. You can now login.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid or has expired!')
        return redirect('login')

def calculate_total_with_shipping(subtotal):
    SHIPPING_THRESHOLD = 500  # Free shipping threshold
    SHIPPING_CHARGE = 40      # Shipping charge for orders below threshold
    
    if subtotal < SHIPPING_THRESHOLD:
        return subtotal + SHIPPING_CHARGE, SHIPPING_CHARGE
    return subtotal, 0

@login_required
def cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart).select_related('product')
        subtotal = sum(item.quantity * item.product.price for item in cart_items)
        total, shipping = calculate_total_with_shipping(subtotal)
        
        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
            'categories': Category.objects.all()
        }
        return render(request, 'store/cart.html', context)
        
    except Cart.DoesNotExist:
        context = {
            'cart_items': [],
            'subtotal': 0,
            'shipping': 0,
            'total': 0,
            'categories': Category.objects.all()
        }
        return render(request, 'store/cart.html', context)

@require_POST
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        request.session['next'] = request.META.get('HTTP_REFERER', '/')
        messages.info(request, 'Please login to add items to your cart')
        return redirect('login')
    
    try:
        with transaction.atomic():
            product = get_object_or_404(Product, id=product_id)
            cart, _ = Cart.objects.get_or_create(user=request.user)
            
            quantity = int(request.POST.get('quantity', 1))
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity = F('quantity') + quantity
                cart_item.save()
                cart_item.refresh_from_db()
        
        # Store the message in session to prevent duplication
        if 'cart_message' not in request.session:
            messages.success(request, f'{product.name} added to cart')
            request.session['cart_message'] = True
            request.session.modified = True
        
        if request.POST.get('goto_cart'):
            return redirect('cart')
        
        # Clear the message flag after redirect
        if 'cart_message' in request.session:
            del request.session['cart_message']
        
        return redirect(request.META.get('HTTP_REFERER', 'home'))
        
    except Exception as e:
        messages.error(request, 'Error adding product to cart')
        return redirect('home')

@login_required
@transaction.atomic
def update_cart(request, item_id):
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(CartItem, 
                                        id=item_id, 
                                        cart__user=request.user)
            action = request.POST.get('action')
            
            print(f"Updating cart item: {cart_item.product.name}, Action: {action}")  # Debug print
            
            if action == 'increment':
                cart_item.quantity = F('quantity') + 1
                cart_item.save()
                cart_item.refresh_from_db()
            elif action == 'decrement':
                if cart_item.quantity > 1:
                    cart_item.quantity = F('quantity') - 1
                    cart_item.save()
                    cart_item.refresh_from_db()
                else:
                    cart_item.delete()
            
        except Exception as e:
            print(f"Error in update_cart: {str(e)}")  # Debug print
            messages.error(request, f'Error updating cart: {str(e)}')
    
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            cart_item.delete()
        except Exception as e:
            print(f"Error in remove_from_cart: {str(e)}")  # Debug print
            messages.error(request, 'Error removing item from cart.')
    return redirect('cart')

def send_order_confirmation_email(order, email, first_name, last_name):
    subject = f'Order Confirmation - #{order.id}'
    
    # Format the shipping address
    shipping_address = f"{order.address}, {order.city}, {order.state}"
    
    message = f"""Hi {first_name} {last_name},
Thank you for your order! Your order #{order.id} has been received and is being processed.

Customer Information:
Name: {first_name} {last_name}
Email: {email}
Phone: {order.phone}

Shipping Address:
{shipping_address}

Order Details:"""
    
    # Add order items
    for item in order.items.all():
        message += f"\n{item.product.name} x {item.quantity} = ₹{item.price * item.quantity:.2f}"
    
    message += f"""

Subtotal: ₹{order.total_amount:.2f}
Shipping: Free
Total: ₹{order.total_amount:.2f}"""
    
    # Send email
    email = EmailMessage(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email]
    )
    email.send(fail_silently=False)

@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart).select_related('product')
        
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty')
            return redirect('cart')
        
        # Calculate totals
        subtotal = sum(item.quantity * item.product.price for item in cart_items)
        total, shipping = calculate_total_with_shipping(subtotal)
        
        if request.method == 'POST':
            form = CheckoutForm(request.POST)
            if form.is_valid():
                try:
                    # Create order with form data
                    order = Order.objects.create(
                        user=request.user,
                        email=form.cleaned_data['email'],
                        phone=form.cleaned_data['phone'],
                        address=form.cleaned_data['address'],
                        city=form.cleaned_data['city'],
                        state=form.cleaned_data['state'],
                        pincode=form.cleaned_data['pincode'],
                        total_amount=total
                    )
                    
                    # Create order items
                    for cart_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=cart_item.product,
                            quantity=cart_item.quantity,
                            price=cart_item.product.price
                        )
                    
                    # Send confirmation email
                    send_order_confirmation_email(order, form.cleaned_data['email'], form.cleaned_data['first_name'], form.cleaned_data['last_name'])
                    
                    # Clear cart
                    cart_items.delete()
                    
                    messages.success(request, 'Order placed successfully! Check your email for confirmation.')
                    return redirect('order_detail', order_id=order.id)
                    
                except Exception as e:
                    print(f"Error in order creation: {str(e)}")
                    messages.error(request, 'Error creating order. Please try again.')
                    return redirect('checkout')
        else:
            # Pre-fill form with user information
            form = CheckoutForm(initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email
            })
        
        context = {
            'form': form,
            'cart_items': cart_items,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
            'categories': Category.objects.all()
        }
        return render(request, 'store/checkout.html', context)
        
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty')
        return redirect('cart')

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {
        'order': order,
    })

@login_required
def order_history(request):
    # Get all orders for the current user with their items
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Prefetch related items and products
    orders = orders.prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('product'))
    )

    context = {
        'orders': orders,
        'categories': Category.objects.all()
    }
    
    return render(request, 'store/order_history.html', context)

def search_products(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort = request.GET.get('sort', '-created_at')  # Default sort by newest
    
    # Base queryset
    products = Product.objects.all()
    
    # Search query
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
        # Category filter
    if category:
        products = products.filter(category_id=category)
    
    # Price range filter
    if min_price:
        products = products.filter(price__gte=float(min_price))
    if max_price:
        products = products.filter(price__lte=float(max_price))
    
    # Sorting
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    else:  # Default sort by newest
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 9)  # 9 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'query': query,
        'categories': Category.objects.all(),
        'selected_category': category,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
    }
    return render(request, 'store/search_results.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Add your contact form processing logic here
        messages.success(request, 'Thank you for your message. We will get back to you soon!')
        return redirect('contact')
    return render(request, 'store/contact.html', {'categories': Category.objects.all()})

def verify_email(request, token):
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        
        if not verification_token.is_verified:
            user = verification_token.user
            user.is_active = True
            user.save()
            
            verification_token.is_verified = True
            verification_token.save()
            
            messages.success(request, 'Your email has been verified. You can now login.')
        else:
            messages.info(request, 'Email already verified.')
            
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
    
    return redirect('login')

@login_required
def order_detail(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        context = {
            'order': order,
            'categories': Category.objects.all()
        }
        return render(request, 'store/order_detail.html', context)
    except Exception as e:
        messages.error(request, f'Error loading order: {str(e)}')
        return redirect('profile')

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)

def cart_count(request):
    if request.user.is_authenticated:
        cart = Cart.objects.get(user=request.user)
        count = cart.get_total_items()
    else:
        count = 0
    return JsonResponse({'count': count})

@login_required
@require_POST
def update_cart_quantity(request, item_id):
    logger.info(f"Received request to update cart item {item_id}")
    print(f"Updating cart item: {item_id}")  # Debug print
    
    try:
        # Get cart item
        cart_item = get_object_or_404(CartItem, 
            id=item_id,
            cart__user=request.user
        )
        
        action = request.POST.get('action')
        print(f"Action: {action}")  # Debug print
        
        if action == 'increment':
            cart_item.quantity += 1
        elif action == 'decrement' and cart_item.quantity > 1:
            cart_item.quantity -= 1
        
        cart_item.save()
        
        # Get updated cart totals
        cart = cart_item.cart
        subtotal = cart.get_total_price()
        shipping = Decimal('50.00') if subtotal < Decimal('500.00') else Decimal('0.00')
        total = subtotal + shipping
        
        response_data = {
            'success': True,
            'quantity': cart_item.quantity,
            'item_total': float(cart_item.get_total()),
            'subtotal': float(subtotal),
            'shipping': float(shipping),
            'total': float(total),
            'free_shipping': subtotal >= Decimal('500.00'),
            'cart_count': cart.get_total_items()
        }
        
        print(f"Response data: {response_data}")  # Debug print
        return JsonResponse(response_data)
        
    except CartItem.DoesNotExist:
        logger.error(f"Cart item {item_id} not found")
        return JsonResponse({
            'success': False,
            'error': 'Cart item not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error updating cart: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    
    context = get_common_context(request)
    context.update({
        'category': category,
        'products': products,
    })
    
    return render(request, 'store/category_products.html', context)

def about(request):
    return render(request, 'store/about.html', {'categories': Category.objects.all()})

def update_cart_count(request):
    """AJAX view to get updated cart count"""
    if request.user.is_authenticated:
        cart_count = request.user.cart.cartitem_set.all().count()
        return JsonResponse({'cart_count': cart_count})
    return JsonResponse({'cart_count': 0})

@login_required
def place_order(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Get cart
                    cart = Cart.objects.get(user=request.user)
                    cart_items = cart.cart_items.all()
                    
                    if not cart_items.exists():
                        messages.error(request, 'Your cart is empty')
                        return redirect('cart')

                    # Calculate total
                    total_amount = Decimal('0.00')
                    for item in cart_items:
                        total_amount += Decimal(str(item.product.price)) * item.quantity

                    # Generate order number
                    timestamp = str(int(time.time()))[-6:]
                    random_str = str(uuid.uuid4().hex)[:4]
                    order_number = f'O{timestamp}{random_str}'

                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        order_number=order_number,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        email=form.cleaned_data['email'],
                        phone=form.cleaned_data['phone'],
                        address=form.cleaned_data['address'],
                        city=form.cleaned_data['city'],
                        state=form.cleaned_data['state'],
                        pincode=form.cleaned_data['pincode'],
                        total_amount=total_amount,
                        status='Pending'
                    )

                    # Create order items
                    for cart_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=cart_item.product,
                            quantity=cart_item.quantity,
                            price=cart_item.product.price
                        )

                    # Clear cart
                    cart_items.delete()

                # Send email with full name
                try:
                    send_order_confirmation_email(
                        order=order,
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name']
                    )
                except Exception as e:
                    print(f"Email error: {str(e)}")

                messages.success(request, 'Order placed successfully!')
                return redirect('order_confirmation', order_id=order.id)

            except Exception as e:
                print(f"Error in order creation: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                messages.error(request, 'Error creating order. Please try again.')
                return redirect('checkout')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please fill all required fields.')
            return redirect('checkout')

    # GET request
    form = CheckoutForm(initial={
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
    })

    cart = Cart.objects.get(user=request.user)
    cart_items = cart.cart_items.all()
    subtotal = sum(item.quantity * item.product.price for item in cart_items)
    shipping = 0 if subtotal >= 500 else 50
    total = subtotal + shipping

    return render(request, 'store/checkout.html', {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'categories': Category.objects.all()
    })

def category_view(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        products = Product.objects.filter(category=category)
        context = {
            'category': category,
            'products': products,
            'categories': Category.objects.all()
        }
        return render(request, 'store/category.html', context)
    except Category.DoesNotExist:
        messages.error(request, 'Category not found')
        return redirect('home')

def faq(request):
    return render(request, 'store/faq.html', {'categories': Category.objects.all()})

def privacy(request):
    return render(request, 'store/privacy.html', {'categories': Category.objects.all()})

def terms(request):
    return render(request, 'store/terms.html', {'categories': Category.objects.all()})

@method_decorator(csrf_protect, name='dispatch')
class RegisterView(FormView):
    template_name = 'store/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = False
                user.email = form.cleaned_data.get('email')
                user.save()
                
                token = EmailVerificationToken.objects.create(
                    user=user,
                    token=uuid.uuid4()
                )
                
                current_site = get_current_site(self.request)
                mail_subject = 'Activate your ShopEase account'
                message = render_to_string('store/email/verify_email.html', {
                    'user': user,
                    'verification_url': f'http://{current_site.domain}/verify-email/{token.token}/'
                })
                
                email = EmailMessage(
                    mail_subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [user.email]
                )
                email.content_subtype = 'html'
                email.send(fail_silently=False)
                
                messages.success(self.request, 'Registration successful! Please check your email to verify your account.')
                return super().form_valid(form)
                
        except Exception as e:
            messages.error(self.request, 'Registration failed. Please try again.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

@require_POST
def clear_message(request):
    if 'show_message' in request.session:
        del request.session['show_message']
    if 'message' in request.session:
        del request.session['message']
    return JsonResponse({'status': 'ok'})

def send_verification_email(request, user, token):
    current_site = get_current_site(request)
    verification_url = f'http://{current_site.domain}/verify-email/{token}/'
    
    subject = 'Verify your email address'
    message = render_to_string('store/email/verify_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    
    email = EmailMessage(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
    )
    email.content_subtype = 'html'
    email.send()

@ensure_csrf_cookie
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                
                token = EmailVerificationToken.objects.create(
                    user=user,
                    token=uuid.uuid4()
                )
                
                current_site = get_current_site(request)
                mail_subject = 'Activate your ShopEase account'
                message = render_to_string('store/email/verify_email.html', {
                    'user': user,
                    'verification_url': f'http://{current_site.domain}/verify-email/{token.token}/'
                })
                
                email = EmailMessage(
                    mail_subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [form.cleaned_data.get('email')]
                )
                email.content_subtype = 'html'
                email.send(fail_silently=False)
                
                messages.success(request, 'Registration successful! Please check your email to verify your account.')
                return redirect('login')
                
            except Exception as e:
                print(f"Error during registration: {str(e)}")
                messages.error(request, 'Registration failed. Please try again.')
                if user:
                    user.delete()
                return redirect('register')
    else:
        form = CustomUserCreationForm()
    
    response = render(request, 'store/register.html', {
        'form': form,
        'categories': Category.objects.all()
    })
    response.set_cookie('csrftoken', request.META.get('CSRF_COOKIE', ''))
    return response

def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            current_site = get_current_site(request)
            reset_url = f"http://{current_site.domain}/reset-password-confirm/{uid}/{token}/"
            
            # Send email
            subject = 'Password Reset Request'
            message = render_to_string('store/email/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
                'site_name': current_site.name,
            })
            
            send_mail(
                subject,
                message,
                'noreply@yourstore.com',
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
            
    return render(request, 'store/password_reset.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if password1 and password2 and password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
        
        return render(request, 'store/password_reset_confirm.html')
    else:
        messages.error(request, 'Password reset link is invalid or has expired.')
        return redirect('password_reset')

