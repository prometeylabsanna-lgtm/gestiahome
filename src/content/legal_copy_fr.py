"""Французькі тексти юридичних сторінок. Структура розділів збігається з legal_copy."""

from __future__ import annotations


def offer_doc() -> dict:
    return {
        "slug": "offer",
        "title": "Contrat public (offre)",
        "seo_title": "Contrat public (offre) · Gestia Home",
        "seo_description": (
            "Offre publique de la boutique Gestia Home : commande, paiement, livraison et retours."
        ),
        "sections": [
            {
                "heading": "1. Dispositions générales",
                "paragraphs": [
                    "1.1. Le présent document constitue une proposition publique (offre) du vendeur Gestia Home (le «Vendeur») de conclure un contrat de vente au détail à distance, aux conditions énoncées ci-dessous.",
                    "1.2. L’offre est acceptée lorsque l’Acheteur passe commande sur le site, confirme la commande et/ou paie les marchandises. Dès l’acceptation, le contrat est réputé conclu.",
                    "1.3. En passant commande, l’Acheteur confirme qu’il a pris connaissance des conditions de l’offre, de la politique de confidentialité et de la politique cookies, et qu’il les accepte.",
                ],
            },
            {
                "heading": "2. Objet du contrat",
                "paragraphs": [
                    "2.1. Le Vendeur s’engage à transférer la propriété des marchandises à l’Acheteur, et l’Acheteur s’engage à les recevoir et à les payer aux conditions du présent contrat.",
                    "2.2. Le nom, les caractéristiques, la disponibilité et le prix des marchandises sont ceux indiqués sur la page du catalogue au moment de la commande.",
                    "2.3. Les images des marchandises sont illustratives. Des écarts mineurs de teinte, de texture et de composition sont admis, compte tenu des matériaux et du travail artisanal.",
                ],
            },
            {
                "heading": "3. Prix et paiement",
                "paragraphs": [
                    "3.1. Les prix sont indiqués en hryvnias (UAH) ou en euros (EUR), selon la devise d’affichage choisie sur le site. Le montant final est fixé au moment de la confirmation de la commande.",
                    "3.2. Les modes de paiement disponibles sont le paiement par carte en ligne sur le site et/ou le paiement à la livraison, selon les options proposées au checkout.",
                    "3.3. Les frais de livraison ne sont pas inclus dans le prix des marchandises, sauf mention contraire expresse, et sont payés selon les tarifs du transporteur.",
                ],
            },
            {
                "heading": "4. Passation et exécution de la commande",
                "paragraphs": [
                    "4.1. Pour passer commande, l’Acheteur indique un nom, un numéro de téléphone, une adresse email (si nécessaire) et les informations de livraison.",
                    "4.2. Après réception d’une commande, le Vendeur peut contacter l’Acheteur pour préciser les détails. La commande est réputée acceptée une fois confirmée par le Vendeur.",
                    "4.3. Le délai de préparation dépend de la disponibilité des marchandises et de la charge de l’atelier, et est communiqué à l’Acheteur lors de la confirmation.",
                    "4.4. Le Vendeur peut refuser de traiter une commande si les marchandises sont indisponibles, en cas d’erreur de prix ou de description, ou en cas de suspicion de fraude, et en informe l’Acheteur.",
                ],
            },
            {
                "heading": "5. Livraison",
                "paragraphs": [
                    "5.1. La livraison est effectuée par des services de livraison (notamment Nova Poshta) vers un point relais, une consigne ou par coursier, au choix de l’Acheteur.",
                    "5.2. Le délai indicatif après expédition est de 1 à 3 jours ouvrés, sauf accord contraire des parties.",
                    "5.3. Le risque de détérioration ou de perte accidentelle des marchandises passe à l’Acheteur lors de la remise au transporteur, sauf disposition légale contraire.",
                    "5.4. L’Acheteur doit vérifier l’intégrité de l’emballage à la réception. En cas de dommage, un constat doit être dressé avec un représentant du transporteur.",
                ],
            },
            {
                "heading": "6. Retours et échanges",
                "paragraphs": [
                    "6.1. Les retours et échanges de marchandises de qualité conforme sont effectués conformément à la loi ukrainienne «Sur la protection des droits des consommateurs».",
                    "6.2. Les marchandises fabriquées sur commande individuelle, ou portant des traces d’usage ou de dommages imputables à l’Acheteur, peuvent ne pas être reprises, dans les limites prévues par la loi.",
                    "6.3. Pour un retour, l’Acheteur contacte le Vendeur via les coordonnées du site. Le remboursement est effectué par le même mode de paiement, ou par un autre mode convenu, après réception et contrôle des marchandises.",
                ],
            },
            {
                "heading": "7. Responsabilité des parties",
                "paragraphs": [
                    "7.1. Les parties sont responsables conformément à la législation de l’Ukraine.",
                    "7.2. Le Vendeur n’est pas responsable des retards dus au transporteur, à un cas de force majeure, ou à des coordonnées ou une adresse incorrectes fournies par l’Acheteur.",
                    "7.3. L’Acheteur est responsable de l’exactitude des informations fournies lors de la commande.",
                ],
            },
            {
                "heading": "8. Autres conditions",
                "paragraphs": [
                    "8.1. Le Vendeur peut modifier les conditions de l’offre. La nouvelle version s’applique dès sa publication sur le site, pour les commandes passées après cette publication.",
                    "8.2. Tous les litiges sont réglés par négociation et, à défaut, selon les modalités prévues par la législation de l’Ukraine.",
                    "8.3. Pour toute question relative aux commandes, utilisez les coordonnées indiquées dans la rubrique «Contacts» du site Gestia Home.",
                ],
            },
        ],
    }


