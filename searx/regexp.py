# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations for efficient processing of regular expressions"""

from __future__ import annotations
from typing import Iterator
import abc
import re
import warnings
import json

class RegExprList(abc.ABC):
    """Abstract base class for efficient processing of lists of regular
    expressions.  The inheriting classes have to implement the
    :py:obj:`RegExprList.load_regexp` method which is used to load the list of
    regular expressions from a configuration, for example.

    Intention: By concatenating the regular expressions from the list into one
    regular expression, all patterns can be performed with just one search and
    it is not necessary to iterate over the individual expressions and perform
    n-searches.

    """

    RE_GRP_PREFIX = "RegExprList"

    @abc.abstractmethod
    def load_regexps(self) -> list[tuple[str, tuple]]:
        """Abstract method to load the list of regular expressions from a
        configuration.  Returns a list of regular expressions (str) or a list of
        two-digit tuples with a regular expression on its first position and
        tuple of *n-objects* related to this regular expression on its second
        position:

        .. code:: python

            [
              ( <regexpr_a>, (obj_a1, obj_a2, ..) ),
              ( <regexpr_b>, (obj_b1, obj_b2, ..) ),
              ..
            ]

        If there is nothing related to the regular expression, the tuple is
        empty (n=0).  The **objects** must be of a simple data type (str, int,
        ..) so that they can be serialized (JSON).

        """

    def __init__(self, chunk_size = 1000):
        self.chunk_size = chunk_size
        self._chunks = None
        self._data_json = None

    def _get_data(self):
        if self._data_json is not None:
            return json.loads(self._data_json)
        return self.load_regexps()

    @property
    def JSON(self):
        """JSON representation of the regular expression list (see
        :py:obj:`RegExprList.load_regexp`).

        Serialize the :py:obj:`RegExprList` object into a JSON string.

        """
        if self._data_json is not None:
            return self._data_json
        return json.dumps(self._get_data(), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> "RegExprList":
        """Build a :py:obj:`RegExprList` object and load regular expressions from
        a JSON string (compare :py:obj:`RegExprList.JSON`)."""
        obj = cls()
        obj._data_json = json_str
        return obj

    @property
    def chunks(self) -> list[tuple[re.Pattern, list[tuple]]]:
        """A list of (concatenated) regular expressions"""
        if self._chunks is None:
            self._chunks = self.get_chunks()
        return self._chunks

    def get_chunks(self) -> list[tuple[re.Pattern, list[tuple]]]:
        """Returns a list chunks items.  A chunk item is a two-digit tuple with
        the concatened :py:obj:`re.Pattern` on its first position and a list of
        tuples (aka grp_tuples) on its second position.

        The regular expressions are placed in *named groups* and the group for
        the match can be determined using :py:obj:`re.Match.groupdict:`.

        .. code: re

           (?P<{_0}>foo)|(?P<_1>bar)

        .. code: python

           >>> grp_tuples[0]
           ('foo', obj_foo_1, obj_foo_2, ...)
           >>> grp_tuples[1]
           ('bar', obj_bar_1, obj_bar_1, ...)

        """
        chunks = []
        re_list = self._get_data()

        chunk_re = ""
        grp_tuples = []
        c = -1


        for pos in range(0, len(re_list)):
            c += 1
            objs_tpl = ()
            if len(re_list[pos]) == 2:
                re_str, objs_tpl = re_list[pos]
            else:
                re_str = re_list[pos]

            grp_re = f"|(?P<{self.RE_GRP_PREFIX}_{c}>{re_str})"

            if len(grp_re) + len(chunk_re) > self.chunk_size:
                # remove the leading | from chunk_re
                chunks.append((re.compile(chunk_re[1:]), grp_tuples))
                chunk_re = ""
                grp_tuples = []

            chunk_re += grp_re
            grp_tuples.append((re_str, ) + objs_tpl)

        # Are there any leftovers from the for loop?
        if chunk_re:
            chunks.append((re.compile(chunk_re[1:]), grp_tuples))
        return chunks


    def search(self, string: str) -> tuple[re.Match, tuple] | None:
        """Search for regular expressions in ``string``.  If none of the regular
        expression matches, ``None`` is returned.  If there is a match, the
        first match (:py:obj:`re.Match`) is returned along with a tuple of
        objects related to the matched pattern (compare :py:obj:`RegExprList`):

        .. code:: python

           ( re.Match, ( <regexpr_str>, obj_1, obj_2, ..) )

        """
        pos = -1
        for regexp, objs_tpl in self.chunks:
            m = regexp.search(string)
            if m:
                prefix = f"{self.RE_GRP_PREFIX}_"
                for grp_name, val in m.groupdict().items():
                    if not grp_name.startswith(prefix):
                        continue
                    if val is None:
                        continue
                    try:
                        pos = int(grp_name[len(prefix):])
                        return (m, objs_tpl[pos])

                    except ValueError:
                        # This case should never occur unless there is something
                        # wrong with the regular expressions.
                        warnings.warn(f"ignoring group '{grp_name}' in regexpr match {m}: check your regular expressions!")
                        m = None
                        break
        return None


    def finditer(self, string: str) -> Iterator[tuple[re.Match, tuple]]:
        """Return an iterator yielding over all *"non-overlapping"* matches for
        the RE pattern in string.  Similar to :py:obj:`RegExpr.search` each
        match (:py:obj:`re.Match`) comes along with a tuple of objects related
        to the matched pattern:

        .. code:: python

           ( re.Match, ( <regexpr_str>, obj_1, obj_2, ..) )

        Since the list of regular expressions is concatenated and also broken up
        at the boundaries of the chunks, it is not possible to ensure
        *"non-overlapping"* over the entirety of all regular expressions in the
        list!  Nevertheless, there will be scenarios where this iterator makes
        sense, e.g. if the regular expressions do not overlap.

        .. caution:

           Use this method with care if the :py:obj:`regular expressions in the
           list <RegExprListload_regexps>` *overlap*, otherwise you get unexpected
           results!

        """

        pos = -1
        for regexp, objs_tpl in self.chunks:
            for m in regexp.finditer(string):
                if m is None:
                    continue
                prefix = f"{self.RE_GRP_PREFIX}_"
                for grp_name, val in m.groupdict().items():
                    if not grp_name.startswith(prefix):
                        continue
                    if val is None:
                        continue
                    try:
                        pos = int(grp_name[len(prefix):])
                        yield (m, objs_tpl[pos])

                    except ValueError:
                        # This case should never occur unless there is something
                        # wrong with the regular expressions.
                        warnings.warn(f"ignoring group '{grp_name}' in regexpr match {m}: check your regular expressions!")
                        continue


##########################################################################
## some tests of the POC above


import pdb

def test_POC():
    test_list = [
        # hint: the order of the list counts!
        (r'aa', ("double 'a' don't overlaps with any other regular expressions",)),
        (r'a', ("single 'a' overlaps with all other regular expressions",)),
        r'(.*\.)?academiapublishing\.org$',
        r'(.*\.)?academiaresearch\.org$',
        r'(.*\.)?academiascholarlyjournal\.org$',
        r'(.*\.)?academicjournalsinc\.com$',
        r'(.*\.)?academicjournalsonline\.co\.in$',
        r'(.*\.)?academicjournals\.org$',
        r'(.*\.)?academicoasis\.org$',
        r'(.*\.)?academic-publishing-house\.com$',
        r'(.*\.)?academicpub\.org$',
        r'(.*\.)?academicresearchjournals\.org$',
        r'(.*\.)?academicstar\.us$',
        r'(.*\.)?academicsworld\.org$',
        r'(.*\.)?academicwebpublishers\.org$',
        r'(.*\.)?academievoorcontinuverbeteren\.nl$',
        (r'(.*\.)?academyirmbr\.com$', ("XX", "YYYY", 7, 8.2)),
        r'(.*\.)?academyjournals\.net$',
        r'(.*\.)?academyofideas\.com$',
        r'(.*\.)?academypublish\.org$'
    ]

    class TestCls(RegExprList):
        def load_regexps(self) -> list[tuple[str, tuple]] | list[str]:
            return test_list
    mylist = TestCls()
    string = "aa.www.academyirmbr.com"
    print(f"matches in '{string}' ...")
    for m, tpl in mylist.finditer(string):
        print(f"  regexp: {tpl[0]} // match: {m.string[m.start():m.end()]} // objects related to regexp: {tpl}")

if __name__ == "__main__":
    test_POC()
