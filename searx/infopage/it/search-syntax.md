# Sintassi di ricerca

SearXNG è dotato di una sintassi di ricerca che consente di modificare le
categorie, motori, lingue e altro ancora.  Vedere il {{link('preferenze',
'preferences')}} per l'elenco dei motori, delle categorie e delle lingue.

## `!` seleziona motore e gategoria

Per impostare i nomi delle categorie e/o dei motori, utilizzare il prefisso `!`.
Per fare qualche esempio:

- ricerca in Wikipedia per **parigi**

  - {{search('!wp parigi')}}
  - {{search('!wikipedia parigi')}}

- ricerca nella categoria **mappa** per **parigi**

- {{search('!map parigi')}}

- ricerca per immagini

- {{search('!images Wau Holland')}}

Sono accettate anche le abbreviazioni dei motori e delle lingue.  I modificatori
di motore/categoria sono modificatori a catena e inclusivi.  Ad esempio, con
{{search('!map !ddg !wp parigi')}} si cerca nella categoria mappe e DuckDuckGo e
Wikipedia per **parigi**.

## `:` selziona lingua

Per selezionare il filtro lingua utilizzare il prefisso `:`.  Per fare un esempio:

- cercare Wikipedia in base a una lingua personalizzata

  - {{search(':it !wp Wau Holland')}}

## `!!<bang>` bangs esterni

SearXNG supporta i bang esterni di [DuckDuckGo].  Per saltare direttamente a una
pagina di ricerca esterna utilizzare il prefisso `!!`.  Per fare un esempio:

- ricerca su Wikipedia in base a una lingua personalizzata

  - {{search('!!wde Wau Holland')}}

Si noti che la ricerca verrà eseguita direttamente nel motore di ricerca
esterno.  motore di ricerca esterno, SearXNG non può proteggere la privacy
dell'utente.

[DuckDuckGo]: https://duckduckgo.com/bang

## `!!` reindirizzamento automatico

Quando si menziona `!!` all'interno della query di ricerca (separata da spazi),
si viene automaticamente reindirizzati al primo risultato.  Questo comportamento
è paragonabile alla funzione "Mi sento fortunato" di DuckDuckGo.  Per fare un
esempio:

- cercare una query e venire reindirizzati al primo risultato

  - {{search('!! Wau Holland')}}

Si tenga presente che il risultato a cui si viene reindirizzati non può essere
verificato come affidabile, SearXNG non è in grado di proteggere la vostra
privacy personale quando utilizzate questa funzione.  Utilizzatela a vostro
rischio e pericolo.

## Queries Speciali

Nella pagina {{link('preferenze', 'preferences')}} si trovano parole chiave per
_query speciali_.  Per fare qualche esempio:

- Generare un UUID casuale

  - {{search('random uuid')}}

- Trovare la media

  - {{search('avg 123 548 2.04 24.2')}}

- Mostra l'_user agent_ del browser (deve essere attivato)

  - {{search('user-agent')}}

- Converte le stringhe in diversi hash digest (deve essere attivato)

  - {{search('md5 lorem ipsum')}}
  - {{search('sha512 lorem ipsum')}}
