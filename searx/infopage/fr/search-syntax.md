# Syntaxe de recherche

SearXNG permet de modifier les catégories de recherche, les moteurs
utilisés ou encore la langue de recherche par l'intermédiaire d'une
syntaxe dédiée. La liste des moteurs de recherche, de catégories et de
langues disponibles est accessible depuis la page de
{{link('préférences', 'preferences')}}.

## `!` Spécifier un moteur ou une catégorie

Pour restreindre la recherche à un moteur ou une catégorie, utilisez le
caractère "!". Voici quelques exemples d'utilisation :

- Rechercher **paris** sur Wikipédia.

  - {{search('!wp paris')}}
  - {{search('!wikipedia paris')}}

- Rechercher **paris** dans la catégorie **Carte**.

  - {{search('!map paris')}}

- Rechercher des **Images**.

  - {{search('!images Wau Holland')}}

Les abréviations de moteurs et de langues sont aussi valides. Il est
possible d'accumuler les moteurs et catégories dans une requête
complexe. Par exemple, {{search('!map !ddg !wp paris')}} recherchera
**paris** dans la catégorie **Carte** de DuckDuckGo et Wikipédia.

## `:` Spécifier une langue

Utilisez le préfixe ":" pour limiter la recherche à une langue en
particulier. Par exemple :

- Rechercher dans les pages françaises de Wikipédia.

  - {{search(':fr !wp Wau Holland')}}

## `!!<bang>` Recherches externes (!Bang)

SearXNG supporte les recherches [DuckDuckGo] de type "!Bang". Utilisez
le préfixe "!!" pour être automatiquement redirigé vers un moteur de
recherche externe. Par exemple :

- Rechercher sur Wikipédia en langue française.

  - {{search('!!wfr Wau Holland')}}

Prenez garde au fait que de telles recherches sont exécutées directement
sur le moteur externe. Dans ce cas, SearXNG ne peut pas protéger votre
vie privée.

[DuckDuckGo]: https://duckduckgo.com/bang

## `!!` Redirection automatique

En utilisant "!!" suivi d'un ou plusieurs espaces lors de votre
recherche, vous serez automatiquement redirigé vers le premier résultat
de recherche. Cela correspondant au fonctionnement "J'ai de la chance"
du moteur Google. Par exemple :

- Rechercher et être redirigé directement vers le premier lien
  correspondant.

  - {{search('!! Wau Holland')}}

Prenez garde au fait qu'aucune vérification ne peut être faite
concernant le premier lien retourné. Il pourrait même s'agir d'un site
dangereux. Dans ce cas, SearXNG ne peut pas protéger votre vie
privée. Soyez prudent en utilisant cette fonctionnalité.

## Requêtes spéciales

Dans la section _requêtes spéciales_ de la page de {{link('préférences',
'preferences')}} se trouve une liste de mots clés à usage particulier.
Par exemple :

- Générer une valeur aléatoire.

  - {{search('random uuid')}}

- Calculer une moyenne.

  - {{search('avg 123 548 2.04 24.2')}}

- Afficher la valeur de la variable _User-Agent_ utilisée par votre
  navigateur (doit être activé manuellement).

  - {{search('user-agent')}}

- Convertir une chaîne de caractères en valeurs de hachage ("hash digests")
  (doit être activé manuellement).

  - {{search('md5 lorem ipsum')}}
  - {{search('sha512 lorem ipsum')}}
