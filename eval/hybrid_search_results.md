# Hybrid Search Evaluation

## Q1: What functions are available in Python collections module?

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\library\collections.abc.txt`
- Section: Collections Abstract Base Classes
- Hybrid score: 0.03055
- Semantic rank: 7
- Lexical rank: 4

```text
collections module offers the following *ABCs*:
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\library\collections.txt`
- Section: "collections" --- Container datatypes
- Hybrid score: 0.01639
- Semantic rank: 1
- Lexical rank: None

```text
"collections" --- Container datatypes
*************************************

**Source code:** Lib/collections/__init__.py

======================================================================

This module implements specialized container datatypes providing
alternatives to Python's general purpose built-in containers, "dict",
"list", "set", and "tuple".
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\library\collections.abc.txt`
- Section: Collections Abstract Base Classes
- Hybrid score: 0.01639
- Semantic rank: None
- Lexical rank: 1

```text
=================================

The collections module offers the following *ABCs*:
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\library\collections.txt`
- Section: "collections" --- Container datatypes
- Hybrid score: 0.01613
- Semantic rank: 2
- Lexical rank: None

```text
Python's general purpose built-in containers, "dict",
"list", "set", and "tuple".
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\library\collections.abc.txt`
- Section: Collections Abstract Base Classes
- Hybrid score: 0.01613
- Semantic rank: None
- Lexical rank: 2

```text
The collections module offers the following *ABCs*:
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---

## Q2: What is the purpose of collections.Counter and how is it used?

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.15.txt`
- Section: collections
- Hybrid score: 0.03068
- Semantic rank: 1
- Lexical rank: 10

```text
collections
-----------

