# Informazioni su SearXNG

SearXNG è un [metamotore di ricerca] che aggrega i risultati di altri motori di
ricerca.  {{link('motori di ricerca', 'preferences')}} e non memorizza
informazioni sui suoi utenti.

Il progetto SearXNG è guidato da una comunità aperta, unisciti a noi su Matrix
se hai domande o vuoi semplicemente chiacchierare.  Se avete domande o volete
semplicemente parlare di SearXNG a [#searxng:matrix.org].

Migliorate SearXNG.

- Potete migliorare le traduzioni di SearXNG su [Weblate], oppure...
- Seguire lo sviluppo, inviare contributi e segnalare problemi a [sorgenti di
  SearXNG].
- Per ulteriori informazioni, visitate la documentazione del progetto SearXNG su
  [SearXNG docs].

## Perché usarlo?

- SearXNG non offre risultati personalizzati come Google, ma non genera un
  profilo dell'utente.
- SearXNG non si preoccupa di ciò che cercate, non condivide mai nulla con terze
  parti e non può essere usato per compromettere l'utente.
- SearXNG è un software libero, il codice è aperto al 100% e tutti sono invitati
  a migliorarlo.

Se avete a cuore la privacy, se volete essere un utente consapevole o se credete
nella libertà digitale, fate di SearXNG il vostro motore di ricerca predefinito
o eseguitelo sul vostro server!

## Come si imposta come motore di ricerca predefinito?

SearXNG supporta [OpenSearch].  Per ulteriori informazioni sulla modifica del
motore di ricerca motore di ricerca predefinito, consultare la documentazione
del browser:

- [Firefox]
- [Microsoft Edge] - nei link, troverete anche alcune utili istruzioni per
  Chrome e Safari.
- I browser basati su [Chromium] aggiungono solo i siti web a cui l'utente
  naviga senza un percorso.

Quando si aggiunge un motore di ricerca, non devono esserci duplicati con lo
stesso nome.  Se si verifica un problema per cui non si riesce ad aggiungere il
motore di ricerca, è possibile:

- rimuovere il duplicato (nome predefinito: SearXNG) o
- contattare il proprietario per assegnare all'istanza un nome diverso da quello
  predefinito.

## Come funziona?

SearXNG è un fork del ben noto [searx] [metamotore di ricerca] che è stato
ispirato dal [progetto Seeks].  Fornisce una privacy di base mescolando le
ricerche su altre piattaforme senza memorizzare i dati di ricerca.  SearXNG può
essere aggiunto alla barra di ricerca del browser; inoltre, può essere impostato
come motore di ricerca predefinito.

Il {{link('statistiche', 'stats')}} contiene alcune utili statistiche anonime di
utilizzo dei motori utilizzati.

## Come posso renderlo mio?

SearXNG apprezza la vostra preoccupazione per i log, quindi prendete il codice
dal file [sorgenti di SearXNG] ed eseguitelo voi stessi!

Aggiungete la vostra istanza a questo [elenco di istanze
pubbliche]({{get_setting('brand.public_instances')}}) per aiutare altre persone
a reclamare la propria privacy e a rendere Internet più libero.  Più internet è
decentralizzato più libertà abbiamo!


[sorgenti di SearXNG]: {{GIT_URL}}
[#searxng:matrix.org]: https://matrix.to/#/#searxng:matrix.org
[SearXNG docs]: {{get_setting('brand.docs_url')}}
[searx]: https://github.com/searx/searx
[metamotore di ricerca]: https://it.wikipedia.org/wiki/Metamotore
[Weblate]: https://translate.codeberg.org/projects/searxng/
[progetto Seeks]: https://beniz.github.io/seeks/
[OpenSearch]: https://github.com/dewitt/opensearch/blob/master/opensearch-1-1-draft-6.md
[Firefox]: https://support.mozilla.org/en-US/kb/add-or-remove-search-engine-firefox
[Microsoft Edge]: https://support.microsoft.com/en-us/help/4028574/microsoft-edge-change-the-default-search-engine
[Chromium]: https://www.chromium.org/tab-to-search