def privacy_doc() -> dict:
    return {
        "slug": "privacy",
        "title": "Politique de confidentialité",
        "seo_title": "Politique de confidentialité · Gestia Home",
        "seo_description": (
            "Comment Gestia Home collecte, utilise et protège les données personnelles des clients et visiteurs du site."
        ),
        "sections": [
            {
                "heading": "1. Qui nous sommes et ce que régit cette politique",
                "paragraphs": [
                    "1.1. La présente politique de confidentialité explique comment Gestia Home («nous», le «Vendeur») traite les données personnelles des utilisateurs du site et des clients.",
                    "1.2. Le traitement est effectué conformément à la loi ukrainienne «Sur la protection des données personnelles» et aux autres règles applicables.",
                    "1.3. En utilisant le site, en passant commande ou en envoyant une demande, vous confirmez avoir pris connaissance de cette politique.",
                ],
            },
            {
                "heading": "2. Quelles données nous collectons",
                "paragraphs": [
                    "2.1. Données que vous fournissez : nom, numéro de téléphone, email, adresse de livraison, texte d’un message, marchandises choisies et paramètres de la commande.",
                    "2.2. Données techniques : adresse IP, type de navigateur, cookies et horodatage des visites, dans la mesure nécessaire au fonctionnement du site et à l’analyse.",
                    "2.3. Nous ne demandons pas de données inutiles. Les champs des formulaires se limitent aux informations nécessaires pour vous contacter et exécuter la commande.",
                ],
            },
            {
                "heading": "3. Finalité du traitement",
                "paragraphs": [
                    "3.1. Passation, confirmation et exécution des commandes ; livraison ; communication sur le statut d’une commande.",
                    "3.2. Réponse aux demandes envoyées via les formulaires de contact et «Commander maintenant».",
                    "3.3. Amélioration du site, prévention de la fraude et respect des obligations légales (comptabilité et fiscalité).",
                    "3.4. Nous ne transmettons pas vos données à des tiers à des fins de publicité qui leur est propre.",
                ],
            },
            {
                "heading": "4. Bases juridiques",
                "paragraphs": [
                    "4.1. Votre consentement (notamment la case d’accord au traitement des données personnelles dans les formulaires).",
                    "4.2. Conclusion et exécution du contrat de vente (l’offre).",
                    "4.3. Les intérêts légitimes du Vendeur — sécurité du service et prévention des abus — dans la mesure où ils ne portent pas atteinte à vos droits.",
                ],
            },
            {
                "heading": "5. Destinataires possibles des données",
                "paragraphs": [
                    "5.1. Aux services de livraison, pour la remise de la commande.",
                    "5.2. Aux prestataires de paiement, si le paiement en ligne est choisi.",
                    "5.3. Aux prestataires d’hébergement et d’infrastructure qui font fonctionner le site, sous réserve de confidentialité.",
                    "5.4. Aux autorités publiques, uniquement dans les cas et dans la mesure prévus par la loi.",
                ],
            },
            {
                "heading": "6. Conservation et protection",
                "paragraphs": [
                    "6.1. Les données sont conservées pendant la durée nécessaire à l’exécution de la commande, aux obligations de garantie et de comptabilité, et au règlement des litiges, et pas au-delà de ce qu’exigent la loi ou la finalité du traitement.",
                    "6.2. Nous appliquons des mesures organisationnelles et techniques pour protéger les données contre l’accès, la modification ou la destruction non autorisés.",
                    "6.3. Les données sont transmises via des connexions sécurisées (HTTPS), lorsque cela est techniquement prévu.",
                ],
            },
            {
                "heading": "7. Vos droits",
                "paragraphs": [
                    "7.1. Vous avez le droit de savoir quelles de vos données sont traitées, et d’exiger leur correction, leur blocage ou leur suppression, dans les limites de la loi.",
                    "7.2. Vous pouvez retirer votre consentement en écrivant à l’adresse ou au téléphone de l’atelier. Le retrait n’affecte pas la licéité du traitement effectué avant le retrait.",
                    "7.3. Le retrait du consentement peut rendre impossible l’exécution d’une commande non achevée, ou la réponse à une demande.",
                ],
            },
            {
                "heading": "8. Cookies et services tiers",
                "paragraphs": [
                    "8.1. Le site utilise des cookies et des technologies similaires. Les détails figurent dans la Politique cookies.",
                    "8.2. Certains services (par exemple l’analyse ou les widgets de paiement) peuvent traiter des données techniques selon leurs propres politiques.",
                ],
            },
            {
                "heading": "9. Modifications de la politique",
                "paragraphs": [
                    "9.1. Nous pouvons mettre à jour cette politique. La version en vigueur est toujours disponible sur cette page, avec la date de mise à jour.",
                    "9.2. Pour toute question relative aux données personnelles, utilisez la rubrique «Contacts» du site Gestia Home.",
                ],
            },
        ],
    }


