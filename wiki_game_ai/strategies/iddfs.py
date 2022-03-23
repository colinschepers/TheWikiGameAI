from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from tqdm import tqdm

from wiki_game_ai.config import CONFIG
from wiki_game_ai.crawler import WikiGameCrawler
from wiki_game_ai.database.connection import PostgresConnection
from wiki_game_ai.database.data_provider import get_pages
from wiki_game_ai.models import Page
from wiki_game_ai.similarity import SimilarityRanker

BOT_NAME = Path(__file__).stem.title() + "_Bot"
GROUP_CODE = CONFIG.get("group_code", None)
CONNECTION = PostgresConnection(**CONFIG["database"])
MAX_PAGES = 250


class Iddfs:
    """
    Iterative Deepening Depth First Search using reference data from Wikipedia in a Postgres Database.

    See https://github.com/colinschepers/wikipedia2pg for crawling the Wikipedia data.

    Unfortunately, the Wikipedia pages contain much more information than the pages from TheWikiGame,
    resulting in a lot of overhead and backtracking.
    """

    def __init__(self, crawler: WikiGameCrawler, ranker: SimilarityRanker):
        self.crawler = crawler
        self.ranker = ranker
        self.start, self.goal = get_pages(CONNECTION, [crawler.start, crawler.goal])
        self.page_cache = {}
        self.solutions = []

    def solve(self, max_breadth: int, max_depth: int) -> Iterable[List[str]]:
        for _max_depth in tqdm(range(1, max_depth)):
            if self.crawler.is_game_over:
                return

            path, visited = [self.start.title], {}
            yield from self.solve_for_depth(self.start, 0, max_breadth, _max_depth, visited, path)

    def solve_for_depth(self, page: Page, depth: int, max_breadth: int, max_depth: int,
                        visited: Dict[str, int], path: List[str]) -> Iterable[List[str]]:
        if self.goal.title in page.links:
            solution = path + [self.goal.title]
            if solution not in self.solutions:
                self.solutions.append(solution)
                yield solution
            return

        if visited.get(page.title, float('inf')) <= depth:
            return

        visited[page.title] = depth

        if self.crawler.is_game_over or depth >= max_depth:
            return

        links = list(set(link for link in page.links if 'disambiguation' not in link))[:MAX_PAGES]
        best_links = [title for title, score in self.ranker.sorted(links, self.goal.title)][:max_breadth]
        for next_page in self.get_pages(best_links):
            yield from self.solve_for_depth(next_page, depth + 1, max_breadth, max_depth,
                                            visited, path + [next_page.title])

    def get_pages(self, titles: Sequence[str]) -> Iterable[Page]:
        titles_not_in_cache = [title for title in titles if title not in self.page_cache]
        self.page_cache.update({page.title: page for page in get_pages(CONNECTION, titles_not_in_cache)})
        return (self.page_cache[title] for title in titles)

    def fix_links(self):
        # Remove links from reference data that are not on WikiGame
        links = self.crawler.get_links()
        url_prefixes = {link.url_prefix for link in links}
        page, = self.get_pages([self.crawler.url_suffix])
        page.links = [link for link in page.links if link in url_prefixes]


def run(crawler: WikiGameCrawler, ranker: SimilarityRanker):
    iddfs, goal, max_breadth, max_depth = None, "", 0, 0

    while True:
        print("Starting game...")
        crawler.new_game(BOT_NAME, GROUP_CODE)

        is_new_game = crawler.goal != goal
        goal = crawler.goal

        if is_new_game:
            iddfs = Iddfs(crawler, ranker)
            iddfs.fix_links()
            max_breadth = 6
            max_depth = 6

        while not crawler.is_game_over:
            for solution in iddfs.solve(max_breadth=max_breadth, max_depth=max_depth):

                print("************ Solution: ", solution)

                for i, solution_step in enumerate(solution[1:]):
                    if crawler.is_game_over:
                        break

                    if links := crawler.get_links():
                        if solution_link := next((link for link in links if link.url_prefix == solution_step), None):
                            crawler.click(solution_link)
                            iddfs.fix_links()
                        else:
                            print(f"Link {solution_step} not found!")
                            for _ in range(i):
                                crawler.back()
                            break

            max_breadth += 1
            max_depth += 1


if __name__ == '__main__':
    crawler = WikiGameCrawler()
    crawler.start = "Data_science"
    crawler.goal = "NASA"
    for solution in Iddfs(crawler, SimilarityRanker()).solve(max_breadth=5, max_depth=5):
        print(solution)
