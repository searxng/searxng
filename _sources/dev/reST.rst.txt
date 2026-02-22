.. _reST primer:

===========
reST primer
===========

.. sidebar:: KISS_ and readability_

   Instead of defining more and more roles, we at SearXNG encourage our
   contributors to follow principles like KISS_ and readability_.

We at SearXNG are using reStructuredText (aka reST_) markup for all kind of
documentation.  With the builders from the Sphinx_ project a HTML output is
generated and deployed at docs.searxng.org_.  For build prerequisites read
:ref:`docs build`.

.. _docs.searxng.org: https://docs.searxng.org/

The source files of SearXNG's documentation are located at :origin:`docs`.
Sphinx assumes source files to be encoded in UTF-8 by default.  Run :ref:`make
docs.live <make docs.live>` to build HTML while editing.

.. sidebar:: Further reading

   - Sphinx-Primer_
   - `Sphinx markup constructs`_
   - reST_, docutils_, `docutils FAQ`_
   - Sphinx_, `sphinx-doc FAQ`_
   - `sphinx config`_, doctree_
   - `sphinx cross references`_
   - linuxdoc_
   - intersphinx_
   - sphinx-jinja_
   - `Sphinx's autodoc`_
   - `Sphinx's Python domain`_, `Sphinx's C domain`_
   - SVG_, ImageMagick_
   - DOT_, `Graphviz's dot`_, Graphviz_


.. contents::
   :depth: 3
   :local:
   :backlinks: entry

Sphinx_ and reST_ have their place in the python ecosystem.  Over that reST is
used in popular projects, e.g the Linux kernel documentation `[kernel doc]`_.

.. _[kernel doc]: https://www.kernel.org/doc/html/latest/doc-guide/sphinx.html

.. sidebar:: Content matters

   The readability_ of the reST sources has its value, therefore we recommend to
   make sparse usage of reST markup / .. content matters!

**reST** is a plaintext markup language, its markup is *mostly* intuitive and
you will not need to learn much to produce well formed articles with.  I use the
word *mostly*: like everything in live, reST has its advantages and
disadvantages, some markups feel a bit grumpy (especially if you are used to
other plaintext markups).

Soft skills
===========

Before going any deeper into the markup let's face on some **soft skills** a
trained author brings with, to reach a well feedback from readers:

- Documentation is dedicated to an audience and answers questions from the
  audience point of view.
- Don't detail things which are general knowledge from the audience point of
  view.
- Limit the subject, use cross links for any further reading.

To be more concrete what a *point of view* means.  In the (:origin:`docs`)
folder we have three sections (and the *blog* folder), each dedicate to a
different group of audience.

User's POV: :origin:`docs/user`
  A typical user knows about search engines and might have heard about
  meta crawlers and privacy.

Admin's POV: :origin:`docs/admin`
  A typical Admin knows about setting up services on a linux system, but he does
  not know all the pros and cons of a SearXNG setup.

Developer's POV: :origin:`docs/dev`
  Depending on the readability_ of code, a typical developer is able to read and
  understand source code.  Describe what a item aims to do (e.g. a function).
  If the chronological order matters, describe it.  Name the *out-of-limits
  conditions* and all the side effects a external developer will not know.

.. _reST inline markup:

Basic inline markup
===================

.. sidebar:: Inline markup

   - :ref:`reST roles`
   - :ref:`reST smart ref`

Basic inline markup is done with asterisks and backquotes.  If asterisks or
backquotes appear in running text and could be confused with inline markup
delimiters, they have to be escaped with a backslash (``\*pointer``).

.. table:: basic inline markup
   :widths: 4 3 7

   ================================================ ==================== ========================
   description                                      rendered             markup
   ================================================ ==================== ========================
   one asterisk for emphasis                        *italics*            ``*italics*``
   two asterisks for strong emphasis                **boldface**         ``**boldface**``
   backquotes for code samples and literals         ``foo()``            ````foo()````
   quote asterisks or backquotes                    \*foo is a pointer   ``\*foo is a pointer``
   ================================================ ==================== ========================

.. _reST basic structure:

Basic article structure
=======================

The basic structure of an article makes use of heading adornments to markup
chapter, sections and subsections.

.. _reST template:

reST template
-------------

reST template for an simple article:

.. code:: reST

    .. _doc refname:

    ==============
    Document title
    ==============

    Lorem ipsum dolor sit amet, consectetur adipisici elit ..  Further read
    :ref:`chapter refname`.

    .. _chapter refname:

    Chapter
    =======

    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
    aliquid ex ea commodi consequat ...

    .. _section refname:

    Section
    -------

    lorem ..

    .. _subsection refname:

    Subsection
    ~~~~~~~~~~

    lorem ..


Headings
--------

#. title - with overline for document title:

  .. code:: reST

    ==============
    Document title
    ==============


