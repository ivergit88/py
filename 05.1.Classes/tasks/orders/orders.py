from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field

DISCOUNT_PERCENTS = 15


@dataclass(order=True, frozen=True)
class Item:
    item_id: int = field(compare=False)
    title: str
    cost: int

    def __post_init__(self) -> None:
        assert self.title
        assert self.cost > 0


@dataclass(frozen=True)
class Position(ABC):
    item: Item

    @property
    @abstractmethod
    def cost(self) -> float | int:
        raise NotImplementedError


@dataclass(frozen=True)
class CountedPosition(Position):
    count: int = 1

    @property
    def cost(self) -> int:
        return self.item.cost * self.count


@dataclass(frozen=True)
class WeightedPosition(Position):
    weight: float = 1

    @property
    def cost(self) -> float:
        return self.item.cost * self.weight


@dataclass
class Order:
    order_id: int
    positions: list[Position] = field(default_factory=list)
    have_promo: InitVar[bool] = False
    cost: int = field(init=False)

    def __post_init__(self, have_promo: bool) -> None:
        total = sum(position.cost for position in self.positions)
        if have_promo:
            total *= (100 - DISCOUNT_PERCENTS) / 100
        self.cost = int(total)
