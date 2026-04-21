from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),


    path('how-it-works/', views.how_it_works, name='how_it_works'),


    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),


    path('contact/', views.contact, name='contact'),


    
    path('terms/', views.terms, name='terms'),

    
    path('api/find-influencers/', views.ai_find_influencers, name='ai_find_influencers'),
]