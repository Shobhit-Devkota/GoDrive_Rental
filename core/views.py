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
        {"name": "Team Member 1", "role": "Founder / Developer", "photo": "https://placehold.co/200x200/1D4ED8/FFFFFF?text=1"},
        {"name": "Team Member 2", "role": "Co-Founder / Operations", "photo": "https://placehold.co/200x200/0D9488/FFFFFF?text=2"},
        {"name": "Team Member 3", "role": "Design", "photo": "https://placehold.co/200x200/111827/FFFFFF?text=3"},
        {"name": "Team Member 4", "role": "Marketing", "photo": "https://placehold.co/200x200/E0F2FE/111827?text=4"},
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
