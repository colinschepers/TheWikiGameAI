import re
from time import sleep
from typing import Callable, Sequence

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located, url_changes, \
    element_to_be_clickable
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager

from wiki_game_ai.models import Link

BASE_URL = "https://www.thewikigame.com"
IGNORED_EXCEPTIONS = (NoSuchElementException, StaleElementReferenceException)
TIMEOUT = 3
RETRIES = 3
RETRY_DELAY = 0.2


def text_changed(locator, previous_text):
    def _predicate(driver):
        element = driver.find_element(*locator)
        if element.text != previous_text:
            return element
        return None

    return _predicate


class WikiGameCrawler:
    def __init__(self):
        self.start = None
        self.goal = None
        self.current = None
        self._driver = None

    @property
    def driver(self):
        if not self._driver:
            self._driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
            self._driver.implicitly_wait(TIMEOUT)
        return self._driver

    def new_game(self, bot_name: str = None, group_code: str = None):
        try:
            self.current = None

            self.driver.get(BASE_URL)

            if bot_name and group_code:
                self.join_game(bot_name, group_code)
            else:
                self.click_button(self.get_new_game_button)

            if self.url_suffix == "group":
                locator = (By.XPATH, "//div[. = 'Start']/following-sibling::div")
                self.start = WebDriverWait(self.driver, TIMEOUT).until(text_changed(locator, "Start article..."))\
                    .text.replace(" ", "_")
                print(f"Start: {self.start}")

                locator = (By.XPATH, "//div[. = 'Goal']/following-sibling::div")
                self.goal = WebDriverWait(self.driver, TIMEOUT).until(text_changed(locator, "Goal article..."))\
                    .text.replace(" ", "_")
                print(f"Goal: {self.goal}")

                self.current = self.start

                self._scroll_down()

                self.click_button(self.get_new_game_button)

            print("Game started!")

        except Exception as ex:
            print(f"Could not start game: {ex}")

    def get_links(self) -> Sequence[Link]:
        if self.is_game_over:
            print("Game is over!")
            return []

        try:
            locator = (By.XPATH, f"//div[contains(@class , 'link')]")
            elements = self.driver.find_elements(*locator)
            self.start = elements[0].text.replace(" ", "_")
            self.goal = elements[1].text.replace(" ", "_")
            print(f"Start: {self.start} \t Current: {self.current} \t Goal: {self.goal}")

            print("Collecting hyperlinks...")
            script = """
                return Array.from(document.querySelectorAll('a')).map(function(element) {
                    return [element.title, element.text, element.href];                
                })
            """
            elements = self.driver.execute_script(script)

            # Remove duplicates
            elements = list({element[-1]: element for element in elements}.values())

            print(f"{len(elements)} hyperlinks collected")

            links = []
            for title, text, href in elements:
                if not href or not title or not text:
                    continue

                # Filter hyperlinks not on same domain
                if not href.startswith("https://www.thewikigame.com/wiki/"):
                    continue

                # Filter hyperlinks containing /File:.., /Template:.., etc.
                if re.search(r"/\w+:\S+$", href):
                    continue

                links.append(Link(title, text, href))

            print(f"Returning links")
            return links

        except Exception as ex:
            print(f"Could not get links: {ex}")

        return []

    def click(self, link: Link):
        if self.is_game_over:
            print("Game is over!")
            return False

        previous_url = self.driver.current_url

        success = False
        for i in range(RETRIES):
            try:
                print(f"Retrieving hyperlink for {link}")
                locator = (By.XPATH, f"//a[contains(@href, '/wiki/{link.url_prefix}')]")
                element = WebDriverWait(self.driver, TIMEOUT, ignored_exceptions=IGNORED_EXCEPTIONS).until(
                    presence_of_element_located(locator) and element_to_be_clickable(locator))

                print(f"Clicking hyperlink...")
                element.click()

                success = True
                break
            except Exception as ex:
                print(f"Unable to click hyperlink: {ex}")

            sleep(RETRY_DELAY)

        if not success:
            return False

        success = False
        for i in range(RETRIES):
            try:
                WebDriverWait(self.driver, TIMEOUT).until(url_changes(previous_url))
                print(f"URL: {self.driver.current_url}")
                success = True
                break
            except Exception as ex:
                sleep(RETRY_DELAY)

        if not success:
            return False

        self.current = link.title
        return True

    def back(self):
        if self.is_game_over:
            print("Game is over!")
            return

        try:
            previous_url = self.driver.current_url
            self.driver.back()

            for i in range(RETRIES):
                try:
                    WebDriverWait(self.driver, TIMEOUT).until(url_changes(previous_url))
                    print(f"Back to URL: {self.driver.current_url}")
                    break
                except Exception as ex:
                    pass
                sleep(RETRY_DELAY)

        except Exception as ex:
            print(f"Failed to go back: {ex}")

    @property
    def url_suffix(self):
        return self.driver.current_url.split("/")[-1]

    def get_buttons(self):
        script = """
            return Array.from(document.querySelectorAll("button")).map(function(element) {
                return element;
            })
        """
        return self.driver.execute_script(script)

    def get_new_game_button(self):
        button_text_starts = ("play now", "find another path", "round is over", "next round")
        for button in self.get_buttons():
            try:
                text = button.text.lower()
                if any(text.startswith(button_text) for button_text in button_text_starts):
                    return button
            except Exception as ex:
                print(f"Could not read button element: {ex}")
        return None

    def get_join_game_button(self):
        for button in self.get_buttons():
            try:
                text = button.text.lower()
                if text.startswith("join"):
                    return button
            except Exception as ex:
                print(f"Could not read button element: {ex}")
        return None

    def click_button(self, button_getter: Callable):
        previous_url = self.driver.current_url

        for i in range(RETRIES):
            try:
                button = button_getter()
                if button:
                    button.click()
                    break
            except Exception:
                print("Unable to click start game button...")
            sleep(RETRY_DELAY)

        for i in range(RETRIES):
            try:
                WebDriverWait(self.driver, TIMEOUT).until(url_changes(previous_url))
                print(f"URL: {self.driver.current_url}")
                break
            except Exception as ex:
                pass
            sleep(RETRY_DELAY)

    def get_name_input(self):
        script = """
            return Array.from(document.querySelectorAll("input[name=name]")).map(function(element) {
                return element;
            })
        """
        return next(iter(self.driver.execute_script(script)), None)

    def get_code_input(self):
        script = """
            return Array.from(document.querySelectorAll("input[name=code]")).map(function(element) {
                return element;
            })
        """
        return next(iter(self.driver.execute_script(script)), None)

    def join_game(self, bot_name: str, group_code: str):
        name_input = self.get_name_input()
        code_input = self.get_code_input()
        if name_input and code_input:
            name_input.send_keys(bot_name)
            code_input.send_keys(group_code)
            self.click_button(self.get_join_game_button)

    @property
    def is_game_over(self):
        try:
            return bool(self.get_new_game_button())
        except Exception as ex:
            return False

    @property
    def has_won(self):
        if self.current == self.goal:
            return True
        try:
            button = self.get_new_game_button()
            return button and button.text.lower().startswith("find another path")
        except Exception as ex:
            return False

    def _scroll_down(self):
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
