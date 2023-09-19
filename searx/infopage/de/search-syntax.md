# Suchbegriffe

SearXNG verfügt über eine Syntax mit der in einer Suchanfrage die Kategorien,
Suchmaschinen, Sprachen und mehr geändert werden können.  In den
{{link('Eigenschaften','preferences')}} sind die Kategorien, Suchmaschinen und
Sprachen zu finden, die zur Verfügung stehen.

## `!` Suchmaschine und Kategorie auswählen

Zum Festlegen von Kategorie- und/oder Suchmaschinen dient das Präfix `!`.  Um
ein paar Beispiele zu geben:

- in der Wikipedia nach dem Begriff **paris** suchen

  - {{search('!wp paris')}}
  - {{search('!wikipedia paris')}}

- in der Kategorie **Karte** nach dem Begriff **paris** suchen:

  - {{search('!map paris')}}

- in der Kategorie **Bilder** suchen

  - {{search('!images Wau Holland')}}

Abkürzungen der Suchmaschinen und Kategorien sind ebenfalls möglich und können
auch kombiniert werden.  So wird z.B. mit {{search('!map !ddg !wp paris')}} in
der Kategorie **Karte** als auch mit den Suchmaschinen DuckDuckGo und Wikipedia
nach dem Begriff **paris** gesucht.

## `:` Sprache auswählen

Um einen Sprachfilter auszuwählen, verwenden Sie das Präfix `:`.  Um ein
einfaches Beispiel zu geben:

- Wikipedia mit einer benutzerdefinierten Sprache durchsuchen

  - {{search(':de !wp Wau Holland')}}

## `!!<bang>` external bangs

SearXNG unterstützt die _external bangs_ von [DuckDuckGo].  Das Präfix `!!` kann
verwendet werden um direkt zu einer externen Suchseite zu springen.  Um ein
Beispiel zu geben:

- In Wikipedia mit einer benutzerdefinierten Sprache eine Suche durchführen

  - {{search('!!wde Wau Holland')}}

Bitte beachten; die Suche wird direkt in der externen Suchmaschine durchgeführt.
SearXNG kann die Privatsphäre des Benutzers in diesem Fall nur eingeschränkt
schützen, dennoch wird diese Funktion von manchen Benutzern als sehr nützlich
empfunden.

[DuckDuckGo]: https://duckduckgo.com/bang

## `!!` automatic redirect

Bei der Verwendung von `!!` innerhalb der Suchanfrage (durch Leerzeichen
getrennt), wird automatisch zum ersten Ergebnis weitergeleitet.  Dieses
Verhalten ist vergleichbar mit der "Feeling Lucky"-Funktion von DuckDuckGo.  Um
ein Beispiel zu geben:

- Suchanfrage und direkte Weiterleitung zum ersten Ergebnis

  - {{search('!! Wau Holland')}}

Bitte beachten: das Ergebnis zu dem weitergeleitet wird, kann nicht auf seine
Vertrauenswürdigkeit überprüft werden.  SearXNG kann die Privatsphäre des
Benutzers in diesem Fall nicht schützen, dennoch wird diese Funktion von manchen
Benutzern als sehr nützlich empfunden.

## Besondere Abfragen

In den {{link('Eigenschaften', 'preferences')}} finden sich Schlüsselwörter für
_besondere Abfragen_.  Um ein paar Beispiele zu geben:

- Zufallsgenerator für eine UUID

  - {{search('random uuid')}}

- Bestimmung des Mittelwerts

  - {{search('avg 123 548 2.04 24.2')}}

- anzeigen des _user agent_ Ihres WEB-Browsers (muss aktiviert sein)

  - {{search('user-agent')}}

- Zeichenketten in verschiedene Hash-Digests umwandeln  (muss aktiviert sein)

  - {{search('md5 lorem ipsum')}}
  - {{search('sha512 lorem ipsum')}}