#. chapter - with anchor named ``anchor name``:

   .. code:: reST

      .. _anchor name:

      Chapter
      =======

#. section

   .. code:: reST

      Section
      -------

#. subsection

   .. code:: reST

      Subsection
      ~~~~~~~~~~



Anchors & Links
===============

.. _reST anchor:

Anchors
-------

.. _ref role:
   https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#role-ref

To refer a point in the documentation a anchor is needed.  The :ref:`reST
template <reST template>` shows an example where a chapter titled *"Chapters"*
gets an anchor named ``chapter title``.  Another example from *this* document,
where the anchor named ``reST anchor``:

.. code:: reST

   .. _reST anchor:

   Anchors
   -------

   To refer a point in the documentation a anchor is needed ...

To refer anchors use the `ref role`_ markup:

.. code:: reST

   Visit chapter :ref:`reST anchor`.  Or set hyperlink text manually :ref:`foo
   bar <reST anchor>`.

.. admonition:: ``:ref:`` role
   :class: rst-example

   Visit chapter :ref:`reST anchor`.  Or set hyperlink text manually :ref:`foo
   bar <reST anchor>`.

.. _reST ordinary ref:

Link ordinary URL
-----------------

If you need to reference external URLs use *named* hyperlinks to maintain
readability of reST sources.  Here is a example taken from *this* article:

.. code:: reST

   .. _Sphinx Field Lists:
      https://www.sphinx-doc.org/en/master/usage/restructuredtext/field-lists.html

   With the *named* hyperlink `Sphinx Field Lists`_, the raw text is much more
   readable.

   And this shows the alternative (less readable) hyperlink markup `Sphinx Field
   Lists
   <https://www.sphinx-doc.org/en/master/usage/restructuredtext/field-lists.html>`__.

.. admonition:: Named hyperlink
   :class: rst-example

   With the *named* hyperlink `Sphinx Field Lists`_, the raw text is much more
   readable.

   And this shows the alternative (less readable) hyperlink markup `Sphinx Field
   Lists
   <https://www.sphinx-doc.org/en/master/usage/restructuredtext/field-lists.html>`__.


.. _reST smart ref:

Smart refs
----------

With the power of sphinx.ext.extlinks_ and intersphinx_ referencing external
content becomes smart.

.. table:: smart refs with sphinx.ext.extlinks_ and intersphinx_
   :widths: 4 3 7

   ========================== ================================== ====================================
   refer ...                  rendered example                   markup
   ========================== ================================== ====================================
   :rst:role:`rfc`            :rfc:`822`                         ``:rfc:`822```
   :rst:role:`pep`            :pep:`8`                           ``:pep:`8```
   sphinx.ext.extlinks_
   --------------------------------------------------------------------------------------------------
   project's wiki article     :wiki:`Offline-engines`            ``:wiki:`Offline-engines```
   to docs public URL         :docs:`dev/reST.html`              ``:docs:`dev/reST.html```
   files & folders origin     :origin:`docs/dev/reST.rst`        ``:origin:`docs/dev/reST.rst```
   pull request               :pull:`4`                          ``:pull:`4```
   patch                      :patch:`af2cae6`                   ``:patch:`af2cae6```
   PyPi package               :pypi:`httpx`                      ``:pypi:`httpx```
   manual page man            :man:`bash`                        ``:man:`bash```
   intersphinx_
   --------------------------------------------------------------------------------------------------
   external anchor            :ref:`python:and`                  ``:ref:`python:and```
   external doc anchor        :doc:`jinja:templates`             ``:doc:`jinja:templates```
   python code object         :py:obj:`datetime.datetime`        ``:py:obj:`datetime.datetime```
   flask code object          :py:obj:`flask.Flask`              ``:py:obj:`flask.Flask```
   ========================== ================================== ====================================


Intersphinx is configured in :origin:`docs/conf.py`:

.. code:: python

    intersphinx_mapping = {
        "python": ("https://docs.python.org/3/", None),
        "flask": ("https://flask.palletsprojects.com/", None),
        "jinja": ("https://jinja.palletsprojects.com/", None),
        "linuxdoc" : ("https://return42.github.io/linuxdoc/", None),
        "sphinx" : ("https://www.sphinx-doc.org/en/master/", None),
    }


To list all anchors of the inventory (e.g. ``python``) use:

.. code:: sh

   $ python -m sphinx.ext.intersphinx https://docs.python.org/3/objects.inv
   ...
   $ python -m sphinx.ext.intersphinx https://docs.searxng.org/objects.inv
   ...

Literal blocks
==============

The simplest form of :duref:`literal-blocks` is a indented block introduced by
two colons (``::``).  For highlighting use :dudir:`highlight` or :ref:`reST
code` directive.  To include literals from external files use
:rst:dir:`literalinclude` or :ref:`kernel-include <kernel-include-directive>`
directive (latter one expands environment variables in the path name).

