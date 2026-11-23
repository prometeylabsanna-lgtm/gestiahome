"""Longs textes FR pour pages CMS. Appelé seulement depuis french_copy."""

from src.content.french_copy import _empty, _set_if_empty, _save_changed

ABOUT_FR = {
    "title_fr": "Hi, I\u2019m Gestia",
    "lead_fr": "Une femme moderne peut tout.",
    "crumb_fr": "Accueil",
    "story_label_fr": "À propos de Gestia Home",
    "intro_text_fr": (
        "<p>Parmi les innombrables chemins que le monde moderne offre à une femme, il y a "
        "un rôle très particulier — être <em>celle qui crée un foyer</em>.</p>"
        "<p>Un <em>foyer</em> qui n’est pas un lieu de corvées sans fin, mais un espace "
        "de créativité, d’inspiration, d’amour et d’expression de soi.</p>"
        "<p>Il ne s’agit pas d’un statut, d’une grande maison ou d’un intérieur raffiné. "
        "Il s’agit d’un <em>état intérieur</em> qui fait partie de la vie personnelle, "
        "comme la mode, le style, le voyage ou l’art.<br>C’est le désir de rentrer un peu "
        "plus tôt, de mettre de la musique, d’allumer les bougies, de dresser une belle "
        "table et d’accueillir ses amis avec un sourire.</p>"
    ),
    "intro_photo_left_alt_fr": "Une femme compose un arrangement de légumes sur une table blanche",
    "intro_photo_main_alt_fr": "Une femme dresse la table avec des serviettes en lin et des ronds de serviette",
    "gestia_quote_fr": (
        "HESTIA EST LA DÉESSE GRECQUE DU FOYER, DE L’HARMONIE ET DU FEU SACRÉ "
        "QUI RÉUNIT LES GENS, LES AMIS ET LES GÉNÉRATIONS."
    ),
    "gestia_plate_alt_fr": "Des mains tiennent une assiette verte au-dessus d’une table de fête",
    "gestia_photo_alt_fr": "Une table ronde avec des fleurs vertes, des bougies et du cristal",
    "gestia_text_fr": (
        "<p>Et comme il est beau que la <em>Gestia</em> d’aujourd’hui n’ait pas à tout "
        "faire seule. Son vrai rôle n’est pas de cocher une liste sans fin, mais "
        "<em>d’inspirer, de rassembler et de créer une atmosphère chaleureuse</em>.</p>"
    ),
    "approach_text_fr": (
        "GESTIA HOME prend en charge toute la préparation supplémentaire. Il ne vous reste "
        "qu’à enfiler votre robe préférée, disposer le décor et ouvrir la porte."
    ),
    "together_photo_alt_fr": "Un arrangement floral près de la fenêtre",
    "together_text_fr": (
        "<p>Nous rêvons de ramener les dîners à la maison, les retrouvailles spontanées, "
        "les grandes fêtes de famille et les petits prétextes du quotidien pour être ensemble.</p>"
        "<p>Car une table bien dressée n’est pas une démonstration de richesse. C’est un "
        "geste d’attention.<br>C’est à table que naissent l’amitié, la confiance, les "
        "souvenirs partagés et les traditions familiales.<br>C’est une façon de dire "
        "sans mots : «Je suis si heureuse que tu sois là ce soir.»</p>"
    ),
    "closing_text_fr": (
        "<p>Nous croyons qu’une femme moderne peut réussir dans tout ce qu’elle choisit. "
        "Et, convenez-en, être l’hôtesse inspirée de son propre foyer est l’un des plus "
        "beaux choix qui soient.</p>"
    ),
    "cta_fr": "Parcourir le catalogue",
    "seo_title_fr": "À propos — Gestia Home",
    "seo_description_fr": (
        "Gestia Home, c’est la femme qui crée un foyer. Coffrets de fête et décor pour "
        "inspirer, rassembler et créer une atmosphère chaleureuse."
    ),
}

