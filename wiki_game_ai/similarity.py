from typing import List, Tuple

from scipy.spatial.distance import cdist
from sentence_transformers import SentenceTransformer

from wiki_game_ai.config import CONFIG

SENTENCE_TRANSFORMER = SentenceTransformer(CONFIG['language_model_name'])


class SimilarityRanker:
    def __init__(self):
        self.cache = {}

    def sorted(self, data: List[str], reference: str) -> List[Tuple[str, float]]:
        return sorted(zip(data, self._get_similarities(data, reference)), key=lambda x: x[1], reverse=True)

    def get_most_similar(self, data: List[str], reference: str) -> Tuple[str, float]:
        return max(zip(data, self._get_similarities(data, reference)), key=lambda x: x[1])

    def get_similarity(self, data: str, reference: str) -> Tuple[str, float]:
        return self._get_similarities([data], reference)

    def _get_similarities(self, data: List[str], reference: str):
        if not data:
            return []

        not_in_cache = [x for x in data + [reference] if x not in self.cache]
        if not_in_cache:
            embeddings = SENTENCE_TRANSFORMER.encode(not_in_cache, show_progress_bar=False)
            self.cache.update({text: embedding for text, embedding in zip(not_in_cache, embeddings)})

        embeddings = [self.cache[x] for x in data]
        distances = cdist([self.cache[reference]], embeddings, "cosine")[0]
        return 1 - distances