.. _reST literal:

``::``
------

.. code:: reST

   ::

     Literal block

   Lorem ipsum dolor::

     Literal block

   Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy
   eirmod tempor invidunt ut labore ::

     Literal block

.. admonition:: Literal block
   :class: rst-example

   ::

     Literal block

   Lorem ipsum dolor::

     Literal block

   Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy
   eirmod tempor invidunt ut labore ::

     Literal block


.. _reST code:

``code-block``
--------------

.. _pygments: https://pygments.org/languages/

.. sidebar:: Syntax highlighting

   is handled by pygments_.

The :rst:dir:`code-block` directive is a variant of the :dudir:`code` directive
with additional options.  To learn more about code literals visit
:ref:`sphinx:code-examples`.

.. code-block:: reST

   The URL ``/stats`` handle is shown in :ref:`stats-handle`

   .. code-block:: Python
      :caption: python code block
      :name: stats-handle

      @app.route('/stats', methods=['GET'])
      def stats():
          """Render engine statistics page."""
          stats = get_engines_stats()
          return render(
              'stats.html'
              , stats = stats )

.. code-block:: reST

.. admonition:: Code block
   :class: rst-example

   The URL ``/stats`` handle is shown in :ref:`stats-handle`

   .. code-block:: Python
      :caption: python code block
      :name: stats-handle

      @app.route('/stats', methods=['GET'])
      def stats():
          """Render engine statistics page."""
          stats = get_engines_stats()
          return render(
              'stats.html'
              , stats = stats )

Unicode substitution
====================

The :dudir:`unicode directive <unicode-character-codes>` converts Unicode
character codes (numerical values) to characters.  This directive can only be
used within a substitution definition.

.. code-block:: reST

   .. |copy| unicode:: 0xA9 .. copyright sign
   .. |(TM)| unicode:: U+2122

   Trademark |(TM)| and copyright |copy| glyphs.

.. admonition:: Unicode
   :class: rst-example

   .. |copy| unicode:: 0xA9 .. copyright sign
   .. |(TM)| unicode:: U+2122

   Trademark |(TM)| and copyright |copy| glyphs.


.. _reST roles:

Roles
=====

.. sidebar:: Further reading

   - `Sphinx Roles`_
   - :doc:`sphinx:usage/restructuredtext/domains`


A *custom interpreted text role* (:duref:`ref <roles>`) is an inline piece of
explicit markup.  It signifies that that the enclosed text should be interpreted
in a specific way.

The general markup is one of:

.. code:: reST

   :rolename:`ref-name`
   :rolename:`ref text <ref-name>`

.. table:: smart refs with sphinx.ext.extlinks_ and intersphinx_
   :widths: 4 3 7

   ========================== ================================== ====================================
   role                       rendered example                   markup
   ========================== ================================== ====================================
   :rst:role:`guilabel`       :guilabel:`&Cancel`                ``:guilabel:`&Cancel```
   :rst:role:`kbd`            :kbd:`C-x C-f`                     ``:kbd:`C-x C-f```
   :rst:role:`menuselection`  :menuselection:`Open --> File`     ``:menuselection:`Open --> File```
   :rst:role:`download`       :download:`this file <reST.rst>`   ``:download:`this file <reST.rst>```
   math_                      :math:`a^2 + b^2 = c^2`            ``:math:`a^2 + b^2 = c^2```
   :rst:role:`ref`            :ref:`svg image example`           ``:ref:`svg image example```
   :rst:role:`command`        :command:`ls -la`                  ``:command:`ls -la```
   :durole:`emphasis`         :emphasis:`italic`                 ``:emphasis:`italic```
   :durole:`strong`           :strong:`bold`                     ``:strong:`bold```
   :durole:`literal`          :literal:`foo()`                   ``:literal:`foo()```
   :durole:`subscript`        H\ :sub:`2`\ O                     ``H\ :sub:`2`\ O``
   :durole:`superscript`      E = mc\ :sup:`2`                   ``E = mc\ :sup:`2```
   :durole:`title-reference`  :title:`Time`                      ``:title:`Time```
   ========================== ================================== ====================================

Figures & Images
================

.. sidebar:: Image processing

   With the directives from :ref:`linuxdoc <linuxdoc:kfigure>` the build process
   is flexible.  To get best results in the generated output format, install
   ImageMagick_ and Graphviz_.

SearXNG's sphinx setup includes: :ref:`linuxdoc:kfigure`.  Scalable here means;
scalable in sense of the build process.  Normally in absence of a converter
tool, the build process will break.  From the authors POV it’s annoying to care
about the build process when handling with images, especially since he has no
access to the build process.  With :ref:`linuxdoc:kfigure` the build process
continues and scales output quality in dependence of installed image processors.

