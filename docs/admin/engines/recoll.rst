.. _engine recoll:

=============
Recoll Engine
=============

.. sidebar:: info

   - `Recoll <https://www.lesbonscomptes.com/recoll/>`_
   - `recoll-webui <https://framagit.org/medoc92/recollwebui.git>`_
   - :origin:`searx/engines/recoll.py`

Recoll_ is a desktop full-text search tool based on Xapian.  By itself Recoll_
does not offer WEB or API access, this can be achieved using recoll-webui_


Configuration
=============

You must configure the following settings:

``base_url``:
  Location where recoll-webui can be reached.

``mount_prefix``:
  Location where the file hierarchy is mounted on your *local* filesystem.

``dl_prefix``:
  Location where the file hierarchy as indexed by recoll can be reached.

``search_dir``:
  Part of the indexed file hierarchy to be search, if empty the full domain is
  searched.


Example
=======

Scenario:

#. Recoll indexes a local filesystem mounted in ``/export/documents/reference``,
#. the Recoll search inteface can be reached at https://recoll.example.org/ and
#. the contents of this filesystem can be reached though https://download.example.org/reference

.. code:: yaml

   base_url: https://recoll.example.org/
   mount_prefix: /export/documents
   dl_prefix: https://download.example.org
   search_dir: ''
