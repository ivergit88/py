import zlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class BlobType(Enum):
    """Helper class for holding blob type"""
    COMMIT = b'commit'
    TREE = b'tree'
    DATA = b'blob'

    @classmethod
    def from_bytes(cls, type_: bytes) -> 'BlobType':
        for member in cls:
            if member.value == type_:
                return member
        assert False, f'Unknown type {type_.decode("utf-8")}'


@dataclass
class Blob:
    """Any blob holder"""
    type_: BlobType
    content: bytes


@dataclass
class Commit:
    """Commit blob holder"""
    tree_hash: str
    parents: list[str]
    author: str
    committer: str
    message: str


@dataclass
class Tree:
    """Tree blob holder"""
    children: dict[str, Blob]


def read_blob(path: Path) -> Blob:
    """
    Read blob-file, decompress and parse header
    :param path: path to blob-file
    :return: blob-file type and content
    """
    with open(path, 'rb') as f:
        compressed = f.read()

    decompressed = zlib.decompress(compressed)
    header_end = decompressed.index(b'\x00')
    header = decompressed[:header_end].decode()
    content = decompressed[header_end + 1:]

    type_str, _ = header.split(' ')
    return Blob(BlobType.from_bytes(type_str.encode()), content)


def traverse_objects(obj_dir: Path) -> dict[str, Blob]:
    """
    Traverse directory with git objects and load them
    :param obj_dir: path to git "objects" directory
    :return: mapping from hash to blob with every blob found
    """
    result = {}

    for subdir in obj_dir.iterdir():
        if subdir.is_dir() and len(subdir.name) == 2:
            for file in subdir.iterdir():
                if file.is_file():
                    hash_val = subdir.name + file.name
                    result[hash_val] = read_blob(file)

    return result


def parse_commit(blob: Blob) -> Commit:
    """
    Parse commit blob
    :param blob: blob with commit type
    :return: parsed commit
    """
    lines = blob.content.decode().split('\n')
    tree_hash = ""
    parents: list[str] = []
    author = ""
    committer = ""
    message_lines: list[str] = []
    in_message = False

    for line in lines:
        if in_message:
            message_lines.append(line)
        elif line.startswith('tree '):
            tree_hash = line[5:]
        elif line.startswith('parent '):
            parents.append(line[7:])
        elif line.startswith('author '):
            author = line[7:]
        elif line.startswith('committer '):
            committer = line[10:]
        elif line == '':
            in_message = True

    return Commit(tree_hash, parents, author, committer, '\n'.join(message_lines).rstrip())


def parse_tree(blobs: dict[str, Blob], tree_root: Blob, ignore_missing: bool = True) -> Tree:
    """
    Parse tree blob
    :param blobs: all read blobs (by traverse_objects)
    :param tree_root: tree blob to parse
    :param ignore_missing: ignore blobs which were not found in objects directory
    :return: tree contains children blobs (or only part of them found in objects directory)
    NB. Children blobs are not being parsed according to type.
        Also nested tree blobs are not being traversed.
    """
    children = {}
    content = tree_root.content
    i = 0

    while i < len(content):
        space_idx = content.index(b' ', i)
        null_idx = content.index(b'\x00', space_idx)

        name = content[space_idx + 1:null_idx].decode()
        hash_val = content[null_idx + 1:null_idx + 21].hex()

        if hash_val in blobs:
            children[name] = blobs[hash_val]
        elif not ignore_missing:
            raise ValueError(f"Missing blob: {hash_val}")

        i = null_idx + 21

    return Tree(children)


def find_initial_commit(blobs: dict[str, Blob]) -> Commit:
    """
    Iterate over blobs and find initial commit (without parents)
    :param blobs: blobs read from objects dir
    :return: initial commit
    """
    for hash_val, blob in blobs.items():
        if blob.type_ == BlobType.COMMIT:
            commit = parse_commit(blob)
            if not commit.parents:
                return commit

    raise ValueError("No initial commit found")


def search_file(blobs: dict[str, Blob], tree_root: Blob, filename: str) -> Blob:
    """
    Traverse tree blob (can have nested tree blobs) and find requested file,
    check if file was not found (assertion).
    :param blobs: blobs read from objects dir
    :param tree_root: root blob for traversal
    :param filename: requested file
    :return: requested file blob
    """
    tree = parse_tree(blobs, tree_root)

    for name, blob in tree.children.items():
        if name == filename:
            return blob
        if blob.type_ == BlobType.TREE:
            try:
                return search_file(blobs, blob, filename)
            except AssertionError:
                continue

    assert False, f"File {filename} not found"