def cookies_doc() -> dict:
    return {
        "slug": "cookies",
        "title": "Politique cookies",
        "seo_title": "Politique cookies · Gestia Home",
        "seo_description": (
            "Quels cookies utilise le site Gestia Home, pourquoi, et comment gérer les paramètres."
        ),
        "sections": [
            {
                "heading": "1. Qu’est-ce qu’un cookie",
                "paragraphs": [
                    "1.1. Les cookies sont de petits fichiers texte stockés dans votre navigateur lorsque vous visitez le site Gestia Home.",
                    "1.2. Des technologies similaires (stockage local et de session) peuvent servir au même but, à savoir le fonctionnement du site.",
                ],
            },
            {
                "heading": "2. Pourquoi nous utilisons des cookies",
                "paragraphs": [
                    "2.1. Cookies nécessaires — pour le panier, les favoris, la langue, la devise, la session et la sécurité des formulaires (y compris CSRF).",
                    "2.2. Cookies fonctionnels — pour mémoriser vos préférences d’interface.",
                    "2.3. Cookies d’analyse (s’ils sont activés) — pour comprendre l’usage du site et l’améliorer. Gestia Home ne les utilise pas pour la publicité de tiers.",
                ],
            },
            {
                "heading": "3. Types de cookies pouvant être utilisés",
                "paragraphs": [
                    "3.1. Cookies de session — supprimés à la fermeture du navigateur.",
                    "3.2. Cookies persistants — conservés pendant une durée définie, ou jusqu’à ce que vous les supprimiez.",
                    "3.3. Cookies internes — déposés par notre site.",
                    "3.4. Cookies tiers — peuvent être déposés par des services connectés (paiement, analyse ou polices) s’ils sont actifs sur la page.",
                ],
            },
            {
                "heading": "4. Exemples de cookies nécessaires sur le site",
                "paragraphs": [
                    "4.1. L’identifiant de session Django — flux authentifiés et de session, panier et favoris.",
                    "4.2. Le cookie de langue — mémorisation de la langue d’interface choisie.",
                    "4.3. Le jeton CSRF — protection des formulaires contre les requêtes forgées.",
                    "4.4. Les données de devise d’affichage — tenues en session ou dans un stockage navigateur associé.",
                ],
            },
            {
                "heading": "5. Comment gérer les cookies",
                "paragraphs": [
                    "5.1. Vous pouvez limiter ou supprimer les cookies dans les paramètres de votre navigateur. Les instructions se trouvent généralement dans la rubrique «Confidentialité».",
                    "5.2. Désactiver les cookies nécessaires peut faire mal fonctionner le panier, les formulaires de commande et le changement de langue et de devise.",
                    "5.3. Sur mobile, le contrôle des cookies se trouve dans les réglages du navigateur (Safari, Chrome et autres).",
                ],
            },
            {
                "heading": "6. Consentement",
                "paragraphs": [
                    "6.1. En continuant à utiliser le site, vous acceptez l’usage des cookies nécessaires au fonctionnement de base du service.",
                    "6.2. Si nous activons des cookies d’analyse ou marketing facultatifs, nous en informerons séparément et, le cas échéant, demanderons votre consentement.",
                ],
            },
            {
                "heading": "7. Mises à jour de la politique",
                "paragraphs": [
                    "7.1. Nous pouvons mettre à jour la Politique cookies. La version en vigueur est publiée sur cette page, avec la date de mise à jour.",
                    "7.2. Les questions relatives aux cookies et aux données personnelles peuvent être envoyées via le formulaire de la rubrique «Contacts».",
                ],
            },
        ],
    }


