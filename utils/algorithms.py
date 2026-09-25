from heapq import heappop, heappush

def build_graph(path: list[str]) -> dict:
    graph = {skill: [] for skill in path}
    for left, right in zip(path, path[1:]):
        graph[left].append(right)
    return graph

def bfs(graph, start, target):
    queue, visited = [(start, [start])], {start}
    while queue:
        node, path = queue.pop(0)
        if node == target: return path
        for next_node in graph.get(node, []):
            if next_node not in visited:
                visited.add(next_node); queue.append((next_node, path + [next_node]))
    return []

def dfs(graph, start, target):
    stack, visited = [(start, [start])], set()
    while stack:
        node, path = stack.pop()
        if node == target: return path
        if node in visited: continue
        visited.add(node)
        stack.extend((n, path + [n]) for n in reversed(graph.get(node, [])))
    return []

def astar(graph, start, target):
    frontier, seen = [(0, 0, start, [start])], set()
    while frontier:
        _, cost, node, path = heappop(frontier)
        if node == target: return path
        if node in seen: continue
        seen.add(node)
        for n in graph.get(node, []): heappush(frontier, (cost + 1, cost + 1, n, path + [n]))
    return []