FAQ_PAGE_FR = {
    "title_fr": "Bon à<br>savoir",
    "crumb_fr": "FAQ",
    "image_alt_fr": "Une table de fête avec des compositions, des bougies et des serviettes",
    "contact_title_fr": "Encore des questions ?",
    "contact_text_fr": "<p>Écrivez-nous — nous vous aiderons à choisir le coffret.</p>",
    "seo_title_fr": "FAQ — Gestia Home",
    "seo_description_fr": (
        "Réponses aux questions fréquentes sur les coffrets de fête Gestia Home : "
        "contenu du coffret, vaisselle, moment pour décorer et durée de la sapinette."
    ),
}

FAQ_ITEMS_FR = [
    {
        "question_uk": "Що входить у святковий бокс?",
        "question_fr": "Que contient un coffret de fête ?",
        "answer_fr": (
            "<p>Nous affinons le contenu de chaque coffret pour que chaque détail de fête "
            "soit prévu. Nos premières collections de Noël comprennent :</p>"
            "<ul>"
            "<li>un beau vase à garder bien après les fêtes</li>"
            "<li>des branches de sapin frais, prêtes à composer</li>"
            "<li>tous les matériaux techniques nécessaires</li>"
            "<li>des ornements ou du décor</li>"
            "<li>des bougies de table design, 35 ou 45 cm</li>"
            "</ul>"
        ),
        "sort": 0,
    },
    {
        "question_uk": "Який посуд та столові прибори підійдуть під бокс?",
        "question_fr": "Quelle vaisselle et quels couverts vont avec un coffret ?",
        "answer_fr": (
            "<p>Nos coffrets de fête sont polyvalents et apportent une ambiance festive "
            "à toute vaisselle et tout linge de table. Pour un accord parfait, essayez "
            "les pièces de la rubrique «Accessoires de table» — elles sont choisies "
            "pour chaque ensemble.</p>"
        ),
        "sort": 1,
    },
    {
        "question_uk": "Коли розпочинати декорувати стіл до Різдвяних свят?",
        "question_fr": "Quand commencer à décorer la table pour Noël ?",
        "answer_fr": (
            "<p>Commencez dès que l’inspiration vient. Seule, avec des amis, ou avec "
            "les enfants en décorant le sapin.</p>"
            "<p>Pour le faire sans stress, nous conseillons de décorer 7 à 10 jours "
            "avant la fête. Ainsi vous savourez le geste et le résultat plus longtemps.</p>"
        ),
        "sort": 2,
    },
    {
        "question_uk": "Скільки може простояти гілля хвої?",
        "question_fr": "Combien de temps durent les branches de sapin ?",
        "answer_fr": (
            "<p>Nos décors de fête sont conçus pour durer. Nous avons choisi une variété "
            "de sapin qui conserve son allure jusqu’à 3 mois à l’intérieur, jusqu’à 25 °C.</p>"
        ),
        "sort": 3,
    },
]

THANKYOU_FR = {
    "order_title_fr": "Heureux de faire partie de vos traditions !",
    "order_text_fr": (
        "<p>La commande n° {number} est enregistrée. Après l’expédition, vous recevrez "
        "un numéro de suivi.</p>"
    ),
    "order_text_nonum_fr": (
        "<p>La commande est enregistrée. Après l’expédition, vous recevrez un numéro "
        "de suivi.</p>"
    ),
    "link_fr": "Retour à l’accueil",
    "contact_title_fr": "Merci",
    "contact_text_fr": "<p>Nous avons reçu votre message et vous répondrons bientôt.</p>",
}

