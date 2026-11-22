.. _changelog:


Changelog
=========

This document presents the changes made between releases
of ``fakepilot``.

Version 2026.11.0
~~~~~~~~~~~~~~~~~

Released November 2026

* Added support for Trustpilot pages as of 2026. Pages with the previous
  layouts are still supported.

* Fixed extracting ``url``, which was always an empty string. It is the
  domain that identifies the company in Trustpilot, e.g.
  ``www.burgerking.dk``.

* Fixed extracting the categories in which the company is ranked. Before,
  ``None`` was returned for each of them.

* Fixed extracting phone numbers written with parentheses or spaces, like
  ``(855) 470-1527``. Before, they were extracted as the address.

* ``rating_distribution`` is now ``None`` when the page doesn't show the
  rating distribution. Before, a dictionary whose values were all ``None``
  was returned.

* ``extract_info`` no longer hides unexpected errors when parsing a page.

* Fixed extracting the review when it does not have any content. Before,
  because there is no content in the review, the content_node was not
  found and trying to access the string attribute caused a Nonetype
  exception.

* Dropped support for Python 3.7.

* Release tags no longer have the ``v`` prefix and match the package
  version, e.g. ``2026.11.0``.

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
