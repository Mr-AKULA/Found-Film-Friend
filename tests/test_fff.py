import re
from playwright.sync_api import Page, expect


def test_fff_loads(page: Page):
    page.goto("https://mr-akula.github.io/Found-Film-Friend/")
    expect(page).to_have_title(re.compile(".+"))
    expect(page.locator("#login-email")).to_be_visible()
