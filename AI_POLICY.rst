.. SPDX-License-Identifier: AGPL-3.0-or-later

AI Policy
=========

Restrictions on Generative AI Usage
-----------------------------------
- **All AI usage in any form must be disclosed.** You must state the tool you used (e.g. Claude Code, Cursor, Amp) along with the extent that the work was AI-assisted.
- **The human-in-the-loop must fully understand all code.** If you use generative AI tools as an aid in developing code or documentation changes, ensure that you fully understand the proposed changes and can explain why they are the correct approach.
- **AI should never be the main author of the PR.** AI may be used as a tool to help with developing, but the human contribution to the code changes should always be reasonably larger than the part written by AI. For example, you should be the one that decides about the structure of the PR, not the LLM.
- **Issues and PR descriptions must be fully human-written.** Do not post output from Large Language Models or similar generative AI as comments on any of our discussion forums (e.g. GitHub Issues, Matrix, ...), as such comments tend to be formulaic and low content. If you're a not a native English speaker, using AI for translating self-written issue texts to English is okay, but please keep the wording as close as possible to the original wording.
- **Bad AI drivers will be denounced.** People who produce bad contributions that are clearly AI (slop) will be blocked for all future contributions.

There are Humans Here
---------------------
Every discussion, issue, and pull request is read and reviewed by humans. It is a boundary point at which people interact with each other and the work done. It is rude and disrespectful to approach this boundary with low-effort, unqualified work, since it puts the burden of validation on the maintainer.

It takes a lot of maintainer time and energy to review AI-generated contributions! Sending the output of an LLM to open source project maintainers extracts work from them in the form of design and code review, so we call this kind of contribution an "extractive contribution".

The *golden rule* is that a contribution should be worth more to the project than the time it takes to review it, which is usually not the case if large parts of your PR were written by LLMs.