If you want to add an image, you should use the ``kernel-figure`` (inheritance
of :dudir:`figure`) and ``kernel-image`` (inheritance of :dudir:`image`)
directives.  E.g. to insert a figure with a scalable image format use SVG
(:ref:`svg image example`):

.. code:: reST

   .. _svg image example:

   .. kernel-figure:: svg_image.svg
      :alt: SVG image example

      Simple SVG image

    To refer the figure, a caption block is needed: :ref:`svg image example`.

.. _svg image example:

.. kernel-figure:: svg_image.svg
   :alt: SVG image example

   Simple SVG image.

To refer the figure, a caption block is needed: :ref:`svg image example`.

DOT files (aka Graphviz)
------------------------

With :ref:`linuxdoc:kernel-figure` reST support for **DOT** formatted files is
given.

- `Graphviz's dot`_
- DOT_
- Graphviz_

A simple example is shown in :ref:`dot file example`:

.. code:: reST

   .. _dot file example:

   .. kernel-figure:: hello.dot
      :alt: hello world

      DOT's hello world example

.. admonition:: hello.dot
   :class: rst-example

   .. _dot file example:

   .. kernel-figure:: hello.dot
      :alt: hello world

      DOT's hello world example

``kernel-render`` DOT
---------------------

Embed *render* markups (or languages) like Graphviz's **DOT** is provided by the
:ref:`linuxdoc:kernel-render` directive.  A simple example of embedded DOT_ is
shown in figure :ref:`dot render example`:

.. code:: reST

   .. _dot render example:

   .. kernel-render:: DOT
      :alt: digraph
      :caption: Embedded  DOT (Graphviz) code

      digraph foo {
        "bar" -> "baz";
      }

   Attribute ``caption`` is needed, if you want to refer the figure: :ref:`dot
   render example`.

Please note :ref:`build tools <linuxdoc:kfigure_build_tools>`.  If Graphviz_ is
installed, you will see an vector image.  If not, the raw markup is inserted as
*literal-block*.

.. admonition:: kernel-render DOT
   :class: rst-example

   .. _dot render example:

   .. kernel-render:: DOT
      :alt: digraph
      :caption: Embedded  DOT (Graphviz) code

      digraph foo {
        "bar" -> "baz";
      }

   Attribute ``caption`` is needed, if you want to refer the figure: :ref:`dot
   render example`.

``kernel-render`` SVG
---------------------

A simple example of embedded SVG_ is shown in figure :ref:`svg render example`:

.. code:: reST

   .. _svg render example:

   .. kernel-render:: SVG
      :caption: Embedded **SVG** markup
      :alt: so-nw-arrow
..

  .. code:: xml

      <?xml version="1.0" encoding="UTF-8"?>
      <svg xmlns="http://www.w3.org/2000/svg" version="1.1"
           baseProfile="full" width="70px" height="40px"
           viewBox="0 0 700 400"
           >
        <line x1="180" y1="370"
              x2="500" y2="50"
              stroke="black" stroke-width="15px"
              />
        <polygon points="585 0 525 25 585 50"
                 transform="rotate(135 525 25)"
                 />
      </svg>

.. admonition:: kernel-render SVG
   :class: rst-example

   .. _svg render example:

   .. kernel-render:: SVG
      :caption: Embedded **SVG** markup
      :alt: so-nw-arrow

      <?xml version="1.0" encoding="UTF-8"?>
      <svg xmlns="http://www.w3.org/2000/svg" version="1.1"
           baseProfile="full" width="70px" height="40px"
           viewBox="0 0 700 400"
           >
        <line x1="180" y1="370"
              x2="500" y2="50"
              stroke="black" stroke-width="15px"
              />
        <polygon points="585 0 525 25 585 50"
                 transform="rotate(135 525 25)"
                 />
      </svg>




.. _reST lists:

List markups
============

Bullet list
-----------

List markup (:duref:`ref <bullet-lists>`) is simple:

.. code:: reST

   - This is a bulleted list.

     1. Nested lists are possible, but be aware that they must be separated from
        the parent list items by blank line
     2. Second item of nested list

   - It has two items, the second
     item uses two lines.

   #. This is a numbered list.
   #. It has two items too.

.. admonition:: bullet list
   :class: rst-example

   - This is a bulleted list.

     1. Nested lists are possible, but be aware that they must be separated from
        the parent list items by blank line
     2. Second item of nested list

   - It has two items, the second
     item uses two lines.

   #. This is a numbered list.
   #. It has two items too.


Horizontal list
---------------

The :rst:dir:`.. hlist:: <hlist>` transforms a bullet list into a more compact
list.

.. code:: reST

   .. hlist::

      - first list item
      - second list item
      - third list item
      ...

