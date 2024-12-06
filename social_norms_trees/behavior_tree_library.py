from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Behavior:
    name: str
    id: Optional[str] = None


@dataclass
class Composite:
    name: str
    children: List[Behavior] = field(default_factory=list)

    def add_child(self, child: Behavior):
        self.children.append(child)

    def insert_child(self, index: int, child: Behavior):
        if 0 <= index <= len(self.children):
            self.children.insert(index, child)

    def remove_child(self, child: Behavior):
        if child in self.children:
            self.children.remove(child)


@dataclass
class Sequence(Composite):
    pass


@dataclass
class Selector(Composite):
    pass