def shipping_doc() -> dict:
    return {
        "slug": "shipping",
        "title": "Livraison et paiement",
        "seo_title": "Livraison et paiement · Gestia Home",
        "seo_description": (
            "Conditions de livraison et de paiement des commandes Gestia Home : Nova Poshta, coursier, paiement en ligne et à la livraison."
        ),
        "sections": [
            {
                "heading": "1. Conditions générales",
                "paragraphs": [
                    "1.1. Cette page décrit les modes de livraison et de paiement des commandes dans la boutique Gestia Home. Les conditions contractuelles détaillées figurent aussi dans le Contrat public (offre).",
                    "1.2. Lors de la commande, l’Acheteur choisit un mode de livraison et de paiement parmi ceux disponibles sur le site au moment du checkout.",
                    "1.3. Les prix des marchandises s’affichent dans la devise choisie (UAH ou EUR). Le montant final est fixé à la confirmation de la commande.",
                ],
            },
            {
                "heading": "2. Livraison",
                "paragraphs": [
                    "2.1. La livraison est effectuée par Nova Poshta sur le territoire de l’Ukraine.",
                    "2.2. Les options disponibles sont un point relais Nova Poshta, une consigne Nova Poshta et une livraison par coursier à l’adresse.",
                    "2.3. Le délai indicatif après remise de la commande au transporteur est de 1 à 3 jours ouvrés. Le délai réel dépend de la région et de la charge du transporteur.",
                    "2.4. Les frais de livraison sont calculés selon les tarifs du transporteur et sont généralement payés par l’Acheteur séparément à la réception, sauf accord contraire.",
                    "2.5. Après l’expédition, le Vendeur communique le numéro de bordereau (TTN) pour le suivi du colis.",
                    "2.6. La durée de conservation d’un colis en point relais ou en consigne est régie par les règles de Nova Poshta. Veuillez retirer votre commande à temps.",
                ],
            },
            {
                "heading": "3. Réception de la commande",
                "paragraphs": [
                    "3.1. À la réception, vérifiez l’intégrité de l’emballage. En cas de dommage, consignez-le avec un représentant du transporteur (constat) et informez Gestia Home.",
                    "3.2. Les réclamations relatives au contenu de la commande ou aux défauts visibles sont acceptées dans un délai raisonnable après réception, avec une photo et une description.",
                    "3.3. Si l’Acheteur a fourni des informations de livraison incorrectes, un nouvel envoi peut être facturé séparément.",
                ],
            },
            {
                "heading": "4. Paiement",
                "paragraphs": [
                    "4.1. En ligne par carte sur le site — Visa / Mastercard via un prestataire de paiement (si ce mode est actif au checkout).",
                    "4.2. Paiement à la livraison — selon les conditions du transporteur et la disponibilité de ce mode pour la commande.",
                    "4.3. Un paiement sur relevé bancaire peut être proposé par un conseiller après confirmation de la commande.",
                    "4.4. L’obligation du Vendeur d’expédier les marchandises naît après confirmation de la commande et, le cas échéant, après réception du paiement, selon le mode choisi.",
                ],
            },
            {
                "heading": "5. Préparation de la commande",
                "paragraphs": [
                    "5.1. Le délai de préparation dépend de la disponibilité des marchandises et de la charge de l’atelier. Les délais habituels sont confirmés par un conseiller lors de la confirmation.",
                    "5.2. Les pièces artisanales, ou fabriquées sur commande, peuvent nécessiter un délai supplémentaire. Vous en serez informé séparément.",
                    "5.3. Si un article est indisponible, le Vendeur proposera un remplacement, une attente ou une annulation avec remboursement (si le paiement a déjà été effectué).",
                ],
            },
            {
                "heading": "6. Remboursement des frais de livraison",
                "paragraphs": [
                    "6.1. Les frais de livraison ne sont généralement pas remboursés si le retour de marchandises de qualité conforme est initié par l’Acheteur et que le Vendeur n’est pas en faute, dans les limites de la loi.",
                    "6.2. En cas de défaut de fabrication, ou d’erreur du Vendeur dans le contenu de la commande, la question des frais de livraison lors d’un échange ou d’un retour est convenu au cas par cas.",
                ],
            },
            {
                "heading": "7. Contacts",
                "paragraphs": [
                    "7.1. Pour les questions de livraison et de paiement, utilisez le formulaire de la rubrique «Contacts» ou le numéro de téléphone indiqué sur le site.",
                    "7.2. Les conditions applicables peuvent être mises à jour. La date de la dernière mise à jour figure sur cette page.",
                ],
            },
        ],
    }


DOCS_FR = {
    "offer": offer_doc,
    "privacy": privacy_doc,
    "cookies": cookies_doc,
    "shipping": shipping_doc,
}
