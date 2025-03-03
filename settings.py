# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Or your email provider's SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'shopease.ecomweb@gmail.com'
EMAIL_HOST_PASSWORD = 'tugc sdmr ycco skym'

SITE_NAME = 'ShopEase'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'store',
]

SITE_ID = 1

# Add these settings for email templates
DEFAULT_FROM_EMAIL = 'noreply@shopease.com'
EMAIL_SUBJECT_PREFIX = '[ShopEase] '
DOMAIN = 'shopease.com'