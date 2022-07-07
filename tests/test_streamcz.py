"""Sample tests of stream.cz search functionality

Tests cover test cases listed in README.md. Running `make tests` in the root dir
runs tests simulating desktop (Chromium) and mobile (Android: Pixel 2). I belive
that should cover most of the users as Chromium/Chrome/Edge and Android should have
the biggest market share. See e.g.
https://gs.statcounter.com/browser-market-share
https://gs.statcounter.com/os-market-share/mobile/worldwide
https://playwright.dev/docs/browsers#when-to-use-google-chrome--microsoft-edge-and-when-not-to

More browsers and devices (e.g. WebKit or iPhones) can be easily simulated by the
`--device` command-line option. For the list of available devices see:
https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/deviceDescriptorsSource.json

Additional tests (implemented):
    * Tests search also for 'Seznam' (not only for 'Kazma') to verify other search
      terms.

Additional tests (not implemented):
    E.g.:
        * Searching a Czech term (e.g. 'Štastné pondělí') without diacritics.
        * Verifying that main topics ("Zábava", "Zpravodajství", "Magazín") return
          correct results.

Notes:
    * For some reason, in headless mode `Page.goto()` requires
      `wait_until='networkidle'`, otherwise the user is *not* redirected to
      `https://www.stream.cz/hledani?dotaz=<searched-term>`, the URL only
      changes to `https://www.stream.cz/?dotaz=<searched-term>` and no search
      results are shown.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def modified_context(context):
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

# Occasionally, stream.cz main page is not fully loaded before timeout.
# See note about `wait_until='networkidle'`. But the next trial is usually ok.
pytestmark = pytest.mark.flaky(reruns=1)

base_url = "https://www.stream.cz"

# selectors
sel_search_field = '[placeholder="Zadejte\\, co chcete hledat"]'
sel_search_button = '[aria-label="Vyhledat"]'
sel_search_top_tag = "[class=search-top-tag__tag]"
sel_vcard = "[class=vcard]"
sel_squircle_carousel_list = "[class=squircle-carousel__list]"
sel_search_episodes_list = "[class=search-episodes__list]"

# selectors: mobile-specific
sel_mob_show_search_button = "[data-dot=search-mobile-show]"

test_data = [
    {
        "term": "Kazma",
        "search_result_sections": [
            {"name": "Nejlepší výsledek", "content": sel_search_top_tag},
            {"name": "Pořady", "content": sel_squircle_carousel_list},
            {"name": "VideaFiltry", "content": sel_search_episodes_list},
        ],
    },
    {
        "term": "Seznam",
        "search_result_sections": [
            {"name": "Nejlepší výsledek", "content": sel_vcard},
            {"name": "Pořady", "content": sel_squircle_carousel_list},
            {"name": "VideaFiltry", "content": sel_search_episodes_list},
        ],
    },
]


def search_term(
    page: Page, url: str, term: str, browser_context_args: Dict[Any, Any]
) -> None:
    """Search a term on stream.cz.

    page: playwright.sync_api.Page
    url: str - URL of a page where to start the search
    term: str - term to search for
    browser_context_args: Dict[Any, Any] - pytest-playwright fixture (for details see
        https://playwright.dev/python/docs/test-runners#fixtures)
    """
    logging.info("Opening '%s'", url)
    page.goto(url, wait_until="networkidle")

    logging.info("Searching for '%s'", term)
    if browser_context_args.get("is_mobile", False):
        page.locator(sel_mob_show_search_button).click()
    page.locator(sel_search_field).click()
    page.locator(sel_search_field).fill(term)
    page.locator(sel_search_button).click()

    logging.info("Waiting for redirection")
    expect(page).to_have_url(f"{base_url}/hledani?dotaz={term}")


@pytest.mark.parametrize("test_data", test_data)
def test_basic_search(page, test_data, browser_context_args):
    """Test basic search on the stream.cz main page."""

    search_term(page, base_url, test_data["term"], browser_context_args)

    logging.info("Verifying search results")
    for section in test_data["search_result_sections"]:
        logging.info("Verifying '%s'", section["name"])
        expect(page.locator(f"text={section['name']}")).to_be_visible()
        expect(page.locator(section["content"])).to_be_visible()
        expect(page.locator(section["content"])).not_to_be_empty()


def test_search_for_nonexistent_term(page, browser_context_args):
    """Test searching for a non-existent term returns no results.

    Verify user is presented with an info that no results were found.
    """
    term = "foobarterm"

    search_term(page, base_url, term, browser_context_args)

    logging.info("Verifying no results were found")
    info_msg = page.locator("text=Bohužel jsme nic nenašli")
    expect(info_msg).to_be_visible()
    expect(page.locator(".page-layout-content", has=info_msg)).to_have_count(1)


def test_empty_search_page(page):
    """Test that the search page ('/hledani') shows no results."""
    search_page_url = base_url + "/hledani"

    logging.info("Opening '%s'", search_page_url)
    page.goto(search_page_url, wait_until="networkidle")

    logging.info("Verifying no results are shown")
    info_msg = page.locator("text=Zadejte, co chcete hledat")
    expect(info_msg).to_be_visible()
    expect(page.locator(".page-layout-content", has=info_msg)).to_have_count(1)


@pytest.mark.parametrize("test_data", test_data)
def test_search_for_videos_from_random_page(page, test_data, browser_context_args):
    """Test searching videos any page.

    Verify the button "Načíst další videa" loads more videos.
    """
    url = base_url + "/moje/odebirane"

    search_term(page, url, test_data["term"], browser_context_args)

    logging.info("Verifying search results (videos)")
    for section in test_data["search_result_sections"]:
        if section["name"] == "VideaFiltry":
            videos_section = section
            break
    expect(page.locator(f"text={videos_section['name']}")).to_be_visible()
    expect(page.locator(videos_section["content"])).to_be_visible()
    expect(page.locator(videos_section["content"])).not_to_be_empty()

    sel_search_episodes_item = "[class=search-episodes__item]"
    num_videos: int = page.locator(sel_search_episodes_item).count()
    logging.debug("Videos found: %s", num_videos)

    logging.info("Trying to load more videos")
    page.locator("text=Načíst další videa").click()
    new_num_videos = page.locator(sel_search_episodes_item).count()
    logging.debug("Videos found: %s", new_num_videos)
    assert new_num_videos > num_videos, "No additional videos were loaded"

    logging.info("Verifying all videos are visible")
    num_visible_videos = page.locator("li.search-episodes__item:visible").count()
    logging.debug("Visible videos: %s", num_visible_videos)
    assert num_visible_videos == new_num_videos, "Not all videos are visible"


@pytest.mark.parametrize("test_data", test_data)
def test_basic_video_filtering(page, test_data, browser_context_args):
    """Test basic video filtering.

    Verify video filter 'Střední (do 30 min)' returns correct results.
    """

    search_term(page, base_url, test_data["term"], browser_context_args)

    filter_name = "Střední (do 30 min)"
    logging.info("Verifying filter '%s'", filter_name)
    page.locator("text=Filtry").click()
    page.locator(f"text={filter_name}").click()

    sel_episode_duration = "[class=episode-duration]"
    # Beware: If `locator(...).first.text_content()` is not called, then
    # `locator(...).all_text_contents()` find no elements. Quite strange.
    # Possible a bug in Playwright?
    page.locator(sel_episode_duration).first.text_content()
    durations = page.locator(sel_episode_duration).all_text_contents()
    max_duration = "30:00"
    logging.debug(
        "Found durations: %s; expected max. duration: %s", durations, max_duration
    )
    for duration in durations:
        assert (
            duration < max_duration
        ), f"Unexpected video lenght: {duration}; should be < {max_duration}"
