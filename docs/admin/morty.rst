
.. _searxng morty:

=========================
How to setup result proxy
=========================

.. sidebar:: further reading

   - :ref:`morty.sh`

.. _morty: https://github.com/asciimoo/morty
.. _morty's README: https://github.com/asciimoo/morty

By default SearXNG can only act as an image proxy for result images, but it is
possible to proxify all the result URLs with an external service, morty_.

To use this feature, morty has to be installed and activated in SearXNG's
``settings.yml``.  Add the following snippet to your ``settings.yml`` and
restart searx:

.. code:: yaml

    result_proxy:
        url : http://127.0.0.1:3000/
        key : !!binary "insert_your_morty_proxy_key_here"

Note that the example above (``http://127.0.0.1:3000``) is only for single-user
instances without a HTTP proxy.  If your morty service is public, the url is the
address of the reverse proxy (e.g ``https://example.org/morty``).

For more information about *result proxy* have a look at *"SearXNG via filtron
plus morty"* in the :ref:`nginx <nginx searxng via filtron plus morty>` and
:ref:`apache <apache searxng via filtron plus morty>` sections.

``url``
  Is the address of the running morty service.

``key``
  Is an optional argument, see `morty's README`_ for more information.
