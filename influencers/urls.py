from django.urls import path
from . import views
from . import views_security

app_name = 'influencers'

urlpatterns = [

    path('dashboard/', views.influencer_dashboard, name='dashboard'),



    path('settings/', views.settings_view, name='settings'),




    path('edit-profile/', views.edit_profile, name='edit_profile'),


    path('', views.influencers_list, name='influencers_list'),



    path('<int:id>/', views.influencer_detail, name='influencer_detail'),

   
    path("settings/password-change/",  views_security.password_change_ajax, name="password_change_ajax"),


    path("settings/toggle/",           views_security.toggle_setting,        name="toggle_setting"),
    


    path("settings/export-data/",      views_security.export_data,           name="export_data"),



    path("settings/pause-account/",    views_security.pause_account,         name="pause_account"),




    path("settings/delete-account/",   views_security.delete_account,        name="delete_account"),
]