from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import RegisterView

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('cart/count/', views.update_cart_count, name='update_cart_count'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_history, name='order_history'),
    path('category/<int:category_id>/', views.category_view, name='category'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('clear-message/', views.clear_message, name='clear_message'),
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='store/password_reset.html',
             email_template_name='registration/password_reset_email.html',
             success_url='/password-reset/done/'
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='store/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='store/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='store/password_reset_complete.html'
         ),
         name='password_reset_complete'),
] 