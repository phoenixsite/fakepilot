.. _changelog:


Changelog
=========

This document presents the changes made between releases
of ``fakepilot``.

Version 25.05.2
~~~~~~~~~~~~~~~

* Fixed extracting the review when it does not have any content. Before,
  because there is no content in the review, the content_node was not
  found and trying to access the string attribute caused a Nonetype
  exception.

Version 25.05.1
~~~~~~~~~~~~~~~

Released May 2025

* Added support for Trustpilot pages as of May 2025. The previous
  version only supports those from December 2023.

Version 25.05.0
~~~~~~~~~~~~~~~

Released May 2025

* Adopted "CalVer" YYYY.MM.MINOR.

* Added support for Python 3.13.

* Using the lxml's parser is now optional, the html.parser may be used.

* Removed everything related to fetching the HTML pages from the Trustpilot
  website. Now that must be done by the user.

* Dropped support for Python 3.7 and 3.8.
