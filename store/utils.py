from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from store.models import Order

def send_verification_email(request, user, token):
    current_site = get_current_site(request)
    verification_url = f"http://{current_site.domain}/verify-email/{token}"
    
    context = {
        'user': user,
        'verification_url': verification_url
    }
    
    html_message = render_to_string('email/verification_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        'Verify your email - ShopEase',
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    ) 