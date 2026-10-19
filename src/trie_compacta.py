class Node:
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.children: dict[str, Node] = {}
        self.values: list = []

class CompactTrie:
    def __init__(self):
        self.root = Node()

    def insert(self, key: str, value) -> None:
        curr = self.root
        remaining = key

        while remaining:
            first_char = remaining[0]

            if first_char not in curr.children:
                new_node = Node(remaining)
                new_node.values.append(value)
                curr.children[first_char] = new_node
                return

            child = curr.children[first_char]
            
            match_len = 0
            limit = min(len(remaining), len(child.prefix))
            while match_len < limit and remaining[match_len] == child.prefix[match_len]:
                match_len += 1

            if match_len == len(child.prefix):
                remaining = remaining[match_len:]
                curr = child
                continue

            split_node = Node(child.prefix[:match_len])
            curr.children[first_char] = split_node

            child.prefix = child.prefix[match_len:]
            split_node.children[child.prefix[0]] = child

            remaining = remaining[match_len:]

            if remaining:
                new_leaf = Node(remaining)
                new_leaf.values.append(value)
                split_node.children[remaining[0]] = new_leaf
            else:
                split_node.values.append(value)

            return

        curr.values.append(value)

    def search_prefix(self, prefix: str) -> list:
        curr = self.root
        remaining = prefix

        while remaining:
            first_char = remaining[0]
            if first_char not in curr.children:
                return []

            child = curr.children[first_char]

            if len(remaining) <= len(child.prefix):
                if child.prefix.startswith(remaining):
                    return self.collect(child)
                return []

            if remaining.startswith(child.prefix):
                remaining = remaining[len(child.prefix):]
                curr = child
            else:
                return []

        return self.collect(curr)

    def collect(self, start_node: Node) -> list:
        results = []
        stack = [start_node]

        while stack:
            node = stack.pop()
            if node.values:
                results.extend(node.values)
            for child in node.children.values():
                stack.append(child)

        return results