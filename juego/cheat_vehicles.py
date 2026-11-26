"""Navigation helpers for optional boat/air autopilots and empty vehicles."""
import heapq
import math


def segment_distance(point, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    den = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / den)) if den else 0.0
    return math.hypot(point[0] - start[0] - t * dx, point[1] - start[1] - t * dy)


def water_route(world, start, destination):
    """Visibility graph around the sea map's circular islands, with clearance.

    Every edge is checked against every island. Polygon chords stay outside
    the safety radius; the boat follows straight segments without cutting
    corners, rather than steering through land toward the GPS marker.
    """
    original_start = start
    start = world.punto_libre(*start)
    prefix = [start] if math.dist(original_start, start) > 0.05 else []
    goal = world.punto_libre(*destination)
    islands = getattr(world, "islas", [])

    def clear(a, b):
        if not all(0 <= p[0] <= world.ancho and 0 <= p[1] <= world.alto for p in (a, b)):
            return False
        return all(segment_distance((i["x"], i["y"]), a, b) >= i["r"] + 3.0 for i in islands)

    if clear(start, goal):
        return prefix + [goal]
    nodes = [start, goal]
    sides = 24
    for island in islands:
        radius = (island["r"] + 8.0) / math.cos(math.pi / sides)
        for n in range(sides):
            a = 2 * math.pi * n / sides
            p = (island["x"] + math.cos(a) * radius, island["y"] + math.sin(a) * radius)
            if world.superficie(*p) == "agua":
                nodes.append(p)
    costs, previous, queue = {0: 0.0}, {}, [(0.0, 0)]
    while queue:
        distance, k = heapq.heappop(queue)
        if distance != costs[k]:
            continue
        if k == 1:
            route = []
            while k:
                route.append(nodes[k])
                k = previous[k]
            return prefix + route[::-1]
        for j, p in enumerate(nodes):
            if j == k or not clear(nodes[k], p):
                continue
            candidate = distance + math.dist(nodes[k], p)
            if candidate < costs.get(j, float("inf")):
                costs[j], previous[j] = candidate, k
                heapq.heappush(queue, (candidate, j))
    return []


def toward(vehicle, point, dt, speed, acceleration=8.0):
    """A non-overshooting step toward an already collision-checked waypoint."""
    from . import mundo as M
    dx, dy = point[0] - vehicle.x, point[1] - vehicle.y
    distance = math.hypot(dx, dy)
    vehicle.rumbo = M.rumbo_a(dx, dy) % 360
    vehicle.dir = M.dir_de_rumbo(vehicle.rumbo)
    vehicle.vel += max(-acceleration * dt, min(acceleration * dt, speed - vehicle.vel))
    step = min(distance, max(0.0, vehicle.vel) * dt)
    if distance:
        return vehicle.x + dx * step / distance, vehicle.y + dy * step / distance
    return vehicle.x, vehicle.y