COLLECTIONS = {
    "kvitka-dusha": {
        "label_fr": "Collection",
        "title_fr": "Fleur-âme",
        "text_fr": (
            "<p>«Fleur-âme», ce sont des amaryllis vivantes que la famille cultive "
            "jusqu’à Noël. Elle unit la beauté de l’hippeastrum vivant à l’art de la "
            "table de fête. Pétales rouge profond, coupes d’argent, pin naturel et "
            "flamme des bougies composent un arrangement raffiné que vous cultivez et "
            "dressez vous-même.</p>"
            "<p>La valeur de cet ensemble est l’attente partagée de l’éclosion. Chaque "
            "fleur devient un petit récit de famille que l’on a envie de recommencer "
            "chaque année.</p>"
        ),
        "box_items_fr": "\n".join(
            [
                "Coupes — 2",
                "3 bulbes d’amaryllis vivants",
                "Pin frais",
                "Tous les matériaux nécessaires",
                "Un atelier pour décorer la table vite et sans stress",
            ]
        ),
        "alt_large_fr": "Composition d’hiver de pin et de branches sur un socle de béton",
        "alt_small_fr": "Composition d’amaryllis rouges, de pin et de rubans",
    },
    "korinnia": {
        "label_fr": "Collection",
        "title_fr": "Racines",
        "text_fr": (
            "<p>Plusieurs sortes de pin frais, des textures naturelles et des tons "
            "retenus, pour une table sans rien de trop. Seulement une harmonie naturelle, "
            "le parfum d’une forêt d’hiver, et des détails que l’on a envie de regarder "
            "de près.</p>"
        ),
        "box_items_fr": "\n".join(
            [
                "Un vase",
                "3 sortes de pin frais",
                "Tous les matériaux nécessaires",
                "Cloches anciennes",
                "Un atelier pour décorer la table vite et sans stress",
            ]
        ),
        "alt_large_fr": "Table dressée avec une serviette de lin, des bougies et des fleurs",
        "alt_small_fr": "Mains nouant une serviette avec un rond sur une assiette",
    },
    "rodynnyi-kryshtal": {
        "label_fr": "Collection",
        "title_fr": "Cristal\nfamilial",
        "text_fr": (
            "<p>Vous souvenez-vous du service en cristal dans le buffet de votre "
            "grand-mère ? Il semblait si précieux qu’il ne venait à table que les jours "
            "de fête. Ou il prenait la poussière des décennies, comme un bijou. "
            "Il est temps de le sortir… Ou de le réinterpréter…</p>"
        ),
        "box_items_fr": "\n".join(
            [
                "Un vase-coupe à fruits",
                "Branches de pin frais préparées",
                "Tous les matériaux pour composer l’arrangement",
                "Bougies — 2",
                "Ornements",
                "Un lien vers un atelier pour assembler vite et avec plaisir",
            ]
        ),
        "alt_large_fr": "Table de fête au jardin avec des compositions de paille",
        "alt_small_fr": "Couronnes de paille, fleurs et verres sur une table de fête",
    },
    "tartan": {
        "label_fr": "Collection",
        "title_fr": "Tartan",
        "text_fr": (
            "<p>La collection s’inspire d’un Noël européen, où le raffinement tient "
            "non seulement aux objets, mais au goût, au savoir et à l’éducation.</p>"
            "<p>Un bordeaux profond et un tartan classique dressent une table de fête "
            "de luxe retenu et de chaleur du foyer.</p>"
        ),
        "box_items_fr": "\n".join(
            [
                "Branches de pin frais préparées",
                "Un plateau et tous les matériaux",
                "4 bougies",
                "Ornements",
            ]
        ),
        "alt_large_fr": "Salle de banquet avec des chandeliers et des callas",
        "alt_small_fr": "Table dressée avec des callas, des bougies et des verres en cristal",
    },
    "dytynstvo": {
        "label_fr": "Collection",
        "title_fr": "Enfance",
        "text_fr": (
            "<p>Retrouvez le parfum de la première mandarine pelée, et la boîte à "
            "chaussures des boules de Noël et du fil d’argent. Chevaux de métal, "
            "flocons faits main, sucreries et mandarines…</p>"
            "<p>Nous avons porté cette nostalgie dans un dressage contemporain, pour "
            "que la table de Noël soit non seulement belle, mais pleine de symboles "
            "familiers, d’histoires chaudes et de souvenirs de famille. Retrouvez "
            "votre ornement préféré dans la vieille boîte d’enfance, ajoutez-le à "
            "la composition, et racontez-le à vos enfants.</p>"
        ),
        "box_items_fr": "\n".join(
            [
                "Un vase-casserole",
                "Branches de pin frais",
                "Tous les matériaux nécessaires",
                "2 bougies",
                "Ornements",
                "Un atelier pour décorer la table vite et sans stress",
            ]
        ),
        "alt_large_fr": "Bougies de cire parmi les baies et les pommes de pin",
        "alt_small_fr": "Bougies, pommes de pin et baies rouges sur une table de fête",
    },
    "spadshchyna": {
        "label_fr": "Collection de Noël",
        "title_fr": "Héritage",
        "text_fr": (
            "<p>Longtemps, Noël dans les familles ukrainiennes commençait par des "
            "préparatifs particuliers. La maison se remplissait non seulement du parfum "
            "du pin et des plats de fête, mais de celui du blé mûr. La place d’honneur "
            "sur la table revenait au didukh — symbole de la mémoire des ancêtres, de "
            "la prospérité et de l’unité du lignage.</p>"
            "<p>La collection Héritage réinterprète ces traditions dans l’art "
            "contemporain de la table.</p>"
        ),
        "box_items_fr": "\n".join(
            [
                "Un vase-coupe en céramique de Pokuttia",
                "Branches de pin préparées",
                "Tresses et gerbes décoratives",
                "Tous les matériaux pour composer l’arrangement",
                "Bougies assorties — 2",
                "Un lien vers un atelier pour décorer la table vite et sans stress",
            ]
        ),
        "alt_large_fr": "Longue table de fête devant des rideaux rouges",
        "alt_small_fr": "Table dressée avec des anthuriums rouges",
    },
}


