from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from influencers.models import InfluencerProfile
from google import genai
import json
import time
import urllib.request
import urllib.parse


def call_gemini_with_retry(client, prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text if hasattr(response, "text") else "No response"
        except Exception as e:
            err = str(e)
            if any(code in err for code in ["503", "500", "UNAVAILABLE", "overloaded"]) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def search_instagram_users(query, max_results=9):
    """Real Instagram users search via RapidAPI Instagram Scraper 2025."""
    rapidapi_key  = getattr(settings, "RAPIDAPI_KEY", "")
    rapidapi_host = getattr(settings, "RAPIDAPI_HOST", "instagram-scraper-20251.p.rapidapi.com")

    if not rapidapi_key:
        return []

    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://{rapidapi_host}/usersearch/?search_query={encoded_query}"

        req = urllib.request.Request(url)
        req.add_header("x-rapidapi-key",  rapidapi_key)
        req.add_header("x-rapidapi-host", rapidapi_host)
        req.add_header("Accept",          "application/json")

        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = json.loads(resp.read().decode())

        
        users_raw = []
        if isinstance(raw, list):
            users_raw = raw
        elif isinstance(raw, dict):
            users_raw = (
                raw.get("users") or
                raw.get("data", {}).get("users", []) or
                raw.get("results", []) or
                raw.get("items", []) or
                []
            )

        results = []
        for u in users_raw[:max_results]:
            if "node" in u:
                u = u["node"]

            username  = u.get("username") or u.get("handle") or ""
            full_name = u.get("full_name") or u.get("name") or username
            followers = int(
                u.get("follower_count") or
                u.get("followers") or
                u.get("edge_followed_by", {}).get("count", 0) or 0
            )
            bio = (
                u.get("biography") or
                u.get("bio") or
                u.get("description") or ""
            )[:120]
            pic = (
                u.get("profile_pic_url") or
                u.get("profile_picture") or
                u.get("hd_profile_pic_url_info", {}).get("url", "") or ""
            )
            verified = bool(u.get("is_verified") or u.get("verified"))

            if username:
                results.append({
                    "username":    username,
                    "full_name":   full_name or username,
                    "followers":   followers,
                    "bio":         bio or f"Instagram creator from {username}",
                    "profile_url": f"https://www.instagram.com/{username}/",
                    "pic_url":     pic,
                    "is_verified": verified,
                })

        return results

    except Exception as e:
        print(f"[Instagram API ERROR] {type(e).__name__}: {e}")
        return []


def _estimate_rate(followers):
    if followers >= 500_000:
        return min(150_000, (followers // 10))
    if followers >= 50_000:
        return min(30_000, (followers // 20))
    return max(500, (followers // 15))


@csrf_exempt
def ai_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Sirf POST request allowed hai"}, status=405)

    try:
        data         = json.loads(request.body)
        user_message = data.get("message", "").strip()
        language     = data.get("language", "Hinglish")
        name         = data.get("name", "User")

        if not user_message:
            return JsonResponse({"error": "Message empty hai"}, status=400)

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        lang_instruction = {
            "Hindi":    "Sirf Hindi mein jawab do.",
            "English":  "Reply only in English.",
            "Hinglish": "Hinglish mein jawab do (Hindi + English mix).",
        }.get(language, "Hinglish mein jawab do.")

        prompt = (
            f"Tum InfluConnect platform ka helpful AI assistant ho. "
            f"{lang_instruction} User ka naam {name} hai. "
            f"Sirf influencer marketing, bookings, platform features, "
            f"aur local business promotion se related sawaalon ka jawab do. "
            f"Agar sawaal off-topic ho toh politely redirect karo. "
            f"User ka sawaal: {user_message}"
        )

        reply = call_gemini_with_retry(client, prompt)
        return JsonResponse({"reply": reply})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        err = str(e)
        print(f"[AI Chat ERROR] {err}")
        if "429" in err:
            return JsonResponse({"reply": "⚠️ Thoda wait karo, API limit hit ho gayi. 1 minute baad try karo!"})
        return JsonResponse({"reply": "⚠️ Kuch galat ho gaya. Please thodi der baad try karo."})


@csrf_exempt
def ai_find_influencers(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data          = json.loads(request.body)
        city          = data.get("city", "").strip()
        niche         = data.get("niche", "All")
        min_followers = int(data.get("minFollowers", 0) or 0)
        max_budget    = int(data.get("maxBudget", 9999999) or 9999999)

        if not city:
            return JsonResponse({"error": "City required"}, status=400)

        city_clean  = city.split(",")[0].strip()
        niche_clean = "" if niche == "All" else niche.lower()

        
        queries = []
        if niche_clean:
            queries = [
                f"{niche_clean} influencer {city_clean}",
                f"{city_clean} {niche_clean}",
                f"{niche_clean} {city_clean} blogger",
            ]
        else:
            queries = [
                f"influencer {city_clean}",
                f"{city_clean} content creator",
                f"{city_clean} blogger",
            ]

        real_users   = []
        seen         = set()

        for q in queries:
            if len(real_users) >= 9:
                break
            for u in search_instagram_users(q, max_results=9):
                if u["username"] not in seen:
                    seen.add(u["username"])
                    real_users.append(u)

        
        if min_followers > 0:
            real_users = [u for u in real_users if u["followers"] >= min_followers]

        
        if real_users:
            formatted = []
            for u in real_users[:9]:
                rate = _estimate_rate(u["followers"])
                if rate > max_budget:
                    continue
                formatted.append({
                    "name":           u["full_name"],
                    "handle":         u["username"],
                    "niche":          niche if niche != "All" else "Creator",
                    "followers":      u["followers"],
                    "engagementRate": round(2.5 + (hash(u["username"]) % 60) / 10, 1),
                    "avgReelViews":   max(500, u["followers"] // 10),
                    "ratePerPost":    rate,
                    "bio":            u["bio"],
                    "verified":       u["is_verified"],
                    "profile_url":    u["profile_url"],
                    "pic_url":        u["pic_url"],
                    "is_real":        True,
                })

            if formatted:
                return JsonResponse({"influencers": formatted, "city": city, "source": "instagram_real"})

        
        print(f"[INFO] No real results for '{city_clean}', using Gemini fallback")
        client     = genai.Client(api_key=settings.GEMINI_API_KEY)
        niche_text = "various niches (food, fashion, beauty, tech, fitness, lifestyle)" if niche == "All" else niche
        budget_note    = f"ratePerPost <= {max_budget}" if max_budget < 9999999 else "no budget limit"
        followers_note = f"followers >= {min_followers}" if min_followers > 0 else "no minimum followers"

        prompt = f"""You are an Instagram influencer discovery AI for India.
Generate exactly 9 realistic mock Instagram influencers from {city}, India in {niche_text}.
Return ONLY a raw JSON array. Each object: name, handle (no @), niche, followers (int),
engagementRate (float 1-8), avgReelViews (int), ratePerPost (int INR), bio (max 12 words), verified (bool).
Followers: 3 nano(5k-50k), 4 micro(50k-500k), 2 macro(500k-2M).
Filter: {followers_note} AND {budget_note}. Start with [ end with ]"""

        raw   = call_gemini_with_retry(client, prompt)
        clean = raw.strip()
        if "```" in clean:
            for part in clean.split("```"):
                p = part.strip().lstrip("json").strip()
                if p.startswith("["):
                    clean = p
                    break

        influencers = json.loads(clean.strip())
        influencers = [
            {
                **inf,
                "is_real":     False,
                "profile_url": f"https://www.instagram.com/explore/search/keyword/?q={urllib.parse.quote(niche_clean + ' ' + city_clean)}",
                "pic_url":     "",
            }
            for inf in influencers
            if inf.get("followers", 0) >= min_followers
            and inf.get("ratePerPost", 0) <= max_budget
        ]

        return JsonResponse({"influencers": influencers, "city": city, "source": "ai_generated"})

    except json.JSONDecodeError as e:
        return JsonResponse({"error": f"JSON error: {str(e)}"}, status=500)
    except Exception as e:
        err = str(e)
        print(f"[Find ERROR] {err}")
        if "429" in err:
            return JsonResponse({"error": "API limit. 1 min baad try karo."}, status=429)
        return JsonResponse({"error": f"Server error: {err}"}, status=500)


def home(request):
    if request.user.is_authenticated:
        if hasattr(request.user, "role"):
            if request.user.role == "shopkeeper":
                return redirect("shopkeepers:shopkeeper_dashboard")
            elif request.user.role == "influencer":
                return redirect("influencers:dashboard")

    influencers = InfluencerProfile.objects.all()
    category = request.GET.get("category", "").strip()
    if category:
        influencers = influencers.filter(category=category)
    city = request.GET.get("city", "").strip()
    if city:
        influencers = influencers.filter(location__icontains=city)

    return render(request, "home/index.html", {"influencers": influencers})


def how_it_works(request):
    return render(request, "home/How it works.html")

def privacy_policy(request):
    return render(request, "home/Privacy policy.html")

def contact(request):
    return render(request, "home/Contact.html")

def terms(request):
    return render(request, "home/Terms conditions.html")