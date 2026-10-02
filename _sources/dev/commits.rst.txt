.. _create commit:

===============================
Git Commits & Change Management
===============================

.. sidebar:: Create good commits!

   - `Conventional Commits`_
   - `Structural split of changes`_
   - `Git Commit Good Practice`_

A commit and its commit message are among the most important information
available to a developer for bug fixing and further development.  A commit is a
change and changes have a context (a change request).

In a SCM system (git), the change history is derived from the commit history. A
commit message is therefore part of the documentation for change management and
thus elementary for the traceability of changes.

**What a commit is not**: *A commit to an SCM system is not used to save files!*

A commit should always have a context and the commit message describes what is
to be changed in that context, just as a function description should describe
what the intention and the goal of the function is, a commit message should
describe what the intention and the goal of that commit is.

The commit messages form the history and are the first and therefore most
important information a developer has when he has to research when and why a
change had to be made and how it was made (what the goal was).

Like any text, a commit message should be written for the reader and not from
the perspective of the author.

When scrolling through the history, the first thing one see is the title of the
commit message. Therefore the title should describe the change as briefly and
precisely as possible ... followed by a blank line and then a somewhat detailed
description of the change.

----

The follwing rules should be in mind, when creating a commit:

- **Commit history should be read like a history book.**
- **Commit messages are for the reader not for the author of the commit.**
- **A commit is the atomic code-modification of a change in change management.**
- **Think about which descriptions from your PR might belong in the commit message.**
- **The maximum line length in a commit message is 80 characters.**

----

Choose meaningful commit messages:

  .. code::

     [type] optional scope: description

     [body]

     [optional trailers]

``[type]``:
  Commits MUST be prefixed with a type .. ``feat``, ``fix``, ``refactor``,
  ``mod``, ``upd``, ``doc``, ``l10n``, ``build`` ..

``[body]``
  `Information in commit messages`_

``[optional trailers]``:
  - `Signed-off-by`_: certify that the committer has the rights to submit the
    work under the project’s license.  That the developer has this right is a
    prerequisite for a merge.  If the `Signed-off-by`_ is not set in the
    commit, the contributor enters his `Developer's Certificate of Origin` at
    the latest when creating a PR!
  - Closes: Link to the bug report or the bug number (e.g. ``Closes: #10``)
  - `Co-authored-by`_: email address of the co-author
  - Reported-by: email address (if there is no bug report)
  - Suggested-by: email address (if there is no bug report)

----

To give examples at hand, here are a few commits.  Follow the links to see the
full commit messages:

:patch:`44d941c93`
  ``[fix] mojeek web engine: don't add empty fmt argument for web searches``

:patch:`feb15e387`
   ``[fix] brave.news engine: response is HTML and no longer JSON``

:patch:`bdfe1c2a1`
   ``[mod] engines: migration of the individual cache solutions to EngineCache``


.. _Conventional Commits:
    https://www.conventionalcommits.org/
.. _Structural split of changes:
    https://wiki.openstack.org/wiki/GitCommitMessages#Structural_split_of_changes
.. _Git Commit Good Practice:
    https://wiki.openstack.org/wiki/GitCommitMessages
.. _Information in commit messages:
    https://wiki.openstack.org/wiki/GitCommitMessages#Information_in_commit_messages
.. _`Developer's Certificate of Origin`:
    https://developercertificate.org/
.. _Signed-off-by:
    https://git-scm.com/docs/git-commit#Documentation/git-commit.txt-code--signoffcode
.. _Co-authored-by:
    https://docs.github.com/en/pull-requests/committing-changes-to-your-project/creating-and-editing-commits/creating-a-commit-with-multiple-authors
