"""Test cases for basic testing of stream.cz

Tasks:
    * Cover at least the test cases listed in README.md
    * What other tests would you implement?

Notes:
    * How to achieve the widest coverage with minimal effort?
        * desktop (Chrome, Edge)
            Playwright docs claim chromium is good enough for most
            testing of Chrome and Edge:
            https://playwright.dev/docs/browsers#when-to-use-google-chrome--microsoft-edge-and-when-not-to
        * mobile (Android)
    * For some reason, in headless mode Page.goto() requires
      `wait_until='networkidle'`, otherwise the user is *not* redirected to
      `https://www.stream.cz/hledani?dotaz=<searched-term>`, the URL only
      changes to `https://www.stream.cz/?dotaz=<searched-term>` and no search
      results are shown.
"""

import logging
from datetime import datetime, timedelta

import pytest
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect


@pytest.fixture(autouse=True)
def mod_context(context):
    """Provide modified context; e.g. set cookies."""
    common_cookie_vals = {
        "domain": ".stream.cz",
        "path": "/",
        "expires": (
            datetime.now() + timedelta(days=30)
        ).timestamp(),  # today + 30 days in secs
        "secure": True,
        "sameSite": "None",
        "httpOnly": False,
    }
    logging.info("Adding cookies to prevent blocking by CMP dialog")
    context.add_cookies(
        [
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
    )
    return context



#
# test cases
#


base_url = "https://www.stream.cz"
search_field = '[placeholder="Zadejte\\, co chcete hledat"]'
search_button = '[aria-label="Vyhledat"]'
search_results = (
    {"name": "Nejlepší výsledek", "content_box": "[class=search-tag-channel]"},
    {"name": "Pořady", "content_box": "[class=squircle-carousel__list]"},
    {"name": "VideaFiltry", "content_box": "[class=search-episodes__list]"},
)


def test_basic_search(page):
    """Test basic search from the Stream.cz main page.

    Test search field works.
    Test user is redirected to the page with search results.
    Test results were found and contain:
        * "Nejlepsi vysledek"
        * "Porady"
        * "Videa"
    Test results above are non-empty.
    """
    term = "Kazma"

    logging.info("Opening '%s'", base_url)
    page.goto(base_url, wait_until="networkidle")

    logging.info("Searching for '%s'", term)
    page.locator(search_field).click()
    page.locator(search_field).fill(term)
    page.locator(search_button).click()
    # TODO: user may press "Enter" as well.
    # page.locator(search_field).press("Enter")

    logging.info("Waiting for redirection")
    expect(page).to_have_url(f"{base_url}/hledani?dotaz={term}")

    logging.info("Verifying search results")
    for result in search_results:
        logging.info("Verifying '%s'", result["name"])
        expect(page.locator(f"text={result['name']}")).to_be_visible()
        expect(page.locator(result["content_box"])).to_be_visible()
        expect(page.locator(result["content_box"])).not_to_be_empty()


def test_search_for_nonexistent_term(page):
    """Test searching for a non-existent term returns no results.

    Verify user is presented with an information that no results were found.
    """
    term = "foobarterm"

    logging.info("Opening '%s'", base_url)
    page.goto(base_url, wait_until="networkidle")

    logging.info("Searching for '%s'", term)
    page.locator(search_field).click()
    page.locator(search_field).fill(term)
    page.locator(search_button).click()

    logging.info("Waiting for redirection")
    expect(page).to_have_url(f"{base_url}/hledani?dotaz={term}")

    logging.info("Verifying no results were found")
    info_msg = page.locator("text=Bohužel jsme nic nenašli")
    content = page.locator(".page-layout-content", has=info_msg)
    expect(info_msg).to_be_visible()
    expect(content).to_have_count(1)

    for result in search_results:
        logging.info("Verifying '%s' is not shown", result["name"])
        expect(page.locator(f"text={result['name']}")).not_to_be_visible()


# test empty search page
def test_empty_search_page(page):
    """Test that default search page ('/hledani') shows no results."""
    default_search_page_url = base_url + "/hledani"

    logging.info("Opening '%s'", default_search_page_url)
    page.goto(default_search_page_url, wait_until="networkidle")

    logging.info("Verifying no results are shown")
    info_msg = page.locator("text=Zadejte, co chcete hledat")
    content = page.locator(".page-layout-content", has=info_msg)
    expect(info_msg).to_be_visible()
    expect(content).to_have_count(1)

    for result in search_results:
        logging.info("Verifying '%s' is not shown", result["name"])
        expect(page.locator(f"text={result['name']}")).not_to_be_visible()


def test_search_for_videos_from_random_page(page):
    """Test searching from a random page, verify related videos are shown.

    Verify the button "Načíst další videa" loads more videos.
    """
    term = "Kazma"
    url = base_url + "/moje/odebirane"

    logging.info("Opening '%s'", url)
    page.goto(url, wait_until="networkidle")

    logging.info("Searching for '%s'", term)
    page.locator(search_field).click()
    page.locator(search_field).fill(term)
    page.locator(search_button).click()

    logging.info("Waiting for redirection")
    expect(page).to_have_url(f"{base_url}/hledani?dotaz={term}")

    # FIXME: verify non-empty results

    logging.info("Trying to load more videos")
    page.locator("text=Načíst další videa").click()

    # FIXME: verify more results is shown


# test video filtering


#
# additional tests?
#
