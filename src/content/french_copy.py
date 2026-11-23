"""Заповнює порожні *_fr. Викликає лише міграція."""

from src.content.ui_fr import UI_FR
from src.content.ui_seed import CONTACTS, SITE_EXTRA, _empty, _fits, _pair


def _set_if_empty(obj, name, value):
    if not hasattr(obj, name) or not value:
        return False
    if not _empty(getattr(obj, name)):
        return False
    if not _fits(obj, name, value):
        return False
    setattr(obj, name, value)
    return True


def _save_changed(obj, names):
    unique = list(dict.fromkeys(names))
    if unique:
        obj.save(update_fields=unique)


def _append_francais(block):
    changed = []
    for name in ("lines_uk", "lines_en"):
        if not hasattr(block, name):
            continue
        value = getattr(block, name) or ""
        parts = [line for line in value.splitlines() if line.strip() != ""]
        if len(parts) != 7:
            continue
        if any(line.strip().lower() == "français" for line in parts):
            continue
        parts.append("Français")
        setattr(block, name, "\n".join(parts))
        changed.append(name)
    return changed


CATEGORY_NAMES = {
    "interierni-kompozytsii": "Compositions d’intérieur",
    "novorichnyi-dekor": "Décor de Nouvel An",
    "podarunkovi-sety": "Coffrets cadeaux",
    "rizdvyani-boksy": "Coffrets de Noël",
    "serviruvannia": "Arts de la table",
    "svichky": "Bougies",
    "tekstyl": "Textiles",
    "vazy-ta-kashpo": "Vases et cache-pots",
    "kolektsiini-dodatky": "Compléments de collections",
}

SET_NAMES = {"velykodni": "Pâques"}

PRODUCTS = {
    "GH-01": {"slug": "velykodnii-ukrainskyi", "name_fr": "Coffret de Pâques « Ukrainien »"},
    "GH-02": {"slug": "boks-rizdvyanyi-shyshky", "name_fr": "Coffret de Noël « Pommes de pin »"},
    "GH-04": {"slug": "vesilnyi", "name_fr": "Coffret de mariage"},
    "GH-05": {"slug": "vesnianyi", "name_fr": "Coffret de printemps"},
    "GH-06": {"slug": "gazetnyi", "name_fr": "Coffret journal"},
    "TL-0012": {
        "slug": "velykodnii-hnizdo",
        "name_fr": "Coffret de Pâques « Le Nid »",
        "description_fr": (
            "Le coffret de Pâques « Le Nid » est une composition festive pour une table de Pâques.\n"
            "Il comprend des œufs décoratifs, des bougeoirs en forme de fleurs et des détails pour la composition."
        ),
    },
    "COL-KVITKA": {"slug": "kvitka-dusha", "name_fr": "Coffret « Fleur-âme »"},
    "COL-KORINNIA": {"slug": "korinnia", "name_fr": "Coffret « Racines »"},
    "COL-KRYSHTAL": {"slug": "rodynnyi-kryshtal", "name_fr": "Coffret « Cristal familial »"},
    "COL-TARTAN": {"slug": "tartan", "name_fr": "Coffret « Tartan »"},
    "COL-DYTYNSTVO": {"slug": "dytynstvo", "name_fr": "Coffret « Enfance »"},
    "COL-SPADSHCHYNA": {"slug": "spadshchyna", "name_fr": "Coffret « Héritage »"},
    "ADD-HOLDERS": {"slug": "addon-pidsvichnyky", "name_fr": "Bougeoirs avec bougies"},
    "ADD-HOLDERS-2": {"slug": "addon-pidsvichnyky-2", "name_fr": "2 bougeoirs + 2 bougies"},
    "ADD-HOLDERS-EXTRA": {
        "slug": "addon-pidsvichnyky-extra",
        "name_fr": "Bougeoirs supplémentaires + 2 bougies",
    },
    "ADD-NAPKIN": {"slug": "addon-llyani-servetky", "name_fr": "Serviettes en lin"},
    "ADD-NAPKIN-PLAID": {"slug": "addon-servetky-klitynka", "name_fr": "Serviettes tartan"},
    "ADD-RINGS": {"slug": "addon-kiltsia", "name_fr": "Ronds de serviette"},
}