* Added "collections.Counter.__xor__()" and
  "collections.Counter.__ixor__()" to compute the symmetric difference
  between "Counter" objects. (Contributed by Raymond Hettinger in
  gh-138682.)
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\library\collections.txt`
- Section: "Counter" objects
- Hybrid score: 0.02964
- Semantic rank: 6
- Lexical rank: 9

```text
a new counter from a mapping
   >>> c = Counter(cats=4, dogs=8)             # a new counter from keyword args

   Counter objects have a dictionary interface except that they return
   a zero count for missing items instead of raising a "KeyError":

   >>> c = Counter(['eggs', 'ham'])
   >>> c['bacon']                              # count of a missing element is zero
   0

   Setting a count to zero does not remove an element from a counter.
   Use "del" to remove it entirely:

   >>> c['sausage
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\library\typing.txt`
- Section: Aliases to types in "collections"
- Hybrid score: 0.01639
- Semantic rank: None
- Lexical rank: 1

```text
Aliases to types in "collections"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class typing.DefaultDict(collections.defaultdict, MutableMapping[KT, VT])

   Deprecated alias to "collections.defaultdict".

   Added in version 3.5.2.

   Deprecated since version 3.9: "collections.defaultdict" now
   supports subscripting ("[]"). See **PEP 585** and Generic Alias
   Type.

class typing.OrderedDict(collections.OrderedDict, MutableMapping[KT, VT])

   Deprecated alias to "collections.OrderedDict".

   Added in
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\library\collections.txt`
- Section: "Counter" objects
- Hybrid score: 0.01613
- Semantic rank: 2
- Lexical rank: None

```text
d                      # inclusion:  c[x] <= d[x]
   False

Unary addition and subtraction are shortcuts for adding an empty
counter or subtracting from an empty counter.

>>> c = Counter(a=2, b=-4)
>>> +c
Counter({'a': 2})
>>> -c
Counter({'b': 4})

Added in version 3.3: Added support for unary plus, unary minus, and
in-place multiset operations.

Added in version 3.15: Added support for the symmetric difference
multiset operation, "c ^ d".

Note:

  Counters were primarily designed to work with
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\library\collections.txt`
- Section: "Counter" objects
- Hybrid score: 0.01613
- Semantic rank: None
- Lexical rank: 2

```text
"Counter" objects
=================

A counter tool is provided to support convenient and rapid tallies.
For example:

   >>> # Tally occurrences of words in a list
   >>> cnt = Counter()
   >>> for word in ['red', 'blue', 'red', 'green', 'blue', 'blue']:
   ...     cnt[word] += 1
   ...
   >>> cnt
   Counter({'blue': 3, 'red': 2, 'green': 1})

   >>> # Find the ten most common words in Hamlet
   >>> import re
   >>> words = re.findall(r'\w+', open('hamlet.txt').read().lower())
   >>> Counter(wo
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---

## Q3: What is the signature of pathlib.Path.read_text?

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\library\pathlib.txt`
- Section: Reading and writing files
- Hybrid score: 0.03175
- Semantic rank: 4
- Lexical rank: 2

```text
Reading and writing files
-------------------------

Path.open(mode='r', buffering=-1, encoding=None, errors=None, newline=None)

   Open the file pointed to by the path, like the built-in "open()"
   function does:

      >>> p = Path('setup.py')
      >>> with p.open() as f:
      ...     f.readline()
      ...
      '#!/usr/bin/env python3\n'

Path.read_text(encoding=None, errors=None, newline=None)

   Return the decoded contents of the pointed-to file as a string:

      >>> p = Path('my_te
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.9.txt`
- Section: pathlib
- Hybrid score: 0.03110
- Semantic rank: 1
- Lexical rank: 8

```text
pathlib
-------

Added "pathlib.Path.readlink()" which acts similarly to
"os.readlink()". (Contributed by Girts Folkmanis in bpo-30618)
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.5.txt`
- Section: pathlib
- Hybrid score: 0.01639
- Semantic rank: None
- Lexical rank: 1

```text
pathlib
-------

The new "Path.samefile()" method can be used to check whether the path
points to the same file as another path, which can be either another
"Path" object, or a string:

   >>> import pathlib
   >>> p1 = pathlib.Path('/etc/hosts')
   >>> p2 = pathlib.Path('/etc/../etc/hosts')
   >>> p1.samefile(p2)
   True

(Contributed by Vajrasky Kok and Antoine Pitrou in bpo-19775.)

The "Path.mkdir()" method now accepts a new optional *exist_ok*
argument to match "mkdir -p" and "os.makedirs()
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.8.txt`
- Section: pathlib
- Hybrid score: 0.01613
- Semantic rank: 2
- Lexical rank: None

```text
pathlib
-------

"pathlib.Path" methods that return a boolean result like "exists()",
"is_dir()", "is_file()", "is_mount()", "is_symlink()",
"is_block_device()", "is_char_device()", "is_fifo()", "is_socket()"
now return "False" instead of raising "ValueError" or its subclass
"UnicodeEncodeError" for paths that contain characters unrepresentable
at the OS level. (Contributed by Serhiy Storchaka in bpo-33721.)

Added "pathlib.Path.link_to()" which creates a hard link pointing to a
path. (Contribut
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\library\importlib.resources.txt`
- Section: Functional API
- Hybrid score: 0.01587
- Semantic rank: 3
- Lexical rank: None

```text
Changed in version 3.13: Multiple *path_names* are accepted.

importlib.resources.open_text(anchor, *path_names, encoding='utf-8', errors='strict')

   Open the named resource for text reading. By default, the contents
   are read as strict UTF-8.

   See the introduction for details on *anchor* and *path_names*.
   *encoding* and *errors* have the same meaning as in built-in
   "open()".

   For backward compatibility reasons, the *encoding* argument must be
   given explicitly if there are mul
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---

## Q4: How does itertools.combinations work and what arguments does it accept?

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\howto\functional.txt`
- Section: Combinatoric functions
- Hybrid score: 0.03154
- Semantic rank: 6
- Lexical rank: 1

```text
Combinatoric functions
----------------------

The "itertools.combinations(iterable, r)" returns an iterator giving
all possible *r*-tuple combinations of the elements contained in
*iterable*.

   itertools.combinations([1, 2, 3, 4, 5], 2) =>
     (1, 2), (1, 3), (1, 4), (1, 5),
     (2, 3), (2, 4), (2, 5),
     (3, 4), (3, 5),
     (4, 5)

   itertools.combinations([1, 2, 3, 4, 5], 3) =>
     (1, 2, 3), (1, 2, 4), (1, 2, 5), (1, 3, 4), (1, 3, 5), (1, 4, 5),
     (2, 3, 4), (2, 3, 5), (2, 4, 5),
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\library\itertools.txt`
- Section: Itertool Functions
- Hybrid score: 0.03101
- Semantic rank: 5
- Lexical rank: 4

```text
single iterable argument that is evaluated lazily.  Roughly
   equivalent to:

      def from_iterable(iterables):
          # chain.from_iterable(['ABC', 'DEF']) → A B C D E F
          for iterable in iterables:
              yield from iterable

   Note that unpacking in comprehensions provides similar
   functionality so that "list(chain.from_iterable(iterables))" could
   be written as "[*s for s in iterables]".

itertools.combinations(iterable, r)

   Return *r* length subsequences of elem
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\2.6.txt`
- Section: New and Improved Modules
- Hybrid score: 0.03083
- Semantic rank: 8
- Lexical rank: 2

```text
4, 2, 3), (1, 4, 2, 4),
      (2, 3, 1, 3), (2, 3, 1, 4), (2, 3, 2, 3), (2, 3, 2, 4),
      (2, 4, 1, 3), (2, 4, 1, 4), (2, 4, 2, 3), (2, 4, 2, 4)]

  "combinations(iterable, r)" returns sub-sequences of length *r* from
  the elements of *iterable*.

     >>> list(itertools.combinations('123', 2))
     [('1', '2'), ('1', '3'), ('2', '3')]
     >>> list(itertools.combinations('123', 3))
     [('1', '2', '3')]
     >>> list(itertools.combinations('1234', 3))
     [('1', '2', '3'), ('1', '2', '4'),
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\2.7.txt`
- Section: New and Improved Modules
- Hybrid score: 0.03031
- Semantic rank: 7
- Lexical rank: 5

```text
2) =>
       ('a', 'a'), ('a', 'b'), ('a', 'c'),
       ('b', 'b'), ('b', 'c'), ('c', 'c')

  Note that elements are treated as unique depending on their position
  in the input, not their actual values.

  The "itertools.count()" function now has a *step* argument that
  allows incrementing by values other than 1.  "count()" also now
  allows keyword arguments, and using non-integer values such as
  floats or "Decimal" instances.  (Implemented by Raymond Hettinger;
  bpo-5032.)

  "itertools.co
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\library\tarfile.txt`
- Section: "tarfile" --- Read and write tar archive files
- Hybrid score: 0.02899
- Semantic rank: 10
- Lexical rank: 8

```text
combinations:
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---

## Q5: Which Python version introduced functools.cache and how does it differ from lru_cache?

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\library\functools.txt`
- Section: "functools" --- Higher-order functions and operations on callable objects
- Hybrid score: 0.03105
- Semantic rank: 7
- Lexical rank: 2

```text
# locale-aware sort order

   For sorting examples and a brief sorting tutorial, see Sorting
   Techniques.

   Added in version 3.2.

@functools.lru_cache(user_function)
@functools.lru_cache(maxsize=128, typed=False)

   Decorator to wrap a function with a memoizing callable that saves
   up to the *maxsize* most recent calls.  It can save time when an
   expensive or I/O bound function is periodically called with the
   same arguments.

   The cache is threadsafe so that the wrapped function c
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\library\functools.txt`
- Section: "functools" --- Higher-order functions and operations on callable objects
- Hybrid score: 0.03068
- Semantic rank: 10
- Lexical rank: 1

```text
"functools" --- Higher-order functions and operations on callable objects
*************************************************************************

**Source code:** Lib/functools.py

======================================================================

The "functools" module is for higher-order functions: functions that
act on or return other functions. In general, any callable object can
be treated as a function for the purposes of this module.

The "functools" module defines the following f
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\library\functools.txt`
- Section: "functools" --- Higher-order functions and operations on callable objects
- Hybrid score: 0.03058
- Semantic rank: 8
- Lexical rank: 3

```text
or invalidating the cache.

   The original underlying function is accessible through the
   "__wrapped__" attribute.  This is useful for introspection, for
   bypassing the cache, or for rewrapping the function with a
   different cache.

   The cache keeps references to the arguments and return values until
   they age out of the cache or until the cache is cleared.

   If a method is cached, the "self" instance argument is included in
   the cache.  See How do I cache method calls?

   An LRU
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.8.txt`
- Section: functools
- Hybrid score: 0.03031
- Semantic rank: 5
- Lexical rank: 7

```text
functools
---------

"@functools.lru_cache" can now be used as a straight decorator rather
than as a function returning a decorator.  So both of these are now
supported:

   @lru_cache
   def f(x):
       ...

   @lru_cache(maxsize=256)
   def f(x):
       ...

(Contributed by Raymond Hettinger in bpo-36772.)

Added a new "@functools.cached_property" decorator, for computed
properties cached for the life of the instance.

   import functools
   import statistics

   class Dataset:
      def __in
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.5.txt`
- Section: functools
- Hybrid score: 0.01639
- Semantic rank: 1
- Lexical rank: None

```text
functools
---------

Most of the "@~functools.lru_cache" machinery is now implemented in C,
making it significantly faster.  (Contributed by Matt Joiner, Alexey
Kachayev, and Serhiy Storchaka in bpo-14373.)
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---

## Q6: What are all the pathlib changes in Python 3.15 release notes?

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.15.txt`
- Section: What's new in Python 3.15
- Hybrid score: 0.03068
- Semantic rank: 1
- Lexical rank: 10

```text
What's new in Python 3.15
*************************

Editor:
   Hugo van Kemenade

This article explains the new features in Python 3.15, compared to
3.14. Python 3.15 was released on 9 October 2026. For full details,
see the changelog.

See also: **PEP 790** -- Python 3.15 release schedule
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.5.txt`
- Section: Notable changes in Python 3.5.4
- Hybrid score: 0.03009
- Semantic rank: 8
- Lexical rank: 5

```text
Notable changes in Python 3.5.4
===============================
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\changelog.txt`
- Section: Python 3.15.0 release candidate 3
- Hybrid score: 0.01639
- Semantic rank: None
- Lexical rank: 1

```text
Python 3.15.0 release candidate 3
=================================

*Release date: 2026-10-02*
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\changelog.txt`
- Section: Python 3.15.0 final
- Hybrid score: 0.01613
- Semantic rank: 2
- Lexical rank: None

```text
Python 3.15.0 final
===================

*Release date: 2026-10-09*

There were no new changes in version 3.15.0.
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\library\subprocess.txt`
- Section: Notes
- Hybrid score: 0.01613
- Semantic rank: None
- Lexical rank: 2

```text
Notes
=====
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---

## Q7: Is datetime.datetime.strptime deprecated and what do the official docs say?

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.14.txt`
- Section: datetime
- Hybrid score: 0.03089
- Semantic rank: 1
- Lexical rank: 9

```text
datetime
--------

* Add the "strptime()" method to the "datetime.date" and
  "datetime.time" classes. (Contributed by Wannes Boeykens in
  gh-41431.)
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.14.txt`
- Section: Deprecated
- Hybrid score: 0.01639
- Semantic rank: None
- Lexical rank: 1

```text
Deprecated
==========
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\library\datetime.txt`
- Section: Technical detail
- Hybrid score: 0.01613
- Semantic rank: 2
- Lexical rank: None

```text
Deprecated since version 3.15, will be removed in version 3.17:
  "strptime()" calls using a format string containing "%e" without a
  year now emit a "DeprecationWarning".

-[ Footnotes ]-

[1] If, that is, we ignore the effects of relativity.

[2] This matches the definition of the "proleptic Gregorian" calendar
    in Dershowitz and Reingold's book *Calendrical Calculations*,
    where it's the base calendar for all computations. See the book
    for algorithms for converting between prolepti
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.15.txt`
- Section: Deprecated
- Hybrid score: 0.01613
- Semantic rank: None
- Lexical rank: 2

```text
Deprecated
==========
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\library\time.txt`
- Section: Functions
- Hybrid score: 0.01587
- Semantic rank: 3
- Lexical rank: None

```text
platform it can sometimes
   offer more directives than those listed.  But "strptime()" is
   independent of any platform and thus does not necessarily support
   all directives available that are not documented as supported.

class time.struct_time

   The type of the time value sequence returned by "gmtime()",
   "localtime()", and "strptime()".  It is an object with a *named
   tuple* interface: values can be accessed by index and by attribute
   name.  The following values are present:
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---

## Q8: Show the official documentation for json.dumps.

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\tutorial\inputoutput.txt`
- Section: 7.2.2. Saving structured data with "json"
- Hybrid score: 0.03154
- Semantic rank: 1
- Lexical rank: 6

```text
>>> json.dumps(x)
   '[1, "simple", "list"]'

Another variant of the "dumps()" function, called "dump()", simply
serializes the object to a *text file*.  So if "f" is a *text file*
object opened for writing, we can do this:

   json.dump(x, f)

To decode the object again, if "f" is a *binary file* or *text file*
object which has been opened for reading:

   x = json.load(f)

Note:

  JSON files must be encoded in UTF-8, the default encoding for *text
  files*.

This simple serialization techniqu
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\changelog.txt`
- Section: Library
- Hybrid score: 0.03110
- Semantic rank: 8
- Lexical rank: 1

```text
Library
-------

* gh-95382: Improve performance of "json.dumps()" and "json.dump()"
  when using the argument *indent*. Depending on the data the encoding
  using "json.dumps()" with *indent* can be up to 2 to 3 times faster.
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\library\json.txt`
- Section: Command-line interface
- Hybrid score: 0.01613
- Semantic rank: 2
- Lexical rank: None

```text
Command-line interface
======================

**Source code:** Lib/json/tool.py

======================================================================

The "json" module can be invoked as a script via "python -m json" to
validate and pretty-print JSON objects. The "json.tool" submodule
implements this interface.

If the optional "infile" and "outfile" arguments are not specified,
"sys.stdin" and "sys.stdout" will be used respectively:

   $ echo '{"json": "obj"}' | python -m json
   {
       "
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\library\json.txt`
- Section: "json" --- JSON encoder and decoder
- Hybrid score: 0.01613
- Semantic rank: None
- Lexical rank: 2

```text
"json" --- JSON encoder and decoder
***********************************

**Source code:** Lib/json/__init__.py

======================================================================

JSON (JavaScript Object Notation), specified by **RFC 7159** (which
obsoletes **RFC 4627**) and by ECMA-404, is a lightweight data
interchange format inspired by JavaScript object literal syntax
(although it is not a strict subset of JavaScript [1] ).

Note:

  The term "object" in the context of JSON processing in
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\library\pprint.txt`
- Section: Example
- Hybrid score: 0.01587
- Semantic rank: 3
- Lexical rank: None

```text
'version': '1.2.0'}

Lastly, we can format like pretty-printed JSON with the *expand*
parameter. Best results are achieved with a higher *indent* value:
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---

## Q9: Which modules in the dataset contain file-handling functions?

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\contents.txt`
- Section: Python Documentation contents
- Hybrid score: 0.01639
- Semantic rank: 1
- Lexical rank: None

```text
functions and variables

    * "glob" --- Unix style pathname pattern expansion

      * Examples

    * "fnmatch" --- Unix filename pattern matching

    * "linecache" --- Random access to text lines

    * "shutil" --- High-level file operations

      * Directory and files operations

        * Platform-dependent efficient copy operations

        * copytree example

        * rmtree example

      * Archiving operations

        * Archiving example

        * Archiving example with *base_dir
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\faq\programming.txt`
- Section: Modules
- Hybrid score: 0.01639
- Semantic rank: None
- Lexical rank: 1

```text
Modules
=======
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\library\filesys.txt`
- Section: File and Directory Access
- Hybrid score: 0.01613
- Semantic rank: 2
- Lexical rank: None

```text
File and Directory Access
*************************

The modules described in this chapter deal with disk files and
directories.  For example, there are modules for reading the
properties of files, manipulating paths in a portable way, and
creating temporary files.  The full list of modules in this chapter
is:

* "pathlib" --- Object-oriented filesystem paths

  * Basic use

  * Exceptions

  * Pure paths

    * General properties

    * Operators

    * Accessing individual parts

    * Methods
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\using\configure.txt`
- Section: 3.1.1. Requirements for optional modules
- Hybrid score: 0.01613
- Semantic rank: None
- Lexical rank: 2

```text
modules are:
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\contents.txt`
- Section: Python Documentation contents
- Hybrid score: 0.01587
- Semantic rank: 3
- Lexical rank: None

```text
* Approximating binomial distributions

        * Naive bayesian classifier

  * Functional Programming Modules

    * "itertools" --- Functions creating iterators for efficient
      looping

      * Itertool Functions

      * Itertools Recipes

    * "functools" --- Higher-order functions and operations on
      callable objects

      * "partial" Objects

    * "operator" --- Standard operators as functions

      * Mapping Operators to Functions

      * In-place Operators

  * File and Dir
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---

## Q10: Where can I find regex-related functions in the Python documentation?

### Rank 1
- Source: `data\raw\extracted\python-3.15-docs-text\howto\regex.txt`
- Section: Abstract
- Hybrid score: 0.01639
- Semantic rank: 1
- Lexical rank: None

```text
Abstract
^^^^^^^^

This document is an introductory tutorial to using regular expressions
in Python with the "re" module.  It provides a gentler introduction
than the corresponding section in the Library Reference.
```

### Rank 2
- Source: `data\raw\extracted\python-3.15-docs-text\library\socket.txt`
- Section: Functions
- Hybrid score: 0.01639
- Semantic rank: None
- Lexical rank: 1

```text
Functions
---------
```

### Rank 3
- Source: `data\raw\extracted\python-3.15-docs-text\howto\regex.txt`
- Section: Using regular expressions
- Hybrid score: 0.01613
- Semantic rank: 2
- Lexical rank: None

```text
Using regular expressions
=========================

Now that we've looked at some simple regular expressions, how do we
actually use them in Python?  The "re" module provides an interface to
the regular expression engine, allowing you to compile REs into
objects and then perform matches with them.
```

### Rank 4
- Source: `data\raw\extracted\python-3.15-docs-text\builtins\functions.txt`
- Section: Built-in functions
- Hybrid score: 0.01613
- Semantic rank: None
- Lexical rank: 2

```text
functions
******************

The Python interpreter has a number of functions and types built into
it that are always available.  They are listed here in alphabetical
order.
```

### Rank 5
- Source: `data\raw\extracted\python-3.15-docs-text\whatsnew\3.15.txt`
- Section: re
- Hybrid score: 0.01587
- Semantic rank: 3
- Lexical rank: None

```text
re
--

* "re.prefixmatch()" and a corresponding "re.Pattern.prefixmatch()"
  have been added as alternate, more explicit names for the existing
  and now *soft deprecated* "re.match()" and "re.Pattern.match()"
  APIs. These are intended to be used to alleviate confusion around
  what *match* means by following the Zen of Python's *"Explicit is
  better than implicit"* mantra. Most other language regular
  expression libraries use an API named *match* to mean what Python
  has always called *sear
```

- [ ] Relevant result found?
- [ ] Correct source and section?
- [ ] Sufficient context to answer?

---
