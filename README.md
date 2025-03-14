# Django-ShopEase-E-Commerce-Website

A modern, fully-functional e-commerce web application built with Django.

## Tech Stack
### Backend
- Python
- Django
- Django REST Framework
- SQLite/MySQL

### Frontend
- HTML
- CSS
- JavaScript
- Bootstrap (for responsive UI)

### Project Structure
```
Django-ShopEase-E-Commerce/
│-- manage.py         # Django project manager
│-- db.sqlite3        # Database file
│-- requirements.txt  # Dependencies
│-- .env              # Environment variables
│-- shopease/         # Main application module
│   │-- models.py     # Database models
│   │-- views.py      # Business logic
│   │-- templates/    # HTML templates
│   │-- static/       # CSS, JS, images
│   │-- urls.py       # URL routing
│   │-- forms.py      # Django forms handling
│   │-- admin.py      # Admin panel configurations
│   │-- serializers.py# DRF serializers for API endpoints
└-- templates/
    └-- base.html     # Main template
```

## Installation & Setup
1. Clone the Repository
```bash
git clone https://github.com/yourusername/Django-ShopEase.git
cd Django-ShopEase-E-Commerce
```

2. Create a Virtual Environment & Activate
```bash
git clone https://github.com/yourusername/Django-ShopEase.git
cd Django-ShopEase-E-Commerce
```

3. Install Dependencies
```bash
pip install -r requirements.txt
```

4. Run Migrations & Start Server
```bash
python manage.py migrate
python manage.py runserver
```
Access the application at [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Features
- ✅ User Authentication & Registration
- ✅ Product Listing & Search
- ✅ Shopping Cart & Checkout
- ✅ Order Management

## Contributing
Feel free to fork this repository and contribute! Pull requests are welcome.

## Live Demo
Visit [ShopEase](https://shopease.pythonanywhere.com)

## Developer
- Name: Srinivas Kanchi
- GitHub: https://github.com/srinivaskanchi-dev
- Email: srinivaskanchi752@gmail.com
