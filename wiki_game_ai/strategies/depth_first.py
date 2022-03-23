from pathlib import Path
from random import Random
from time import sleep

from wiki_game_ai.config import CONFIG
from wiki_game_ai.crawler import WikiGameCrawler
from wiki_game_ai.similarity import SimilarityRanker

BOT_NAME = Path(__file__).stem.title() + "_Bot"
GROUP_CODE = CONFIG.get("group_code", None)
RANDOM = Random()
GAME_DECAY = 0.8


def run(crawler: WikiGameCrawler, ranker: SimilarityRanker):
    goal = ""
    certainty = None

    while True:
        print("Starting game...")
        crawler.new_game(BOT_NAME, GROUP_CODE)

        is_new_game = crawler.goal != goal
        certainty = 1.0 if is_new_game else certainty * GAME_DECAY
        goal = crawler.goal
        visited = set()

        while not crawler.is_game_over:
            if links := crawler.get_links():
                data = [link.title for link in links]
                results = ranker.sorted(data, crawler.goal)

                print(f"Top 10:")
                for result in results[:10]:
                    print(result)

                best_result = results[0][0]
                for result, score in results:
                    if result in visited:
                        continue
                    if RANDOM.random() <= certainty:
                        best_result = result
                        break

                visited.add(best_result)

                print(f"Chosen {best_result} based on certainty {certainty}")

                best_link = next(link for link in links if link.title == best_result)
                crawler.click(best_link)

                if crawler.has_won:
                    print("WIN!!!")
                    sleep(3)
