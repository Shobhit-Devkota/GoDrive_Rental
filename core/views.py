from django.shortcuts import render, redirect
from django.contrib import messages
from vehicles.models import Vehicle
from .forms import ContactForm


def home(request):
    featured_vehicles = Vehicle.objects.filter(is_featured=True).prefetch_related('images')[:10]
    if featured_vehicles.count() < 1:
        featured_vehicles = Vehicle.objects.all().prefetch_related('images')[:10]
    return render(request, 'home.html', {'vehicles': featured_vehicles})


def about(request):
    # Replace these with your real team members — name, role, and a photo URL
    # (upload your own images somewhere and paste the link, or swap in a static file path).
    team_members = [
    {"name": "Shobhit Devkota", "role": "Founder / Developer", "photo": "img/team/member1.jpg"},
    {"name": "Sandhya Paudel", "role": "Co-Founder / Operations", "photo": "img/team/member2.jpg"},
    {"name": "Priyanshu Khanal", "role": "Design", "photo": "img/team/member3.jpg"},
    {"name": "Sanjiv Dahal", "role": "Marketing", "photo": "img/team/member4.jpg"},
    ]
    return render(request, 'about.html', {'team_members': team_members})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for reaching out. Our team will get back to you shortly.")
            return redirect('core:contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})