GROUP_NAMES = {"color": "Couleur", "style": "Style"}
ATTRIBUTE_NAMES = {
    ("color", "beige"): "Beige",
    ("color", "black"): "Noir",
    ("color", "gold"): "Or",
    ("color", "green"): "Vert",
    ("color", "red"): "Rouge",
    ("color", "white"): "Blanc",
    ("style", "boho"): "Boho",
    ("style", "classic"): "Classique",
    ("style", "modern"): "Moderne",
    ("style", "rustic"): "Rustique",
    ("style", "scandi"): "Scandinave",
}

BLOCKS = {
    "hero": {
        "title_fr": "Art of modern hospitality",
        "text_fr": "Coffrets de fête pour décorer votre table vous-même",
        "cta_fr": "Aller au catalogue",
    },
    "popular": {"title_fr": "Produits populaires", "cta_fr": "Aller au catalogue"},
    "collections": {
        "title_fr": "Collection de Noël des coffrets de fête",
        "link_fr": "Les traditions commencent à table",
        "cta_fr": "En savoir plus",
    },
    "categories": {"title_fr": "Catégories"},
    "advantages": {
        "title_fr": "Pourquoi l’on choisit GESTIA HOME",
        "text_fr": "Décor, floristique, textiles et linge de maison fabriqués en Ukraine",
        "text_mobile_fr": "Décor, floristique, textiles \net linge de maison fabriqués en Ukraine",
        "cta_fr": "Aller au catalogue",
    },
    "reviews": {"title_fr": "Avis"},
    "callback": {
        "title_fr": "Demander un rappel",
        "text_fr": "Laissez votre numéro, nous vous recontacterons sous peu",
        "text_mobile_fr": "Laissez votre numéro, \nnous vous recontacterons sous peu",
        "cta_fr": "Aller au catalogue",
        "link_fr": "la Politique de confidentialité",
        "note_fr": "J’accepte le traitement des données personnelles conformément à ",
        "lines_fr": "Prénom\nNuméro de téléphone\nMessage",
    },
    "mega": {"cta_fr": "Voir tout"},
    "catalog": {"cta_fr": "Tout charger"},
    "pdp_ship": {
        "title_fr": "Livraison",
        "text_fr": (
            "Livraison Nova Poshta en Ukraine — point relais, consigne ou coursier\n"
            "Délai indicatif — 1 à 3 jours ouvrés après expédition\n"
            "Les frais de livraison suivent les tarifs du transporteur\n"
            "Après l’expédition, vous recevez un numéro de suivi"
        ),
    },
    "pdp_pay": {
        "title_fr": "Paiement",
        "text_fr": (
            "Paiement en ligne par carte Visa ou Mastercard\n"
            "Paiement par virement bancaire\n"
            "La confirmation et les détails de paiement sont envoyés après la commande"
        ),
    },
    "pdp_set": {
        "title_fr": "Du même ensemble",
        "text_mobile_fr": "De cet ensemble",
        "cta_fr": "Aller au catalogue",
    },
    "pdp_related": {"title_fr": "Pièces similaires", "cta_fr": "Aller au catalogue"},
    "locale": {
        "title_fr": "Pays et langue",
        "text_fr": "Ukraine/Hryvnia ",
        "cta_fr": "Confirmer",
        "link_fr": "Modifier",
        "lines_fr": (
            "Lieu de livraison\nUkraine\nLivraison internationale\n"
            "Langue du site\nChoisissez la langue / Choose language\n"
            "Українська\nEnglish\nFrançais"
        ),
        "note_fr": "Veuillez choisir le lieu de livraison pour voir les prix et les modes de livraison corrects",
    },
}

NAV = {
    "nav_about_fr": "À propos",
    "nav_all_fr": "Tous les produits",
    "nav_faq_fr": "Questions fréquentes",
    "nav_contacts_fr": "Contacts",
    "menu_title_fr": "Catalogue",
    "credit_fr": "Créé par",
    "developer_note_fr": "Développé par PrometeyLabs",
    "footer_note_fr": "Tous droits réservés.",
}

MENU_GROUPS = {
    "Святкові бокси": "Coffrets de fête",
    "Столові аксесуари": "Accessoires de table",
}

MENU_ITEMS = {
    "«Квітка-душа»": "« Fleur-âme »",
    "«Коріння»": "« Racines »",
    "«Родинний кришталь»": "« Cristal familial »",
    "«Тартан»": "« Tartan »",
    "«Дитинство»": "« Enfance »",
    "«Спадщина»": "« Héritage »",
    "Підсвічники": "Bougeoirs",
    "Серветки": "Serviettes",
    "Кільця для серветок": "Ronds de serviette",
}

