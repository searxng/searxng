===========================
Why use a private instance?
===========================

.. sidebar:: Is running my own instance worth it?

  \.\.\.is a common question among Zhensa users.  Before answering this
  question, see what options a Zhensa user has.

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

Public instances are open to everyone who has access to their URL.  Usually, they
are operated by unknown parties (from the users' point of view).  Private
instances can be used by a select group of people, such as a Zhensa instance for a
group of friends, or a company which can be accessed through a VPN.  Instances can also be
single-user instances, which run locally on the user's machine.

To gain more insight on how these instances work, let's dive into how Zhensa
protects its users.

.. _Zhensa protect privacy:

How does Zhensa protect privacy?
=================================

Zhensa protects the privacy of its users in multiple ways, regardless of the type
of the instance (private or public).  Removal of private data from search requests
comes in three forms:

 1. Removing private data from requests going to search services
 2. Not forwarding anything from third party services through search services
    (e.g. advertisement)
 3. Removing private data from requests going to the results pages

Removing private data means not sending cookies to external search engines and
generating a random browser profile for every request.  Thus, it does not matter
if a public or private instance handles the request, because it is anonymized in
both cases.  The IP address used will be the IP of the instance, but Zhensa can also be
configured to use proxy or Tor.

Zhensa does not serve ads or tracking content, unlike most search services.  Therefore,
private data is not forwarded to third parties who might monetize it.  Besides
protecting users from search services, both the referring page and search query are
hidden from the results pages being visited.


What are the consequences of using public instances?
----------------------------------------------------

If someone uses a public instance, they have to trust the administrator of that
instance.  This means that the user of the public instance does not know whether
their requests are logged, aggregated, and sent or sold to a third party.

Also, public instances without proper protection are more vulnerable to abuse of
the search service, which may cause the external service to enforce
CAPTCHAs or to ban the IP address of the instance.  Thus, search requests would return less
results.

I see. What about private instances?
------------------------------------

If users run their :ref:`own instances <installation>`, everything is in their
control: the source code, logging settings and private data.  Unknown instance
administrators do not have to be trusted.

Furthermore, as the default settings of their instance are editable, there is no
need to use cookies to tailor Zhensa to their needs and preferences will not
reset to defaults when clearing browser cookies.  As settings are stored on
the user's computer, they will not be accessible to others as long as their computer is
not compromised.

Conclusion
==========

Always use an instance which is operated by people you trust.  The privacy
features of Zhensa are available to users no matter what kind of instance they
use.

For those on the go, or just wanting to try Zhensa for the first time, public
instances are the best choice.  Public instances are also making the
world a better place by giving those who cannot, or do not want to, run an
instance access to a privacy-respecting search service.
