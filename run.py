from wiki_game_ai.crawler import WikiGameCrawler
from wiki_game_ai.similarity import SimilarityRanker

similarity_ranker = SimilarityRanker()

crawler = WikiGameCrawler()

while True:
    visited = set()

    crawler.new_game()

    while not crawler.is_game_over:
        if links := crawler.get_links():
            texts = [link.text for link in links]
            results = similarity_ranker.sorted(texts, crawler.goal)
            print(f"Top 5: {results[:5]}")

            best_result = next(result for result, score in results if result not in visited)
            visited.add(best_result)

            best_link = next(link for link in links if link.text == best_result)
            crawler.click(best_link)