ADVANTAGES = (
    {
        "title_uk": "Унікальний дизайн",
        "title_fr": "Design unique",
        "text_uk": "Декор, що поєднує сучасну естетику та природну красу",
        "text_fr": "Un décor qui unit un regard contemporain à la beauté naturelle",
    },
    {
        "title_uk": "Українське виробництво",
        "title_fr": "Fabriqué en Ukraine",
        "text_uk": "Вироби, створені в Україні \nз увагою до деталей та естетики",
        "text_fr": "Des pièces faites en Ukraine \navec soin du détail et de l’esthétique",
    },
    {
        "title_uk": "Натуральні матеріали",
        "title_fr": "Matériaux naturels",
        "text_uk": "Натуральні матеріали для природної естетики та затишку вдома",
        "text_fr": "Des matériaux naturels pour un look vivant et le confort chez soi",
    },
    {
        "title_uk": "Багатофункціональність",
        "title_fr": "Polyvalence",
        "text_uk": "Речі, які легко адаптувати до різних потреб і домашніх сценаріїв",
        "text_fr": "Des pièces qui s’adaptent aux besoins et aux usages de la maison",
    },
)

REVIEW_AUTHOR_UK = "Марія\u00a0К."
REVIEW_AUTHOR_FR = "Maria\u00a0K."
REVIEW_TEXT_UK = (
    "Дуже красивий декор, який повністю відповідає фотографіям. "
    "Усе виглядає витончено й гармонійно. Саме такі деталі створюють особливу атмосферу вдома"
)
REVIEW_TEXT_FR = (
    "Un décor très beau, fidèle aux photographies. "
    "Tout paraît raffiné et harmonieux. Ce sont ces détails qui créent une atmosphère particulière chez soi."
)

FOOTER = (
    ("catalog", "", "Tous les produits"),
    ("category", "rizdvyani-boksy", "Coffrets de Noël"),
    ("category", "interierni-kompozytsii", "Compositions d’intérieur"),
    ("category", "serviruvannia", "Arts de la table"),
    ("about", "", "À propos"),
    ("anchor", "callback", "Contacts"),
    ("shipping", "", "Livraison et paiement"),
    ("offer", "", "Contrat public (offre)"),
    ("privacy", "", "Politique de confidentialité"),
    ("cookies", "", "Politique cookies"),
    ("faq", "", "Questions fréquentes"),
    ("contacts", "", "Contacts"),
)

FORMS = {
    "waitlist_title_fr": "Ta fête parfaite est presque dans la boîte…",
    "waitlist_p1_fr": (
        "Nous ajoutons les dernières touches aux coffrets Gestia Home, pour créer "
        "une atmosphère unique à la table du Nouvel An."
    ),
    "waitlist_p2_fr": "Encore un peu — et l’art de l’hospitalité fera partie de tes histoires !",
    "waitlist_p3_fr": "Ne manque pas le lancement — laisse ton email pour être prévenue la première.",
    "waitlist_email_fr": "Votre email",
    "waitlist_consent_fr": "J’accepte le traitement des données selon",
    "waitlist_privacy_fr": "la Politique de confidentialité",
    "waitlist_button_fr": "Me prévenir",
    "waitlist_thanks_title_fr": "Merci !",
    "waitlist_thanks_text_fr": "Nous vous préviendrons dès que les coffrets seront disponibles.",
    "sheet_consent_fr": "J’accepte le traitement des données personnelles",
    "sheet_close_fr": "Fermer",
    "contact_button_fr": "Envoyer",
    "callback_button_fr": "Envoyer la demande",
    "buy_button_fr": "Commander maintenant",
    "label_name_fr": "Prénom",
    "label_phone_fr": "Téléphone",
    "label_message_fr": "Message",
    "label_address_fr": "Adresse de livraison",
    "label_email_fr": "Email",
}