.. admonition:: hlist
   :class: rst-example

   .. hlist::

      - first list item
      - second list item
      - third list item
      - next list item
      - next list item xxxx
      - next list item yyyy
      - next list item zzzz


Definition list
---------------

.. sidebar:: Note ..

   - the term cannot have more than one line of text

   - there is **no blank line between term and definition block** // this
     distinguishes definition lists (:duref:`ref <definition-lists>`) from block
     quotes (:duref:`ref <block-quotes>`).

Each definition list (:duref:`ref <definition-lists>`) item contains a term,
optional classifiers and a definition.  A term is a simple one-line word or
phrase.  Optional classifiers may follow the term on the same line, each after
an inline ' : ' (**space, colon, space**).  A definition is a block indented
relative to the term, and may contain multiple paragraphs and other body
elements.  There may be no blank line between a term line and a definition block
(*this distinguishes definition lists from block quotes*).  Blank lines are
required before the first and after the last definition list item, but are
optional in-between.

Definition lists are created as follows:

.. code:: reST

   term 1 (up to a line of text)
       Definition 1.

   See the typo : this line is not a term!

     And this is not term's definition.  **There is a blank line** in between
     the line above and this paragraph.  That's why this paragraph is taken as
     **block quote** (:duref:`ref <block-quotes>`) and not as term's definition!

   term 2
       Definition 2, paragraph 1.

       Definition 2, paragraph 2.

   term 3 : classifier
       Definition 3.

   term 4 : classifier one : classifier two
       Definition 4.

.. admonition:: definition list
   :class: rst-example

   term 1 (up to a line of text)
       Definition 1.

   See the typo : this line is not a term!

     And this is not term's definition.  **There is a blank line** in between
     the line above and this paragraph.  That's why this paragraph is taken as
     **block quote** (:duref:`ref <block-quotes>`) and not as term's definition!


   term 2
       Definition 2, paragraph 1.

       Definition 2, paragraph 2.

   term 3 : classifier
       Definition 3.

   term 4 : classifier one : classifier two


Quoted paragraphs
-----------------

Quoted paragraphs (:duref:`ref <block-quotes>`) are created by just indenting
them more than the surrounding paragraphs.  Line blocks (:duref:`ref
<line-blocks>`) are a way of preserving line breaks:

.. code:: reST

   normal paragraph ...
   lorem ipsum.

      Quoted paragraph ...
      lorem ipsum.

   | These lines are
   | broken exactly like in
   | the source file.


.. admonition:: Quoted paragraph and line block
   :class: rst-example

   normal paragraph ...
   lorem ipsum.

      Quoted paragraph ...
      lorem ipsum.

   | These lines are
   | broken exactly like in
   | the source file.


.. _reST field list:

Field Lists
-----------

.. _Sphinx Field Lists:
   https://www.sphinx-doc.org/en/master/usage/restructuredtext/field-lists.html

.. sidebar::  bibliographic fields

   First lines fields are bibliographic fields, see `Sphinx Field Lists`_.

Field lists are used as part of an extension syntax, such as options for
directives, or database-like records meant for further processing.  Field lists
are mappings from field names to field bodies.  They marked up like this:

.. code:: reST

   :fieldname: Field content
   :foo:       first paragraph in field foo

               second paragraph in field foo

   :bar:       Field content

.. admonition:: Field List
   :class: rst-example

   :fieldname: Field content
   :foo:       first paragraph in field foo

               second paragraph in field foo

   :bar:       Field content


They are commonly used in Python documentation:

.. code:: python

   def my_function(my_arg, my_other_arg):
       """A function just for me.

       :param my_arg: The first of my arguments.
       :param my_other_arg: The second of my arguments.

       :returns: A message (just for me, of course).
       """

Further list blocks
-------------------

- field lists (:duref:`ref <field-lists>`, with caveats noted in
  :ref:`reST field list`)
- option lists (:duref:`ref <option-lists>`)
- quoted literal blocks (:duref:`ref <quoted-literal-blocks>`)
- doctest blocks (:duref:`ref <doctest-blocks>`)


Admonitions
===========

Sidebar
-------

Sidebar is an eye catcher, often used for admonitions pointing further stuff or
site effects.  Here is the source of the sidebar :ref:`on top of this page <reST
primer>`.

.. code:: reST

   .. sidebar:: KISS_ and readability_

      Instead of defining more and more roles, we at SearXNG encourage our
      contributors to follow principles like KISS_ and readability_.

Generic admonition
------------------

The generic :dudir:`admonition <admonitions>` needs a title:

.. code:: reST

   .. admonition:: generic admonition title

      lorem ipsum ..


.. admonition:: generic admonition title

   lorem ipsum ..


Specific admonitions
--------------------

