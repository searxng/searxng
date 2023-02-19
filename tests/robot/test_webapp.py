# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring,missing-function-docstring

from time import sleep

url = "http://localhost:11111/"


def test_index(browser):
    # Visit URL
    browser.visit(url)
    assert browser.is_text_present('searxng')


def test_404(browser):
    # Visit URL
    browser.visit(url + 'missing_link')
    assert browser.is_text_present('Page not found')


def test_about(browser):
    browser.visit(url)
    browser.links.find_by_text('searxng').click()
    assert browser.is_text_present('Why use it?')


def test_preferences(browser):
    browser.visit(url)
    browser.links.find_by_href('/preferences').click()
    assert browser.is_text_present('Preferences')
    assert browser.is_text_present('COOKIES')

    assert browser.is_element_present_by_xpath('//label[@for="checkbox_dummy"]')


def test_preferences_engine_select(browser):
    browser.visit(url)
    browser.links.find_by_href('/preferences').click()

    assert browser.is_element_present_by_xpath('//label[@for="tab-engines"]')
    browser.find_by_xpath('//label[@for="tab-engines"]').first.click()

    assert not browser.find_by_xpath('//input[@id="engine_general_dummy__general"]').first.checked
    browser.find_by_xpath('//label[@for="engine_general_dummy__general"]').first.check()
    browser.find_by_xpath('//input[@type="submit"]').first.click()

    # waiting for the redirect - without this the test is flaky..
    sleep(1)

    browser.visit(url)
    browser.links.find_by_href('/preferences').click()
    browser.find_by_xpath('//label[@for="tab-engines"]').first.click()

    assert browser.find_by_xpath('//input[@id="engine_general_dummy__general"]').first.checked


def test_preferences_locale(browser):
    browser.visit(url)
    browser.links.find_by_href('/preferences').click()

    browser.find_by_xpath('//label[@for="tab-ui"]').first.click()
    browser.select('locale', 'fr')
    browser.find_by_xpath('//input[@type="submit"]').first.click()

    # waiting for the redirect - without this the test is flaky..
    sleep(1)

    browser.visit(url)
    browser.links.find_by_href('/preferences').click()
    browser.is_text_present('Préférences')


def test_search(browser):
    browser.visit(url)
    browser.fill('q', 'test search query')
    browser.find_by_xpath('//button[@type="submit"]').first.click()
    assert browser.is_text_present('didn\'t find any results')
