from typing import Protocol, TypeVar

ContentType = TypeVar("ContentType", covariant=True)

class Gettable(Protocol[ContentType]):
    def __getitem__(self, index: int) -> ContentType:
        ...

    def __len__(self) -> int:
        ...

def get(container: Gettable[ContentType] | None, index: int) -> ContentType | None:
    if container:
        return container[index]
    return None