Specific admonitions: :dudir:`hint`, :dudir:`note`, :dudir:`tip` :dudir:`attention`,
:dudir:`caution`, :dudir:`danger`, :dudir:`error`, , :dudir:`important`, and
:dudir:`warning` .

.. code:: reST

   .. hint::

      lorem ipsum ..

   .. note::

      lorem ipsum ..

   .. warning::

      lorem ipsum ..


.. hint::

   lorem ipsum ..

.. note::

   lorem ipsum ..

.. tip::

   lorem ipsum ..

.. attention::

   lorem ipsum ..

.. caution::

   lorem ipsum ..

.. danger::

   lorem ipsum ..

.. important::

   lorem ipsum ..

.. error::

   lorem ipsum ..

.. warning::

   lorem ipsum ..


Tables
======

.. sidebar:: Nested tables

   Nested tables are ugly! Not all builder support nested tables, don't use
   them!

ASCII-art tables like :ref:`reST simple table` and :ref:`reST grid table` might
be comfortable for readers of the text-files, but they have huge disadvantages
in the creation and modifying.  First, they are hard to edit.  Think about
adding a row or a column to a ASCII-art table or adding a paragraph in a cell,
it is a nightmare on big tables.


.. sidebar:: List tables

   For meaningful patch and diff use :ref:`reST flat table`.

Second the diff of modifying ASCII-art tables is not meaningful, e.g. widening a
cell generates a diff in which also changes are included, which are only
ascribable to the ASCII-art.  Anyway, if you prefer ASCII-art for any reason,
here are some helpers:

* `Emacs Table Mode`_
* `Online Tables Generator`_

.. _reST simple table:

Simple tables
-------------

:duref:`Simple tables <simple-tables>` allow *colspan* but not *rowspan*.  If
your table need some metadata (e.g. a title) you need to add the ``.. table::
directive`` :dudir:`(ref) <table>` in front and place the table in its body:

.. code:: reST

   .. table:: foo gate truth table
      :widths: grid
      :align: left

      ====== ====== ======
          Inputs    Output
      ------------- ------
      A      B      A or B
      ====== ====== ======
      False
      --------------------
      True
      --------------------
      True   False  True
             (foo)
      ------ ------ ------
      False  True
             (foo)
      ====== =============

.. admonition:: Simple ASCII table
   :class: rst-example

   .. table:: foo gate truth table
      :widths: grid
      :align: left

      ====== ====== ======
          Inputs    Output
      ------------- ------
      A      B      A or B
      ====== ====== ======
      False
      --------------------
      True
      --------------------
      True   False  True
             (foo)
      ------ ------ ------
      False  True
             (foo)
      ====== =============



.. _reST grid table:

Grid tables
-----------

:duref:`Grid tables <grid-tables>` allow colspan *colspan* and *rowspan*:

.. code:: reST

   .. table:: grid table example
      :widths: 1 1 5

      +------------+------------+-----------+
      | Header 1   | Header 2   | Header 3  |
      +============+============+===========+
      | body row 1 | column 2   | column 3  |
      +------------+------------+-----------+
      | body row 2 | Cells may span columns.|
      +------------+------------+-----------+
      | body row 3 | Cells may  | - Cells   |
      +------------+ span rows. | - contain |
      | body row 4 |            | - blocks. |
      +------------+------------+-----------+

.. admonition:: ASCII grid table
   :class: rst-example

   .. table:: grid table example
      :widths: 1 1 5

      +------------+------------+-----------+
      | Header 1   | Header 2   | Header 3  |
      +============+============+===========+
      | body row 1 | column 2   | column 3  |
      +------------+------------+-----------+
      | body row 2 | Cells may span columns.|
      +------------+------------+-----------+
      | body row 3 | Cells may  | - Cells   |
      +------------+ span rows. | - contain |
      | body row 4 |            | - blocks. |
      +------------+------------+-----------+


.. _reST flat table:

flat-table
----------

The ``flat-table`` is a further developed variant of the :ref:`list tables
<linuxdoc:list-table-directives>`.  It is a double-stage list similar to the
:dudir:`list-table` with some additional features:

column-span: ``cspan``
  with the role ``cspan`` a cell can be extended through additional columns

row-span: ``rspan``
  with the role ``rspan`` a cell can be extended through additional rows

auto-span:
  spans rightmost cell of a table row over the missing cells on the right side
  of that table-row.  With Option ``:fill-cells:`` this behavior can changed
  from *auto span* to *auto fill*, which automatically inserts (empty) cells
  instead of spanning the last cell.

options:
  :header-rows:   [int] count of header rows
  :stub-columns:  [int] count of stub columns
  :widths:        [[int] [int] ... ] widths of columns
  :fill-cells:    instead of auto-span missing cells, insert missing cells

