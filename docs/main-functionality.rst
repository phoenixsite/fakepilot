.. _main-functionality:

Main functionality
==================

``fakepilot`` extracts the information of a company, and optionally its
reviews, from a Trustpilot company page. Everything is done through
:func:`fakepilot.extract_info`.

Getting the page
----------------

``fakepilot`` doesn't download anything from Trustpilot. You have to get the
company's page yourself, for example by opening
``https://www.trustpilot.com/review/<company-domain>`` in your browser and
saving it as HTML.

Use the English version of the site: some fields, like the date of
experience of the reviews, are parsed assuming the English format.

Extracting the information
--------------------------

Pass the saved page to :func:`fakepilot.extract_info`, either as an open file
or as a string with the HTML content. Don't pass the path of the file: it
would be parsed as if it were the HTML content.

.. code-block:: python

    import fakepilot as fp

    with open("company_page.html", encoding="utf-8") as page:
        company = fp.extract_info(page)

    print(company["name"])                 # Perfumeria Online Infragantia
    print(company["score"])                # 4.3
    print(company["nreviews"])             # 12
    print(company["categories"])           # ['Perfume Store']
    print(company["rating_distribution"])  # {1: 0.0, 2: 0.0, 3: 0.0, 4: 8.33..., 5: 91.66...}

To also extract the reviews shown on the page, set ``with_reviews`` to
``True``. ``nreviews`` is the maximum number of reviews to extract (5 by
default). A Trustpilot page shows at most 20 reviews, so if you need more,
save the following pages of reviews and extract them too.

.. code-block:: python

    with open("company_page.html", encoding="utf-8") as page:
        company = fp.extract_info(page, with_reviews=True, nreviews=20)

    for review in company["reviews"]:
        print(review["star_rating"], review["date"], review["title"])

Company's data
--------------

:func:`fakepilot.extract_info` returns a dictionary with the following keys.
Those fields that aren't shown on the page are ``None``, except
``categories``, which is an empty list.

======================== ================== ==============================================
Key                      Type               Description
======================== ================== ==============================================
``name``                 ``str``            Name of the company.
``url``                  ``str``            Website of the company, as registered in
                                            Trustpilot.
``nreviews``             ``int``            Number of reviews of the company.
``score``                ``float``          TrustScore of the company.
``categories``           ``list[str]``      Categories the company belongs to.
``email``                ``str``            Contact email.
``phone``                ``str``            Contact phone number.
``address``              ``str``            Contact address.
``is_claimed``           ``bool``           Whether the company has claimed its
                                            Trustpilot profile.
``rating_distribution``  ``dict[int,        Percentage of reviews for each number of
                         float]``           stars, from 1 to 5.
``reviews``              ``list[dict]``     Reviews of the company. Only present if
                                            ``with_reviews`` is ``True``.
======================== ================== ==============================================

Reviews' data
-------------

Each review in ``reviews`` is a dictionary with the following keys.

==================== ======================= ===========================================
Key                  Type                    Description
==================== ======================= ===========================================
``author_name``      ``str``                 Name of the author of the review.
``author_id``        ``str``                 Trustpilot's identifier of the author.
``is_verified``      ``bool``                Whether the review is verified.
``star_rating``      ``float``               Number of stars, from 1 to 5.
``date``             ``datetime.datetime``   Date and time the review was posted.
``title``            ``str``                 Title of the review.
``content``          ``str``                 Text of the review. It is an empty
                                             string if the review has no text.
``nreviews``         ``int``                 Number of reviews written by the author.
``country``          ``str``                 Country code of the author, e.g. ``ES``.
``date_experience``  ``datetime.datetime``   Date of the experience being reviewed.
==================== ======================= ===========================================

Supported pages
---------------

Trustpilot changes the layout of its pages from time to time. ``fakepilot``
supports the pages from December 2023, May 2025 and 2026. The current layout
is tried first and, if it isn't recognized, the previous ones are used.

If a page can't be parsed, it is likely that Trustpilot has changed its
layout again. Please, `open an issue <https://github.com/phoenixsite/fakepilot/issues>`_
and attach the saved page.
