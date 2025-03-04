from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    context = {
        'page_title': 'Dashboard'
    }
    return render(request, 'core/dashboard.html', context)