from collections import deque

from app.domain import Priority


WEIGHTS = {
    Priority.CRITICAL: 8,
    Priority.HIGH: 4,
    Priority.NORMAL: 2,
    Priority.LOW: 1,
}


def weighted_priority_cycle() -> deque[Priority]:
    cycle: deque[Priority] = deque()
    for priority, weight in WEIGHTS.items():
        cycle.extend([priority] * weight)
    return cycle


def stream_name(priority: Priority) -> str:
    return f"queueflow:{priority.lower()}"