roles:
  :cspan: [int] additional columns (*morecols*)
  :rspan: [int] additional rows (*morerows*)

The example below shows how to use this markup.  The first level of the staged
list is the *table-row*. In the *table-row* there is only one markup allowed,
the list of the cells in this *table-row*. Exception are *comments* ( ``..`` )
and *targets* (e.g. a ref to :ref:`row 2 of table's body <row body 2>`).

.. code:: reST

   .. flat-table:: ``flat-table`` example
      :header-rows: 2
      :stub-columns: 1
      :widths: 1 1 1 1 2

      * - :rspan:`1` head / stub
        - :cspan:`3` head 1.1-4

      * - head 2.1
        - head 2.2
        - head 2.3
        - head 2.4

      * .. row body 1 / this is a comment

        - row 1
        - :rspan:`2` cell 1-3.1
        - cell 1.2
        - cell 1.3
        - cell 1.4

      * .. Comments and targets are allowed on *table-row* stage.
        .. _`row body 2`:

        - row 2
        - cell 2.2
        - :rspan:`1` :cspan:`1`
          cell 2.3 with a span over

          * col 3-4 &
          * row 2-3

      * - row 3
        - cell 3.2

      * - row 4
        - cell 4.1
        - cell 4.2
        - cell 4.3
        - cell 4.4

      * - row 5
        - cell 5.1 with automatic span to right end

      * - row 6
        - cell 6.1
        - ..


.. admonition:: List table
   :class: rst-example

   .. flat-table:: ``flat-table`` example
      :header-rows: 2
      :stub-columns: 1
      :widths: 1 1 1 1 2

      * - :rspan:`1` head / stub
        - :cspan:`3` head 1.1-4

      * - head 2.1
        - head 2.2
        - head 2.3
        - head 2.4

      * .. row body 1 / this is a comment

        - row 1
        - :rspan:`2` cell 1-3.1
        - cell 1.2
        - cell 1.3
        - cell 1.4

      * .. Comments and targets are allowed on *table-row* stage.
        .. _`row body 2`:

        - row 2
        - cell 2.2
        - :rspan:`1` :cspan:`1`
          cell 2.3 with a span over

          * col 3-4 &
          * row 2-3

      * - row 3
        - cell 3.2

      * - row 4
        - cell 4.1
        - cell 4.2
        - cell 4.3
        - cell 4.4

      * - row 5
        - cell 5.1 with automatic span to right end

      * - row 6
        - cell 6.1
        - ..


CSV table
---------

CSV table might be the choice if you want to include CSV-data from a outstanding
(build) process into your documentation.

.. code:: reST

   .. csv-table:: CSV table example
      :header: .. , Column 1, Column 2
      :widths: 2 5 5
      :stub-columns: 1
      :file: csv_table.txt

Content of file ``csv_table.txt``:

.. literalinclude:: csv_table.txt

.. admonition:: CSV table
   :class: rst-example

   .. csv-table:: CSV table example
      :header: .. , Column 1, Column 2
      :widths: 3 5 5
      :stub-columns: 1
      :file: csv_table.txt

Templating
==========

.. sidebar:: Build environment

   All *generic-doc* tasks are running in the :ref:`make install`.

Templating is suitable for documentation which is created generic at the build
time.  The sphinx-jinja_ extension evaluates jinja_ templates in the :ref:`make
install` (with SearXNG modules installed).  We use this e.g. to build chapter:
:ref:`configured engines`.  Below the jinja directive from the
:origin:`docs/admin/engines.rst` is shown:

.. literalinclude:: ../user/configured_engines.rst
   :language: reST
   :start-after: .. _configured engines:

The context for the template is selected in the line ``.. jinja:: searx``.  In
sphinx's build configuration (:origin:`docs/conf.py`) the ``searx`` context
contains the ``engines`` and ``plugins``.

.. code:: py

   import searx.search
   import searx.engines
   import searx.plugins
   searx.search.initialize()
   jinja_contexts = {
      'searx': {
         'engines': searx.engines.engines,
         'plugins': searx.plugins.plugins
      },
   }


Tabbed views
============

.. _sphinx-tabs: https://github.com/djungelorm/sphinx-tabs
.. _basic-tabs: https://github.com/djungelorm/sphinx-tabs#basic-tabs
.. _group-tabs: https://github.com/djungelorm/sphinx-tabs#group-tabs
.. _code-tabs: https://github.com/djungelorm/sphinx-tabs#code-tabs

With `sphinx-tabs`_ extension we have *tabbed views*.  To provide installation
instructions with one tab per distribution we use the `group-tabs`_ directive,
others are basic-tabs_ and code-tabs_.  Below a *group-tab* example from
:ref:`docs build` is shown:

.. literalinclude:: ../admin/buildhosts.rst
   :language: reST
   :start-after: .. SNIP sh lint requirements
   :end-before: .. SNAP sh lint requirements

