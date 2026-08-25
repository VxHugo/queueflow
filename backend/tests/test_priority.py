from app.domain import Priority
from app.priority import weighted_priority_cycle


def test_weighted_cycle_favors_critical_without_starving_low() -> None:
    cycle = weighted_priority_cycle()
    assert len(cycle) == 15
    assert cycle.count(Priority.CRITICAL) == 8
    assert cycle.count(Priority.LOW) == 1
