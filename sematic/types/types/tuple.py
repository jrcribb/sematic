# Standard Library
import typing
from typing import Any, Iterable, List, Optional, Tuple, Type

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.registry import (
    SummaryOutput,
    register_can_cast,
    register_from_json_encodable,
    register_safe_cast,
    register_to_json_encodable,
    register_to_json_encodable_summary,
)
from sematic.types.serialization import (
    get_json_encodable_summary,
    value_from_json_encodable,
    value_to_json_encodable,
)


@register_safe_cast(tuple)
def _tuple_safe_cast(value: Tuple, type_: Type) -> Tuple[Optional[Tuple], Optional[str]]:
    """
    Casting logic for tuples.

    Ellipsis not supported at this time.
    """
    if not isinstance(value, Iterable):
        return None, "{} not an iterable".format(value)

    element_types = type_.__args__

    if element_types[-1] is ...:
        return None, "Sematic does not support Ellipsis in Tuples yet (...)"

    if len(value) != len(element_types):
        return None, "Expected {} elements, got {}: {}".format(
            len(element_types), len(value), repr(value)
        )

    result: List[Any] = []  # type: ignore

    for element, element_type in zip(value, element_types):
        cast_element, error = safe_cast(element, element_type)
        if error is not None:
            return None, "Cannot cast {} to {}: {}".format(repr(value), type_, error)

        result.append(cast_element)

    return tuple(result), None


@register_to_json_encodable(tuple)
def _tuple_to_json_encodable(value: Tuple, type_: Type) -> List:
    """
    Serialization of tuples
    """
    return [
        value_to_json_encodable(element, element_type)
        for element, element_type in zip(value, type_.__args__)
    ]


@register_from_json_encodable(tuple)
def _tuple_from_json_encodable(value: Tuple, type_: Type) -> Tuple[Any, ...]:
    """Deserialize a tuple."""
    return tuple(
        [
            value_from_json_encodable(element, element_type)
            for element, element_type in zip(value, type_.__args__)
        ]
    )


@register_to_json_encodable_summary(tuple)
def _tuple_to_json_encodable_summary(value: Tuple, type_: Type) -> SummaryOutput:
    """
    Generate summary for the UI.
    """
    summary, blobs = [], {}

    for element, element_type in zip(value, type_.__args__):
        element_summary, element_blobs = get_json_encodable_summary(element, element_type)
        summary.append(element_summary)
        blobs.update(element_blobs)

    return summary, blobs


# Using `tuple` instead of `typing.Tuple` here because
# `typing.Tuple[T].__origin__` is `tuple`
@register_can_cast(tuple)
def can_cast_to_tuple(from_type: typing.Any, to_type: typing.Any):
    """
    Type casting logic for `Tuple[T, U, <more?>]`.

    `from_type` and `to_type` should be subscripted generics
    of the form `Tuple[T, <more?>]`.

    A type of the form `Tuple[T, <more?>]` is castable to `Tuple[U, <more>]` if the
    two tuples have the same arity and the types in the second tuple can all be casted
    to the corresponding types in the first.

    For example `Tuple[int, float]` is castable to `Tuple[float, float]`, but
    `Tuple[int, str]` is not.
    """
    err_prefix = "Can't cast {} to {}:".format(from_type, to_type)

    from_args = typing.get_args(from_type)
    if len(from_args) < 1:
        return False, "{} not a subscripted generic".format(err_prefix)

    to_args = typing.get_args(to_type)
    if len(from_args) != len(to_args):
        return False, "{} they have different arities ({} vs {})".format(
            err_prefix, len(from_args), len(to_args)
        )

    from_origin = typing.get_origin(from_type)
    if not (from_origin is not None and issubclass(from_origin, tuple)):
        return False, "{} not a tuple".format(err_prefix)

    for from_t, to_t in zip(from_args, to_args):
        can_cast, error = can_cast_type(from_t, to_t)
        if can_cast is False:
            return False, "{}: {}".format(err_prefix, error)

    return True, None