.. _math:

Math equations
==============

.. _Mathematics: https://en.wikibooks.org/wiki/LaTeX/Mathematics
.. _amsmath user guide:
   http://vesta.informatik.rwth-aachen.de/ftp/pub/mirror/ctan/macros/latex/required/amsmath/amsldoc.pdf

.. sidebar:: About LaTeX

   - `amsmath user guide`_
   - Mathematics_
   - :ref:`docs build`

The input language for mathematics is LaTeX markup using the :ctan:`amsmath`
package.

To embed LaTeX markup in reST documents, use role :rst:role:`:math: <math>` for
inline and directive :rst:dir:`.. math:: <math>` for block markup.

.. code:: reST

   In :math:numref:`schroedinger general` the time-dependent Schrödinger equation
   is shown.

   .. math::
      :label: schroedinger general

       \mathrm{i}\hbar\dfrac{\partial}{\partial t} |\,\psi (t) \rangle =
             \hat{H} |\,\psi (t) \rangle.

.. admonition:: LaTeX math equation
   :class: rst-example

   In :math:numref:`schroedinger general` the time-dependent Schrödinger equation
   is shown.

   .. math::
      :label: schroedinger general

       \mathrm{i}\hbar\dfrac{\partial}{\partial t} |\,\psi (t) \rangle =
             \hat{H} |\,\psi (t) \rangle.


The next example shows the difference of ``\tfrac`` (*textstyle*) and ``\dfrac``
(*displaystyle*) used in a inline markup or another fraction.

.. code:: reST

   ``\tfrac`` **inline example** :math:`\tfrac{\tfrac{1}{x}+\tfrac{1}{y}}{y-z}`
   ``\dfrac`` **inline example** :math:`\dfrac{\dfrac{1}{x}+\dfrac{1}{y}}{y-z}`

.. admonition:: Line spacing
   :class: rst-example

   Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy
   eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
   voluptua.  ...
   ``\tfrac`` **inline example** :math:`\tfrac{\tfrac{1}{x}+\tfrac{1}{y}}{y-z}`
   At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd
   gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.

   Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy
   eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
   voluptua.  ...
   ``\tfrac`` **inline example** :math:`\dfrac{\dfrac{1}{x}+\dfrac{1}{y}}{y-z}`
   At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd
   gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.


.. _KISS: https://en.wikipedia.org/wiki/KISS_principle

.. _readability: https://docs.python-guide.org/writing/style/
.. _Sphinx-Primer:
    https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _reST: https://docutils.sourceforge.io/rst.html
.. _Sphinx Roles:
    https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html
.. _Sphinx: https://www.sphinx-doc.org
.. _`sphinx-doc FAQ`: https://www.sphinx-doc.org/en/stable/faq.html
.. _Sphinx markup constructs:
    https://www.sphinx-doc.org/en/stable/markup/index.html
.. _`sphinx cross references`:
    https://www.sphinx-doc.org/en/stable/markup/inline.html#cross-referencing-arbitrary-locations
.. _sphinx.ext.extlinks:
    https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html
.. _intersphinx: https://www.sphinx-doc.org/en/stable/ext/intersphinx.html
.. _sphinx config: https://www.sphinx-doc.org/en/stable/config.html
.. _Sphinx's autodoc: https://www.sphinx-doc.org/en/stable/ext/autodoc.html
.. _Sphinx's Python domain:
    https://www.sphinx-doc.org/en/stable/domains.html#the-python-domain
.. _Sphinx's C domain:
   https://www.sphinx-doc.org/en/stable/domains.html#cross-referencing-c-constructs
.. _doctree:
    https://www.sphinx-doc.org/en/master/extdev/tutorial.html?highlight=doctree#build-phases
.. _docutils: http://docutils.sourceforge.net/docs/index.html
.. _docutils FAQ: http://docutils.sourceforge.net/FAQ.html
.. _linuxdoc: https://return42.github.io/linuxdoc
.. _jinja: https://jinja.palletsprojects.com/
.. _sphinx-jinja: https://github.com/tardyp/sphinx-jinja
.. _SVG: https://www.w3.org/TR/SVG11/expanded-toc.html
.. _DOT: https://graphviz.gitlab.io/_pages/doc/info/lang.html
.. _`Graphviz's dot`: https://graphviz.gitlab.io/_pages/pdf/dotguide.pdf
.. _Graphviz: https://graphviz.gitlab.io
.. _ImageMagick: https://www.imagemagick.org

.. _`Emacs Table Mode`: https://www.emacswiki.org/emacs/TableMode
.. _`Online Tables Generator`: https://www.tablesgenerator.com/text_tables
.. _`OASIS XML Exchange Table Model`: https://www.oasis-open.org/specs/tm9901.html