def fill_french_copy(apps, schema_editor):
    del schema_editor
    from src.content.french_copy_pages import fill_pages
    from src.content.legal_copy import sections_to_html
    from src.content.legal_copy_fr import DOCS_FR

    InterfaceCopy = apps.get_model("content", "InterfaceCopy")
    copy, _ = InterfaceCopy.objects.get_or_create(pk=1)
    changed = [f"{key}_fr" for key, value in UI_FR.items() if _set_if_empty(copy, f"{key}_fr", value)]
    _save_changed(copy, changed)

    SiteSettings = apps.get_model("content", "SiteSettings")
    site, _ = SiteSettings.objects.get_or_create(pk=1)
    site_changed = [name for name, value in NAV.items() if _set_if_empty(site, name, value)]
    for stem, pair in SITE_EXTRA.items():
        fr = pair[2] if len(pair) > 2 else ""
        if _pair(site, stem, "", "", fr):
            site_changed.append(f"{stem}_fr")
    _save_changed(site, site_changed)

    ContactsPage = apps.get_model("content", "ContactsPage")
    page, _ = ContactsPage.objects.get_or_create(pk=1)
    contact_changed = [
        name for name, value in CONTACTS.items() if name.endswith("_fr") and _set_if_empty(page, name, value)
    ]
    _save_changed(page, contact_changed)

    ContactForms = apps.get_model("content", "ContactForms")
    forms, _ = ContactForms.objects.get_or_create(pk=1)
    form_changed = [name for name, value in FORMS.items() if _set_if_empty(forms, name, value)]
    _save_changed(forms, form_changed)

    HomeBlock = apps.get_model("content", "HomeBlock")
    for key, fields in BLOCKS.items():
        block = HomeBlock.objects.filter(key=key).first()
        if block is None:
            continue
        names = [name for name, value in fields.items() if _set_if_empty(block, name, value)]
        names.extend(_append_francais(block))
        _save_changed(block, names)

    Advantage = apps.get_model("content", "Advantage")
    for row in ADVANTAGES:
        found = Advantage.objects.filter(title_uk=row["title_uk"])
        found.filter(title_fr="").update(title_fr=row["title_fr"])
        found.filter(text_uk=row["text_uk"], text_fr="").update(text_fr=row["text_fr"])

    Review = apps.get_model("content", "Review")
    Review.objects.filter(author_uk=REVIEW_AUTHOR_UK, author_fr="").update(author_fr=REVIEW_AUTHOR_FR)
    Review.objects.filter(text_uk=REVIEW_TEXT_UK, text_fr="").update(text_fr=REVIEW_TEXT_FR)

    Category = apps.get_model("catalog", "Category")
    for slug, value in CATEGORY_NAMES.items():
        Category.objects.filter(slug=slug, name_fr="").update(name_fr=value)

    ProductSet = apps.get_model("catalog", "ProductSet")
    for slug, value in SET_NAMES.items():
        ProductSet.objects.filter(slug=slug, name_fr="").update(name_fr=value)

    Product = apps.get_model("catalog", "Product")
    for sku, data in PRODUCTS.items():
        qs = Product.objects.filter(sku=sku, slug=data["slug"])
        for field, value in data.items():
            if field == "slug":
                continue
            qs.filter(**{field: ""}).update(**{field: value})

    Group = apps.get_model("catalog", "ProductAttributeGroup")
    for slug, value in GROUP_NAMES.items():
        Group.objects.filter(slug=slug, name_fr="").update(name_fr=value)
    Attr = apps.get_model("catalog", "ProductAttribute")
    for (group, slug), value in ATTRIBUTE_NAMES.items():
        Attr.objects.filter(group__slug=group, slug=slug, name_fr="").update(name_fr=value)

    fill_pages(apps)

    LegalPage = apps.get_model("content", "LegalPage")
    for key, factory in DOCS_FR.items():
        doc = factory()
        legal = LegalPage.objects.filter(key=key).first()
        if legal is None:
            continue
        fields = {
            "title_fr": doc["title"],
            "body_fr": sections_to_html(doc["sections"]),
            "seo_title_fr": doc["seo_title"],
            "seo_description_fr": doc["seo_description"],
        }
        names = [name for name, value in fields.items() if _set_if_empty(legal, name, value)]
        _save_changed(legal, names)

    FooterLink = apps.get_model("content", "FooterLink")
    for url_name, url_arg, label_fr in FOOTER:
        FooterLink.objects.filter(url_name=url_name, url_arg=url_arg, label_fr="").update(label_fr=label_fr)

    MenuGroup = apps.get_model("content", "MenuGroup")
    for title_uk, title_fr in MENU_GROUPS.items():
        MenuGroup.objects.filter(title_uk=title_uk, title_fr="").update(title_fr=title_fr)
    MenuGroupItem = apps.get_model("content", "MenuGroupItem")
    for label_uk, label_fr in MENU_ITEMS.items():
        MenuGroupItem.objects.filter(label_uk=label_uk, label_fr="").update(label_fr=label_fr)


def unfill_french_copy(apps, schema_editor):
    del apps, schema_editor
