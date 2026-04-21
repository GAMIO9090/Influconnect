from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from .models import InfluencerProfile
from bookings.models import Booking

STATES = [
    'Andhra Pradesh', 'Delhi', 'Gujarat', 'Haryana', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Punjab', 'Rajasthan',
    'Tamil Nadu', 'Telangana', 'Uttar Pradesh', 'West Bengal',
]

CATEGORIES = [
    'Fashion', 'Food', 'Travel', 'Tech', 'Fitness',
    'Beauty', 'Gaming', 'Education', 'Lifestyle', 'Finance',
]


@login_required
def influencer_dashboard(request):
    profile, created = InfluencerProfile.objects.get_or_create(user=request.user)
    total_bookings = Booking.objects.filter(influencer=profile).count()
    accepted_bookings = Booking.objects.filter(influencer=profile, status='approved').count()
    total_earnings = Booking.objects.filter(influencer=profile, status='approved').aggregate(
        total=models.Sum('amount'))['total'] or 0
    recent_bookings = Booking.objects.filter(influencer=profile).order_by('-created_at')[:5]

    return render(request, 'influencers/dashboard.html', {
        'profile': profile,
        'total_requests': total_bookings,
        'accepted_requests': accepted_bookings,
        'total_earnings': total_earnings,
        'bookings': recent_bookings,
    })


@login_required
def edit_profile(request):
    profile, created = InfluencerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        profile.phone = request.POST.get('phone', '')
        profile.date_of_birth = request.POST.get('date_of_birth') or None
        profile.street = request.POST.get('street', '')
        profile.city = request.POST.get('city', '')
        profile.state = request.POST.get('state', '')
        profile.pincode = request.POST.get('pincode', '')
        profile.country = request.POST.get('country', 'India')
        profile.bio = request.POST.get('bio', '')
        profile.category = request.POST.get('category', '')
        profile.location = request.POST.get('location', '')
        profile.price_per_post = request.POST.get('price_per_post', 0) or 0
        profile.instagram = request.POST.get('instagram', '')
        profile.youtube = request.POST.get('youtube', '')
        profile.twitter = request.POST.get('twitter', '')

        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']

        if 'banner_image' in request.FILES:
            profile.banner_image = request.FILES['banner_image']

        profile.save()
        messages.success(request, 'Profile saved successfully!')
        return redirect('influencers:edit_profile')

    return render(request, 'influencers/edit_profile.html', {
        'profile': profile,
        'states': STATES,
        'categories': CATEGORIES,
    })


def influencers_list(request):
    influencers = InfluencerProfile.objects.all()
    return render(request, 'influencers/influencers.html', {'influencers': influencers})


def influencer_detail(request, id):
    influencer = get_object_or_404(InfluencerProfile, id=id)

    booking_id = None
    if request.user.is_authenticated:
        booking = Booking.objects.filter(
            shopkeeper=request.user,
            influencer=influencer
        ).first()
        if booking:
            booking_id = booking.id

    return render(request, 'influencers/detail.html', {
        'influencer': influencer,
        'booking_id': booking_id,
    })


@login_required
def settings_view(request):
    profile, created = InfluencerProfile.objects.get_or_create(user=request.user)
    total_bookings = Booking.objects.filter(influencer=profile).count()

    if request.method == 'POST':
        section = request.POST.get('section')

        if section == 'profile':
            user = request.user
            full_name = request.POST.get('full_name', '')
            parts = full_name.strip().split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
            user.email = request.POST.get('email', '')
            user.save()

            profile.bio = request.POST.get('bio', '')
            profile.location = request.POST.get('location', '')
            profile.category = request.POST.get('niche', '')
            profile.phone = request.POST.get('phone', '')
            profile.instagram = request.POST.get('instagram', '')
            profile.youtube = request.POST.get('youtube', '')
            profile.twitter = request.POST.get('twitter', '')

            if 'avatar' in request.FILES:
                profile.photo = request.FILES['avatar']

            profile.save()
            messages.success(request, 'Profile updated successfully!')

        elif section == 'password':
            current = request.POST.get('current_password')
            new_pw = request.POST.get('new_password')
            confirm = request.POST.get('confirm_password')

            if not request.user.check_password(current):
                messages.error(request, 'Current password is incorrect.')
            elif new_pw != confirm:
                messages.error(request, 'New passwords do not match.')
            elif len(new_pw) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                request.user.set_password(new_pw)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')

        elif section == 'rates':
            def safe_int(val, default=0):
                try:
                    return max(0, int(val))
                except (TypeError, ValueError):
                    return default

            profile.rate_instagram_post = safe_int(request.POST.get('rate_instagram_post'), 3000)
            profile.rate_instagram_story = safe_int(request.POST.get('rate_instagram_story'), 1500)
            profile.rate_youtube_integration = safe_int(request.POST.get('rate_youtube_integration'), 8000)
            profile.rate_youtube_dedicated = safe_int(request.POST.get('rate_youtube_dedicated'), 15000)
            profile.rate_twitter_thread = safe_int(request.POST.get('rate_twitter_thread'), 2000)
            profile.rate_brand_package = safe_int(request.POST.get('rate_brand_package'), 25000)
            profile.price_per_post = profile.rate_instagram_post
            profile.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Rate card saved!'})
            messages.success(request, 'Rate card updated successfully!')

        return redirect('influencers:settings')

    return render(request, 'influencers/settings.html', {
        'profile': profile,
        'total_requests': total_bookings,
        'categories': CATEGORIES,
        'states': STATES,
    })