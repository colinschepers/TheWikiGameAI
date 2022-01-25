from dataclasses import dataclass


@dataclass
class Link:
    title: str = ""
    text: str = ""
    href: str = ""

    @property
    def topic(self):
        return self.href.split("/")[-1]

    def __str__(self):
        return f"Link(title=\"{self.title}\", topic=\"{self.topic}\", text=\"{self.text}\")"
