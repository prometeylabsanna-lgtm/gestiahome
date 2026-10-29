"""Поточні тексти вітрини (uk + en). Порожнє поле в адмінці повертає цей рядок."""

LITERALS = {
    "hero_title": (
        "Декор для дому, текстиль \nі флористика",
        "Home decor, textiles \nand floristry",
    ),
    "hero_text": (
        "Декор для дому, домашній текстиль, флористика та одяг для дому від Gestia Home. "
        "Створюйте затишний простір із речами, у яких поєднуються естетика та функціональність",
        "Home decor, home textiles, floristry, and clothing for the home from Gestia Home. "
        "Create a cosy space with pieces that bring aesthetics and function together.",
    ),
    "hero_cta": ("Перейти до каталогу", "Go to the catalogue"),
    "categories_label": ("Категорії", "Categories"),
    "popular_title": ("Популярні товари", "Popular products"),
    "popular_cta": ("Перейти до каталогу", "Go to the catalogue"),
    "advantages_title": ("Чому обирають GESTIA HOME", "Why people choose GESTIA HOME"),
    "advantages_text": (
        "Декор для дому, флористика, текстиль та одяг для дому українського виробництва",
        "Home decor, floristry, textiles, and clothing for the home, made in Ukraine",
    ),
    "advantages_text_mobile": (
        "Декор для дому, флористика, текстиль \nта одяг для дому українського виробництва",
        "Home decor, floristry, textiles \nand clothing for the home, made in Ukraine",
    ),
    "advantages_cta": ("Перейти до каталогу", "Go to the catalogue"),
    "reviews_title": ("Відгуки", "Reviews"),
    "callback_title": ("Замовити зворотний дзвінок", "Request a callback"),
    "callback_text": (
        "Залиште свій номер телефону, і ми зв’яжемося з вами найближчим часом",
        "Leave your phone number and we will contact you shortly",
    ),
    "callback_text_mobile": (
        "Залиште свій номер телефону, \nі ми зв’яжемося з вами найближчим часом",
        "Leave your phone number, \nand we will contact you shortly",
    ),
    "callback_cta": ("Перейти до каталогу", "Go to the catalogue"),
    "callback_name": ("Ім’я", "Name"),
    "callback_phone": ("Номер телефону", "Phone number"),
    "callback_message": ("Повідомлення", "Message"),
    "callback_note": (
        "Погоджуюсь на обробку персональних даних згідно з ",
        "I agree to the processing of personal data according to ",
    ),
    "callback_privacy": ("Політикою конфіденційності", "the Privacy policy"),
    "waitlist_title": (
        "Твоє ідеальне свято вже майже у коробці…",
        "Your perfect celebration is almost in the box…",
    ),
    "waitlist_p1": (
        "Ми додаємо останні штрихи до святкових боксів Gestia Home, щоб ти могла "
        "легко створити особливу атмосферу за новорічним столом.",
        "We're adding the final touches to the Gestia Home festive boxes, so you can "
        "easily create a special atmosphere for the New Year's table.",
    ),
    "waitlist_p2": (
        "Ще трішки — і мистецтво гостинності стане частиною твоїх сімейних історій!",
        "Just a little longer — and the art of hospitality will become part of your family stories!",
    ),
    "waitlist_p3": (
        "Не пропусти старт продажів — залиш свій email та дізнайся першою, коли "
        "святкові бокси стануть доступними!",
        "Don't miss the launch — leave your email and be the first to know when the "
        "festive boxes are available!",
    ),
    "waitlist_email": ("Ваш email", "Your email"),
    "waitlist_consent": (
        "Погоджуюсь на обробку персональних даних згідно з",
        "I agree to the processing of personal data according to",
    ),
    "waitlist_privacy": ("Політикою конфіденційності", "the Privacy policy"),
    "waitlist_button": ("Повідомити мене", "Notify me"),
    "waitlist_thanks_title": ("Дякуємо!", "Thank you!"),
    "waitlist_thanks_text": (
        "Ми повідомимо вас першими, коли святкові бокси стануть доступними.",
        "We will let you know first when the festive boxes are available.",
    ),
    "sheet_consent": (
        "Погоджуюсь на обробку персональних даних",
        "I agree to the processing of personal data",
    ),
    "sheet_close": ("Закрити", "Close"),
    "contact_button": ("Надіслати", "Send"),
    "callback_button": ("Надіслати заявку", "Send request"),
    "buy_button": ("Замовити одразу", "Order now"),
    "label_name": ("Ім'я", "Name"),
    "label_phone": ("Телефон", "Phone"),
    "label_message": ("Повідомлення", "Message"),
    "label_address": ("Адреса доставки", "Delivery address"),
    "label_email": ("Email", "Email"),
    "lead": ("Сучасна жінка може все.", "A modern woman can do anything."),
    "credit": ("Зроблено", "Made by"),
    "nav_about": ("Про нас", "About"),
    "nav_all": ("Усі товари", "All products"),
    "menu_title": ("Каталог", "Catalogue"),
    "crumb": ("Головна", "Home"),
    "story_label": ("Про Gestia Home", "About Gestia Home"),
}


def seed_form_kwargs():
    names = (
        "waitlist_title",
        "waitlist_p1",
        "waitlist_p2",
        "waitlist_p3",
        "waitlist_email",
        "waitlist_consent",
        "waitlist_privacy",
        "waitlist_button",
        "waitlist_thanks_title",
        "waitlist_thanks_text",
        "sheet_consent",
        "sheet_close",
        "contact_button",
        "callback_button",
        "buy_button",
        "label_name",
        "label_phone",
        "label_message",
        "label_address",
        "label_email",
    )
    data = {}
    for name in names:
        uk, en = LITERALS[name]
        data[f"{name}_uk"] = uk
        data[f"{name}_en"] = en
    return data
