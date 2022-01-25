from typing import List, Tuple

from scipy.spatial.distance import cdist
from sentence_transformers import SentenceTransformer

from wiki_game_ai.config import CONFIG

sentence_transformer = SentenceTransformer(CONFIG['language_model_name'])


class SimilarityRanker:
    def __init__(self):
        pass

    def sorted(self, data: List[str], reference: str) -> List[Tuple[str, float]]:
        return sorted(zip(data, self._get_similarities(data, reference)), key=lambda x: x[1], reverse=True)

    def get_most_similar(self, data: List[str], reference: str) -> Tuple[str, float]:
        return max(zip(data, self._get_similarities(data, reference)), key=lambda x: x[1])

    @staticmethod
    def _get_similarities(data: List[str], reference: str):
        embeddings = sentence_transformer.encode(data + [reference], show_progress_bar=True)
        distances = cdist(embeddings[-1:], embeddings[:-1], "cosine")[0]
        return 1 - distances
