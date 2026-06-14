TRANSLATIONS = {
    "en": {
        "welcome": "Hi {name}! I am Kabbary Assistant. Tell me what you are looking for, your size and budget and I will find the best products for you! (e.g. 'jacket size M under 100')",
        "welcome_anon": "Hi! I am Kabbary Assistant. Tell me what you are looking for, your size and budget and I will find the best products for you! (e.g. 'jacket size M under 100')",
        "results": "Here are my recommendations for you:",
        "no_results": "Sorry, I could not find products matching your criteria. Try different keywords!",
        "register_hint": "Register or log in to get personalized recommendations!",
        "found_it": "Did you find what you were looking for?",
        "great": "Great! Enjoy your purchase. See you soon! 👋",
        "what_else": "What else are you looking for? Tell me the item, size and budget.",
        "price_label": "Price",
        "size_label": "Size",
        "view_product": "View product",
        "yes": "Yes",
        "no": "No",
    },
    "es": {
        "welcome": "Hola {name}! Soy el Asistente Kabbary. Dime que buscas, tu talla y presupuesto y te recomendare los mejores productos! (ej. 'vestido talla S menos de 100')",
        "welcome_anon": "Hola! Soy el Asistente Kabbary. Dime que buscas, tu talla y presupuesto y te recomendare los mejores productos! (ej. 'vestido talla S menos de 100')",
        "results": "Aqui estan mis recomendaciones para ti:",
        "no_results": "Lo siento, no encontre productos con esos criterios. Intenta con otras palabras!",
        "register_hint": "Registrate o inicia sesion para obtener recomendaciones personalizadas!",
        "found_it": "Encontraste lo que buscabas?",
        "great": "Genial! Disfruta tu compra. Hasta pronto! 👋",
        "what_else": "Que mas deseas? Dime la prenda, talla y presupuesto.",
        "price_label": "Precio",
        "size_label": "Talla",
        "view_product": "Ver producto",
        "yes": "Si",
        "no": "No",
    },
    "ru": {
        "welcome": "Привет {name}! Я ассистент Kabbary. Скажите что ищете, ваш размер и бюджет и я найду лучшие товары! (напр. 'куртка размер M до 100')",
        "welcome_anon": "Привет! Я ассистент Kabbary. Скажите что ищете, ваш размер и бюджет и я найду лучшие товары! (напр. 'куртка размер M до 100')",
        "results": "Вот мои рекомендации для вас:",
        "no_results": "Извините, товары не найдены. Попробуйте другие слова!",
        "register_hint": "Зарегистрируйтесь для получения персональных рекомендаций!",
        "found_it": "Вы нашли то что искали?",
        "great": "Отлично! Приятных покупок. До свидания! 👋",
        "what_else": "Что ещё ищете? Скажите товар, размер и бюджет.",
        "price_label": "Цена",
        "size_label": "Размер",
        "view_product": "Смотреть товар",
        "yes": "Да",
        "no": "Нет",
    },
    "ar": {
        "welcome": "مرحبا {name}! انا مساعد Kabbary. اخبرني ما تبحث عنه، مقاسك وميزانيتك وسأجد افضل المنتجات لك! (مثال: 'جاكيت مقاس M اقل من 100')",
        "welcome_anon": "مرحبا! انا مساعد Kabbary. اخبرني ما تبحث عنه، مقاسك وميزانيتك وسأجد افضل المنتجات لك! (مثال: 'جاكيت مقاس M اقل من 100')",
        "results": "اليك توصياتي لك:",
        "no_results": "عذرا، لم اجد منتجات. جرب كلمات مختلفة!",
        "register_hint": "سجل للحصول على توصيات مخصصة!",
        "found_it": "هل وجدت ما تبحث عنه؟",
        "great": "رائع! استمتع بمشترياتك. الى اللقاء! 👋",
        "what_else": "ماذا تريد ايضا؟ اخبرني المنتج والمقاس والميزانية.",
        "price_label": "السعر",
        "size_label": "المقاس",
        "view_product": "عرض المنتج",
        "yes": "نعم",
        "no": "لا",
    },
}


def t(key, lang="en", **kwargs):
    lang = lang if lang in TRANSLATIONS else "en"
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text