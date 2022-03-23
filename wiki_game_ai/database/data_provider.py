from typing import Sequence

from wiki_game_ai.database.connection import PostgresConnection
from wiki_game_ai.models import Page


def get_pages(connection: PostgresConnection, titles: Sequence[str]) -> Sequence[Page]:
    if not titles:
        return []

    with connection.cursor() as cursor:
        cursor.execute("""
                    select p.title, pl.title link
                    from page p
                    left join redirect r on r.from = p.id
                    left join page p2 on p2.title = r.title
                    left join pagelink pl on (pl.from = p2.id) or (pl.from = p.id)
                    where p.title in %s and pl.namespace = 0
                """, (tuple(titles),))

        pages = {}
        for title, link in cursor:
            if title not in pages:
                pages[title] = Page(title)
            pages[title].links.append(link)

        return [pages[title] if title in pages else Page(title) for title in titles]
