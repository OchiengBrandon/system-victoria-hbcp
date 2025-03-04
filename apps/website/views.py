from django.shortcuts import render, get_object_or_404
from .models import Item, Category, Tag, ItemImage  # Ensure ItemImage is imported

# Create your views here.
def index(request):
    return render(request, 'index.html')

def gallery_list(request):
    items = Item.objects.all()
    categories = Category.objects.all()
    return render(request, 'gallery_list.html', {'items': items, 'categories': categories})

def gallery_detail(request, slug):
    item = get_object_or_404(Item, slug=slug)
    images = item.images.all()  # Retrieve all related images for the item
    return render(request, 'gallery_detail.html', {'item': item, 'images': images})

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

# In website/views.py
from django.shortcuts import render
from apps.products.models import Product

def products(request):
    query = request.GET.get('search', '')  
    categories = Product.objects.values('category').distinct()  
    products_by_category = {}

    for category in categories:
        products_list = Product.objects.filter(category=category['category'])
        if query:
            products_list = products_list.filter(name__icontains=query)  # Filter products by name
        products_by_category[category['category']] = products_list

    return render(request, 'products.html', {'products_by_category': products_by_category, 'query': query})

def projects(request):
    return render(request, 'projects.html')

def services(request):
    return render(request, 'services.html')