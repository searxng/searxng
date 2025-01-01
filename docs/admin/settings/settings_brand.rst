.. _settings brand:

==========
``brand:``
==========

.. code:: yaml

   brand:
     issue_url: https://github.com/searxng/searxng/issues
     docs_url: https://docs.searxng.org
     public_instances: https://searx.space
     wiki_url: https://github.com/searxng/searxng/wiki
     custom_files:
       logo: /path/to/file.png
       favicon_png: /path/to/file.png
       favicon_svg: /path/to/file.svg

``issue_url`` :
  If you host your own issue tracker change this URL.

``docs_url`` :
  If you host your own documentation change this URL.

``public_instances`` :
  If you host your own https://searx.space change this URL.

``wiki_url`` :
  Link to your wiki (or ``false``)

``custom_files.logo`` :
  Filepath to a custom logo. Be sure it has the right file extension, as that's used to determine the mimetype.

``custom_files.favicon_png`` :
  Filepath to a custom PNG favicon.

``custom_files.favicon_svg`` :
  Filepath to a custom SVG favicon. When using, be sure to also set ``custom_files.favicon_png``, as some browsers still don't support SVG favicons.
