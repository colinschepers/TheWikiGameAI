import argparse

from wiki_game_ai.crawler import WikiGameCrawler
from wiki_game_ai.similarity import SimilarityRanker
from wiki_game_ai.strategies import america_first, depth_first, iddfs, mcts

CRAWLER = WikiGameCrawler()
RANKER = SimilarityRanker()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("strategy", type=str, default="depth_first")
    args = parser.parse_args()

    if args.strategy == "depth_first":
        depth_first.run(CRAWLER, RANKER)
    elif args.strategy == "america_first":
        america_first.run(CRAWLER, RANKER)
    elif args.strategy == "mcts":
        mcts.run(CRAWLER, RANKER)
    elif args.strategy == "iddfs":
        iddfs.run(CRAWLER, RANKER)
    else:
        raise ValueError("Invalid strategy")
