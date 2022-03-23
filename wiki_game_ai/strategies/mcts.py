from math import log, sqrt
from pathlib import Path
from time import sleep
from typing import Optional

from wiki_game_ai.config import CONFIG
from wiki_game_ai.crawler import WikiGameCrawler
from wiki_game_ai.models import Link
from wiki_game_ai.similarity import SimilarityRanker

BOT_NAME = Path(__file__).stem.title() + "_Bot"
GROUP_CODE = CONFIG.get("group_code", None)
MAX_BREADTH = 3
UCT_C = sqrt(2)


class Node:
    def __init__(self, link: Optional[Link], depth: int, parent: Optional["Node"], score: float = 0.0):
        self.link = link
        self.depth = depth
        self.parent = parent
        self.children = []
        self.cum_score = score
        self.num_visits = 1

    @property
    def score(self):
        return self.cum_score / self.num_visits if self.num_visits > 0 else 0

    @property
    def is_leaf(self):
        return not any(self.children)

    def __str__(self):
        title = self.link.title if self.link else ""
        return "-" * self.depth + f"Node(title={title}, score={self.score}, num_visits={self.num_visits})\n" \
            + "".join(str(child) for child in self.children)


class Mcts:
    """
    Real time solver for The Wiki Game, based on Monte Carlo Tree Search.
    """
    def __init__(self, ranker: SimilarityRanker):
        self.root = None
        self.nodes = None
        self.ranker = ranker

    def run(self, crawler: WikiGameCrawler):
        self.root = Node(None, 0, None, 0)
        self.root.num_visits -= 1
        self.nodes = dict()

        node = self.root

        while not crawler.is_game_over or crawler.has_won:
            if crawler.has_won:
                print("WIN!!!")
                sleep(1)

            if not node.is_leaf:
                node = self.selection(node, crawler)
            else:
                score = self.expand(node, crawler)
                self.backtrack(node, crawler, score)
                node = self.root
                print(self)
                print()

    def selection(self, node: Node, crawler: WikiGameCrawler):
        best_child, best_score = None, float('-inf')
        for child in node.children:
            uct_score = sqrt(2.0 * log(node.num_visits) / child.num_visits)
            score = child.score + UCT_C * uct_score
            if score > best_score:
                best_score = score
                best_child = child

        crawler.click(best_child.link)
        return best_child

    def expand(self, node: Node, crawler: WikiGameCrawler):
        links = crawler.get_links()
        links_by_title = {link.title: link for link in links}
        titles = [link.title for link in links]
        results = self.ranker.sorted(titles, crawler.goal)

        for title, score in results[:MAX_BREADTH]:
            link = links_by_title[title]
            child = Node(link, node.depth + 1, node, score)
            node.children.append(child)
            self.nodes[title] = child

        return node.children[0].score if node.children else 0

    def backtrack(self, node: Node, crawler: WikiGameCrawler, score: float):
        while node:
            node.cum_score += score
            node.num_visits += 1
            node = node.parent
            if node:
                crawler.back()

    def __str__(self):
        return str(self.root)


def run(crawler: WikiGameCrawler, ranker: SimilarityRanker):
    goal = ""
    mcts = None

    while True:
        print("Starting game...")
        crawler.new_game(BOT_NAME, GROUP_CODE)

        is_new_game = crawler.goal != goal
        goal = crawler.goal

        if is_new_game:
            mcts = Mcts(ranker)

        mcts.run(crawler)
