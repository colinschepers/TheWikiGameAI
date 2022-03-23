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
RANDOMNESS = 7


def run(crawler: WikiGameCrawler, ranker: SimilarityRanker):
    goal = ""
    america_first = 'United States'
    certainty = None
    columbus = False

    while True:
        print("Starting game...")
        crawler.new_game(BOT_NAME, GROUP_CODE)

        is_new_game = crawler.goal != goal
        certainty = 1.0 if is_new_game else certainty * GAME_DECAY
        goal = crawler.goal
        visited = set()

        while not crawler.is_game_over:
            columbus |= crawler.url_suffix == 'United_States_of_America'
            if links := crawler.get_links():
                data = [link.title for link in links]
                results = ranker.sorted(data, america_first if not columbus else crawler.goal)

                print(f"Top 10:")
                for result in results[:10]:
                    print(result)

                if columbus and len(visited) % RANDOMNESS == 0:
                    best_result = results[RANDOM.randint(0, len(results) - 1)][0]
                else:
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
