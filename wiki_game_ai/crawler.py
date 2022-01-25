import logging
import re
import warnings
from time import sleep
from typing import Sequence

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, \
    NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_all_elements_located, \
    presence_of_element_located, url_changes, element_to_be_clickable
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from wiki_game_ai.models import Link

BASE_URL = "https://www.thewikigame.com"
DELAY = 60
IGNORED_EXCEPTIONS = (NoSuchElementException, StaleElementReferenceException)


def text_changed(locator, previous_text):
    def _predicate(driver):
        element = driver.find_element(*locator)
        if element.text != previous_text:
            return element
        return None

    return _predicate


class WikiGameCrawler:
    def __init__(self):
        self.driver = webdriver.Edge(EdgeChromiumDriverManager(log_level=logging.DEBUG).install())
        self.start = None
        self.goal = None
        self.depth = None

    def new_game(self):
        self.driver.get(BASE_URL)
        self.local_storage.remove('userData')

        locator = (By.XPATH, "//button/div[. = 'Play Now!']")
        start_button = WebDriverWait(self.driver, DELAY).until(presence_of_element_located(locator))

        previous_url = self.driver.current_url
        start_button.click()
        WebDriverWait(self.driver, DELAY).until(url_changes(previous_url))
        print(f"URL: {self.driver.current_url}")

        locator = (By.XPATH, "//div[. = 'Start']/following-sibling::div")
        self.start = WebDriverWait(self.driver, DELAY).until(text_changed(locator, "Start article...")).text
        print(f"Start: {self.start}")

        locator = (By.XPATH, "//div[. = 'Goal']/following-sibling::div")
        self.goal = WebDriverWait(self.driver, DELAY).until(text_changed(locator, "Goal article...")).text
        print(f"Goal: {self.goal}")

        self._scroll_down()

        previous_url = self.driver.current_url
        while True:
            try:

                locator = (By.XPATH, "//button/div[. = 'Play Now!']")
                start_button = WebDriverWait(self.driver, DELAY).until(element_to_be_clickable(locator))
                start_button.click()
                break
            except ElementClickInterceptedException:
                print("Unable to start game yet...")
                sleep(1)

        WebDriverWait(self.driver, DELAY).until(url_changes(previous_url))
        print(f"URL: {self.driver.current_url}")

        self.depth = 0

        print("Game started!")

    def get_links(self) -> Sequence[Link]:
        if self.is_game_over:
            warnings.warn("Game is over!")
            return []

        print("Collecting hyperlinks...")

        locator = (By.XPATH, f"//a[starts-with(@href, '/wiki/')]")
        elements = WebDriverWait(self.driver, DELAY, ignored_exceptions=IGNORED_EXCEPTIONS).until(
            presence_of_all_elements_located(locator))

        print(f"{len(elements)} hyperlinks collected")

        try:
            links = [
                Link(element.get_attribute('title'), element.text, element.get_attribute('href'))
                for element in elements
                if not re.search(r"/\w+:\S+$", element.get_attribute('href'))  # Remove /File:.., /Template:.., etc.
            ]
        except StaleElementReferenceException:
            warnings.warn("Failed to read elements, retrying...")
            return self.get_links()

        return links

    def click(self, link: Link):
        if self.is_game_over:
            warnings.warn("Game is over!")
            return

        print(f"Retrieving hyperlink for {link}")

        locator = (By.XPATH, f"//a[contains(@href, '/wiki/{link.topic}')]")
        element = WebDriverWait(self.driver, DELAY, ignored_exceptions=IGNORED_EXCEPTIONS).until(
            presence_of_element_located(locator))

        previous_url = self.driver.current_url

        print(f"Clicking hyperlink...")
        try:
            element.click()
        except ElementClickInterceptedException:
            warnings.warn("Failed to click hyperlink, retrying...")
            return self.click(link)

        try:
            WebDriverWait(self.driver, DELAY).until(url_changes(previous_url))
            print(f"Url: {self.driver.current_url}")
        except UnexpectedAlertPresentException:
            warnings.warn(f"UnexpectedAlertPresentException?!")

        self.depth += 1

    def back(self):
        if self.is_game_over:
            warnings.warn("Game is over!")
        elif self.depth == 0:
            warnings.warn("Already back at start!")
        else:
            self.driver.back()

    @property
    def current(self):
        return self.driver.current_url.split("/")[-1]

    @property
    def is_game_over(self):
        return self.depth is None or self.current == "group" or self.current == self.goal

    def _scroll_down(self):
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
