

import json
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import InfluencerProfile


@login_required
@require_POST
def password_change_ajax(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid request format."}, status=400)

    current  = data.get("current_password", "")
    new_pwd  = data.get("new_password", "")
    confirm  = data.get("confirm_password", "")

    if not request.user.check_password(current):
        return JsonResponse({"success": False, "message": "Current password galat hai."}, status=400)
    if len(new_pwd) < 8:
        return JsonResponse({"success": False, "message": "Password kam se kam 8 characters ka hona chahiye."}, status=400)
    if new_pwd != confirm:
        return JsonResponse({"success": False, "message": "Naya password aur confirm password match nahi kar rahe."}, status=400)
    if current == new_pwd:
        return JsonResponse({"success": False, "message": "Naya password purane se alag hona chahiye."}, status=400)

    request.user.set_password(new_pwd)
    request.user.save()
    update_session_auth_hash(request, request.user)

    return JsonResponse({"success": True, "message": "Password successfully change ho gaya! ✓"})


ALLOWED_TOGGLES = {
    "sms_auth", "authenticator_app", "login_alerts",
    "public_profile", "show_earnings", "show_analytics", "accept_dm",
    "notif_new_booking", "notif_booking_approved", "notif_payment_received",
    "notif_weekly_report", "notif_announcements", "notif_inapp",
    "notif_browser_push", "notif_sms", "notif_sound",
    "instant_payouts", "auto_withdraw",
    "show_rate_card", "accept_custom_offers",
}


@login_required
@require_POST
def toggle_setting(request):
    try:
        data  = json.loads(request.body)
        field = data.get("field", "")
        value = bool(data.get("value", False))
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

    if field not in ALLOWED_TOGGLES:
        return JsonResponse({"success": False, "message": f"Unknown setting: {field}"}, status=400)

    try:
        profile = request.user.influencerprofile
    except InfluencerProfile.DoesNotExist:
        return JsonResponse({"success": False, "message": "Profile nahi mila."}, status=404)

    setattr(profile, field, value)
    profile.save(update_fields=[field])

    label = field.replace("_", " ").title()
    state = "enable" if value else "disable"
    return JsonResponse({"success": True, "message": f"{label} {state} ho gaya."})



@login_required
@require_POST
def export_data(request):
    user    = request.user
    profile = getattr(user, "influencerprofile", None)

    payload = {
        "username":    user.username,
        "email":       user.email,
        "full_name":   user.get_full_name(),
        "date_joined": str(user.date_joined),
        "profile": {
            "bio":       getattr(profile, "bio", ""),
            "location":  getattr(profile, "location", ""),
            "instagram": getattr(profile, "instagram", ""),
            "youtube":   getattr(profile, "youtube", ""),
            "twitter":   getattr(profile, "twitter", ""),
        } if profile else {}
    }

    from django.http import HttpResponse
    response = HttpResponse(
        json.dumps(payload, indent=2, ensure_ascii=False),
        content_type="application/json"
    )
    response["Content-Disposition"] = f'attachment; filename="influconnect_data_{user.username}.json"'
    return response



@login_required
@require_POST
def pause_account(request):
    try:
        profile = request.user.influencerprofile
        profile.is_paused = True
        profile.save(update_fields=["is_paused"])
        return JsonResponse({"success": True, "message": "Account pause ho gaya. Koi brand aapko nahi dekh sakta."})
    except InfluencerProfile.DoesNotExist:
        return JsonResponse({"success": False, "message": "Profile nahi mila."}, status=404)



@login_required
@require_POST
def delete_account(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

    password = data.get("confirm_password", "")
    if not request.user.check_password(password):
        return JsonResponse({"success": False, "message": "Password galat hai. Account delete nahi hua."}, status=400)

    from django.contrib.auth import logout
    user = request.user
    logout(request)
    user.delete()

    return JsonResponse({"success": True, "message": "Account permanently delete ho gaya.", "redirect": "/"})