def fill_pages(apps):
    AboutPage = apps.get_model("content", "AboutPage")
    FaqPage = apps.get_model("content", "FaqPage")
    FaqItem = apps.get_model("content", "FaqItem")
    ThankYouPage = apps.get_model("content", "ThankYouPage")
    HomeCollection = apps.get_model("content", "HomeCollection")

    about, _ = AboutPage.objects.get_or_create(pk=1)
    _save_changed(about, [name for name, value in ABOUT_FR.items() if _set_if_empty(about, name, value)])

    faq, _ = FaqPage.objects.get_or_create(pk=1)
    _save_changed(faq, [name for name, value in FAQ_PAGE_FR.items() if _set_if_empty(faq, name, value)])

    for row in FAQ_ITEMS_FR:
        item = (
            FaqItem.objects.filter(page=faq, question_uk=row["question_uk"], sort=row["sort"])
            .order_by("id")
            .first()
        )
        if item is None:
            item = (
                FaqItem.objects.filter(page=faq, question_uk=row["question_uk"])
                .order_by("sort", "id")
                .first()
            )
        if item is None:
            continue
        names = [
            name
            for name, value in (("question_fr", row["question_fr"]), ("answer_fr", row["answer_fr"]))
            if _set_if_empty(item, name, value)
        ]
        _save_changed(item, names)

    thanks, _ = ThankYouPage.objects.get_or_create(pk=1)
    _save_changed(thanks, [name for name, value in THANKYOU_FR.items() if _set_if_empty(thanks, name, value)])

    for slug, payload in COLLECTIONS.items():
        row = HomeCollection.objects.filter(slug=slug).first()
        if row is None:
            continue
        story = payload["text_fr"]
        names = []
        for field, value in payload.items():
            if _set_if_empty(row, field, value):
                names.append(field)
        if _empty(getattr(row, "story_fr", "")) and _set_if_empty(row, "story_fr", story):
            names.append("story_fr")
        _save_changed(row, names)
