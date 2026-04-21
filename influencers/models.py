from django.db import models
from django.conf import settings


class InfluencerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    phone = models.CharField(max_length=20, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='influencer_photos/', blank=True, null=True)
    profile_image = models.ImageField(upload_to='influencer_profiles/', null=True, blank=True)
    banner_image = models.ImageField(upload_to='influencer_banners/', null=True, blank=True)

    street = models.CharField(max_length=200, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    pincode = models.CharField(max_length=10, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='India')

    bio = models.TextField(blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')
    price_per_post = models.IntegerField(default=0)

    followers = models.IntegerField(default=0)

    instagram = models.URLField(blank=True, default='')
    youtube = models.URLField(blank=True, default='')
    twitter = models.URLField(blank=True, default='')

    rate_instagram_post = models.IntegerField(default=3000)
    rate_instagram_story = models.IntegerField(default=1500)
    rate_youtube_integration = models.IntegerField(default=8000)
    rate_youtube_dedicated = models.IntegerField(default=15000)
    rate_twitter_thread = models.IntegerField(default=2000)
    rate_brand_package = models.IntegerField(default=25000)

    sms_auth = models.BooleanField(default=True)
    authenticator_app = models.BooleanField(default=False)
    login_alerts = models.BooleanField(default=True)

    public_profile = models.BooleanField(default=True)
    show_earnings = models.BooleanField(default=False)
    show_analytics = models.BooleanField(default=True)
    accept_dm = models.BooleanField(default=True)

    notif_new_booking = models.BooleanField(default=True)
    notif_booking_approved = models.BooleanField(default=True)
    notif_payment_received = models.BooleanField(default=True)
    notif_weekly_report = models.BooleanField(default=False)
    notif_announcements = models.BooleanField(default=False)
    notif_inapp = models.BooleanField(default=True)
    notif_browser_push = models.BooleanField(default=False)
    notif_sms = models.BooleanField(default=False)
    notif_sound = models.BooleanField(default=True)

    instant_payouts = models.BooleanField(default=True)
    auto_withdraw = models.BooleanField(default=False)

    show_rate_card = models.BooleanField(default=True)
    accept_custom_offers = models.BooleanField(default=True)

    is_paused = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


from django.contrib import admin
admin.site.register(InfluencerProfile)