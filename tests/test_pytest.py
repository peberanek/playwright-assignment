"""
Ukoly:
  * Pokryt minimalne testove scenare (viz README.md)
  * Jake dalsi testy bych implementoval?

Otazky:
  * Kdo jsou cilovi uzivatele? Nevim.
  * Jake jsou cilove platformy? Nevim.
  * Co pokryje nejvice?
      - desktop (Chrome, Edge)
          Playwright docs claim chromium is good enough for most testing of Chrome and Edge:
          https://playwright.dev/docs/browsers#when-to-use-google-chrome--microsoft-edge-and-when-not-to
      - mobile (Android)
"""

import logging
from datetime import datetime, timedelta

#
# test cases
#

# TODO: what about to use some autouse fixture?
future_timestamp = (
    datetime.now() + timedelta(days=30)
).timestamp()  # today + 30 days in secs
common_cookie_vals = {
    "domain": ".stream.cz",
    "path": "/",
    "expires": future_timestamp,
    "secure": True,
    "sameSite": "None",
    "httpOnly": False,
}
cookies = [
    {
        "name": "euconsent-v2",  # TCF string v2
        "value": "CPWQiJUPWQiJUD3ACBCSCHCsAP_AAEPAAATIIDoBhCokBSFCAGpYIIMAAAAHxxAAYCACABAAoAABABIAIAQAAAAQAAAgBAAAABQAIAIAAAAACEAAAAAAAAAAAQAAAAAAAAAAIQIAAAAAACBAAAAAAABAAAAAAABAQAAAggAAAAIAAAAAAAEAgAAAAAAAAAAAAAAAAAgAAAAAAAAAAAgd1AmAAWABUAC4AGQAQAAyABoADmAIgAigBMACeAFUAMQAfgBCQCIAIkARwAnABSgCxAGWAM0AdwA_QCEAEWALQAXUAwIBrAD5AJBATaAtQBeYDSgGpgO6AAAA.YAAAAAAAAAAA",
        **common_cookie_vals,
    },
    {
        "name": "cmppersisttestcookie",  # unix timestamp of first visit, yup could be 1
        "value": "1",
        **common_cookie_vals,
    },
    {
        "name": "szncmpone",  # some helper to track purpose1 consent
        "value": "1",
        **common_cookie_vals,
    },
]

# test search basic
def test_basic_search(page, context):
    """Test basic search from the Stream.cz main page.

    Test search field works.
    Test user is redirected to the page with search results.
    Test results were found and contain:
        * "Nejlepsi vysledek"
        * "Porady"
        * "Videa"
    """
    basel_url = "https://www.stream.cz/"
    term = "Kazma"
    search_field = '[placeholder="Zadejte\\, co chcete hledat"]'

    # Add cookies to prevent CMP dialog to block further actions
    context.add_cookies(cookies)

    logging.info("Opening '%s'", basel_url)
    page.goto(basel_url)

    logging.info("Searching for '%s'", term)
    page.locator(search_field).click()
    page.locator(search_field).fill(term)
    # TODO: user may click the magnifier icon as well.
    page.locator(search_field).press("Enter")

    logging.info("Waiting for redirection")
    # XXX: in headless mode this fails with timeout
    page.wait_for_url(f"{basel_url}hledani?dotaz={term}")

    # FIXME: verify results were found


# test search nonexistent term


# test empty search page


# test search from random page


# test video filtering


#
# additional tests?
#
