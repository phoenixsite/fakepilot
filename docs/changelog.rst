.. _changelog:


Changelog
=========

This document presents the changes made between releases
of ``fakepilot``.

Version 25.05.0
~~~~~~~~~~~~~~~

Released April 2025

* Adopted "CalVer" YYYY.MM.MINOR.

* Added support for Python 3.13.

* Using the lxml's parser is now optional, the html.parser may be used.

* Removed everything related to fetching the HTML pages from the Trustpilot
  website. Now that must be done by the user.

* Dropped support for Python 3.7 and 3.8.
