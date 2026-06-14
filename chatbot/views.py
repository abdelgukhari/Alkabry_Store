import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from products.models import Product
from recommendations.services import RecommendationService
from .i18n import t

rec_service = None


def get_rec_service():
    global rec_service
    if rec_service is None:
        try:
            rec_service = RecommendationService()
        except Exception:
            rec_service = None
    return rec_service

KEYWORD_MAP = {
    "vestido": "dress",
    "camisa": "shirt",
    "pantalon": "pants",
    "pantalón": "pants",
    "chaqueta": "jacket",
    "abrigo": "coat",
    "zapatos": "shoes",
    "botas": "boots",
    "bolso": "bag",
    "sombrero": "hat",
    "bufanda": "scarf",
    "sudadera": "hoodie",
    "платье": "dress",
    "рубашка": "shirt",
    "куртка": "jacket",
    "пальто": "coat",
    "обувь": "shoes",
    "сапоги": "boots",
    "сумка": "bag",
    "شرت": "shirt",
    "فستان": "dress",
    "جاكيت": "jacket",
    "حذاء": "shoes",
    "حقيبة": "bag",
}


def translate_query(query):
    for word, translation in KEYWORD_MAP.items():
        query = query.replace(word, translation)
    return query


def parse_message(text):
    text_lower = text.lower()
    size = None
    min_price = None
    max_price = None

    size_match = re.search(r'\b(xs|s|m|l|xl|xxl)\b', text_lower)
    if size_match:
        size = size_match.group(1).upper()

    nums = re.findall(r'\d+', text)
    if any(w in text_lower for w in ["under","up to","hasta","menos de","до","below","less","menos"]):
        if nums:
            max_price = float(nums[0])
    elif any(w in text_lower for w in ["over","up","mas de","больше","above","more","mas"]):
        if nums:
            min_price = float(nums[0])
    elif '-' in text and len(nums) >= 2:
        min_price = float(nums[0])
        max_price = float(nums[1])
    elif nums:
        max_price = float(nums[0])

    query = re.sub(r'\b(xs|s|m|l|xl|xxl)\b', '', text_lower)
    query = re.sub(r'(under|up to|hasta|menos de|до|below|less than|up|over|mas de|больше|above|more than|size|talla|размер|مقاس)\s*\d*', '', query)
    query = re.sub(r'\d+', '', query)
    query = re.sub(r'\s+', ' ', query).strip()
    query = translate_query(query)

    return query, size, min_price, max_price


def _apply_filters(qs, query, size, min_price, max_price, apply_size=True):
    if query:
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    if apply_size and size:
        qs = qs.filter(size__icontains=size)
    if min_price:
        qs = qs.filter(price__gte=min_price)
    if max_price:
        qs = qs.filter(price__lte=max_price)
    return qs


def get_products(query, size, min_price, max_price, user, lang):
    base = Product.objects.filter(is_available=True, is_active=True)

    products = list(_apply_filters(base, query, size, min_price, max_price, apply_size=True).order_by("-views_count")[:6])

    # Size field may be blank on all products — retry without size but keep query + price
    if not products and size:
        products = list(_apply_filters(base, query, size, min_price, max_price, apply_size=False).order_by("-views_count")[:6])

    # Last resort: bestsellers (no query/price constraint)
    if not products:
        products = list(base.order_by("-views_count")[:6])

    if user and products:
        try:
            rs = get_rec_service()
            if rs is not None:
                recs = rs.get_recommendations_for_user(user, algorithm="hybrid", limit=6)
                rec_ids = {p.id for p in recs}
                recommended = [p for p in products if p.id in rec_ids]
                others = [p for p in products if p.id not in rec_ids]
                products = (recommended + others)[:6]
        except Exception:
            pass

    products_data = []
    for p in products:
        products_data.append({
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "size": p.size,
            "color": p.color,
            "image": p.image.url if p.image else "",
            "url": p.get_absolute_url(),
            "price_label": t("price_label", lang),
            "size_label": t("size_label", lang),
            "view_product": t("view_product", lang),
        })

    return products_data


@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    data = json.loads(request.body)
    message = data.get("message", "").strip()
    state = data.get("state", "welcome")
    lang = data.get("lang", "en")
    context = data.get("context", {})
    user = request.user if request.user.is_authenticated else None

    if state == "welcome":
        if user:
            reply = t("welcome", lang, name=user.first_name or user.email.split("@")[0])
        else:
            reply = t("welcome_anon", lang)
        return JsonResponse({"reply": reply, "state": "ask_product", "context": {}})

    if state == "ask_product":
        query, size, min_price, max_price = parse_message(message)
        products_data = get_products(query, size, min_price, max_price, user, lang)

        messages = [t("results", lang)]
        if not user:
            messages.append(t("register_hint", lang))
        messages.append(t("found_it", lang))

        return JsonResponse({
            "reply": messages[0],
            "messages": messages,
            "state": "ask_found",
            "context": {},
            "products": products_data
        })

    if state == "ask_found":
        yes_words = ["yes","si","sí","да","نعم","y","yep","sure","found","genial","great","perfect"]
        if message.lower().strip() in yes_words:
            return JsonResponse({
                "reply": t("great", lang),
                "state": "welcome",
                "context": {}
            })
        else:
            return JsonResponse({
                "reply": t("what_else", lang),
                "state": "ask_product",
                "context": {}
            })

    return JsonResponse({"reply": "ok", "state": state, "context": context})