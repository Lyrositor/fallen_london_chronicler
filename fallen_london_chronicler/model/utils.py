from datetime import datetime
from typing import Any, Iterable, Type, TypeVar, Dict, List

from sqlalchemy import inspect
from sqlalchemy.orm.collections import InstrumentedList

T = TypeVar("T")


def latest_observation_property(
        observations: Iterable[Any], attr_name: str
) -> Any:
    observation = next((o for o in observations), None)
    value = None
    if observation:
        value = getattr(observation, attr_name, None)
    return value


def record_observation(
        observations: InstrumentedList,
        observation_cls: Type[T],
        **values: Any
) -> T:
    for observation in observations:
        for name, value in values.items():
            if value is None:
                continue
            observed_value = getattr(observation, name)
            if observed_value is not None:
                if isinstance(value, list) and value:
                    diffable_value = \
                        get_diffable_observation_relationship_values(value)
                    diffable_observed_value = \
                        get_diffable_observation_relationship_values(observed_value)
                    if diffable_value != diffable_observed_value:
                        break
                elif observed_value != value:
                    break
        else:
            for name, value in values.items():
                if value is None:
                    continue
                setattr(observation, name, value)
            observation.last_modified = datetime.utcnow()
            return observation
    new_observation = observation_cls(**values)
    observations.append(new_observation)
    import pprint
    pprint.pprint(observations)
    return new_observation


def get_diffable_observation_relationship_values(
        values: Iterable[Any]
) -> List[Dict[str, Any]]:
    """
    Gets a diffable list of dictionaries which excludes observation-specific
    values.

    This makes a lot of assumptions about the data but for our purposes it
    should be fine.
    """
    return [
        {
            attr.key: attr.value for attr in inspect(v).attrs
            if attr.key != "id"
            and not attr.key.endswith("_observation")
            and not attr.key.endswith("_observation_id")
        }
        for v in values
    ]


def pairwise(iterable: Iterable[T]) -> Iterable[T]:
    it = iter(iterable)
    a = next(it, None)
    for b in it:
        yield a, b
        a = b
