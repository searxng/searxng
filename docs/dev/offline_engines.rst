===============================
Preparation for offline engines
===============================

Offline engines
===============

To extend the functionality of searx, offline engines are going to be
introduced.  An offline engine is an engine which does not need Internet
connection to perform a search and does not use HTTP to communicate.

Offline engines can be configured as online engines, by adding those to the
`engines` list of :origin:`settings.yml <searx/settings.yml>`.  Thus, searx
finds the engine file and imports it.

Example skeleton for the new engines:

.. code:: python

   from subprocess import PIPE, Popen

   categories = ['general']
   offline = True

   def init(settings):
       pass

   def search(query, params):
       process = Popen(['ls', query], stdout=PIPE)
       return_code = process.wait()
       if return_code != 0:
           raise RuntimeError('non-zero return code', return_code)

       results = []
       line = process.stdout.readline()
       while line:
           result = parse_line(line)
           results.append(results)

           line = process.stdout.readline()

       return results


Development progress
====================

First, a proposal has been created as a Github issue.  Then it was moved to the
wiki as a design document.  You can read it here: :wiki:`Offline-engines`.

In this development step, searx core was prepared to accept and perform offline
searches.  Offline search requests are scheduled together with regular offline
requests.

As offline searches can return arbitrary results depending on the engine, the
current result templates were insufficient to present such results.  Thus, a new
template is introduced which is caplable of presenting arbitrary key value pairs
as a table. You can check out the pull request for more details see
:pull-searx:`1700`.

Next steps
==========

Today, it is possible to create/run an offline engine. However, it is going to be publicly available for everyone who knows the searx instance. So the next step is to introduce token based access for engines. This way administrators are able to limit the access to private engines.

Acknowledgement
===============

This development was sponsored by `Search and Discovery Fund`_ of `NLnet Foundation`_ .

.. _Search and Discovery Fund: https://nlnet.nl/discovery
.. _NLnet Foundation: https://nlnet.nl/


| Happy hacking.
| kvch // 2019.10.21 17:03

