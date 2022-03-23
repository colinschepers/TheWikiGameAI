from dataclasses import dataclass, field
from typing import List


@dataclass
class Page:
    title: str = ""
    links: List[str] = field(default_factory=list)

    def __str__(self):
        return f"Link(title=\"{self.title}\", num_links={len(self.links)})"


@dataclass
class Link:
    title: str = ""
    text: str = ""
    href: str = ""

    @property
    def url_prefix(self):
        return self.href.split("/")[-1]

    def __str__(self):
        return f"Link(title=\"{self.title}\", url_prefix=\"{self.url_prefix}\")"
