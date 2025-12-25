# pyrefly: ignore-errors

import bson
import pytest
import random
import string
from typing import Any, Dict
from datetime import datetime, timezone
from collections import namedtuple as nt
from dataclasses import dataclass


def test_marshal_dict_empty() -> None:
    inout_test(
        inp={},
        exp=bytes([5, 0, 0, 0, 0]),
    )


def test_marshal_dict_simple_string() -> None:
    inout_test(
        inp={"q": "abc"},
        exp=bytes([16, 0, 0, 0, 2, 113, 0, 4, 0, 0, 0, 97, 98, 99, 0, 0]),
    )


def test_marshal_dict_zero_string() -> None:
    inout_test(
        inp={"q": chr(0)},
        exp=bytes([14, 0, 0, 0, 2, 113, 0, 2, 0, 0, 0, 00, 0, 0]),
    )


def test_marshal_dict_zero_inside_string() -> None:
    inout_test(
        inp={"q": "a\x00c"},
        exp=bytes([16, 0, 0, 0, 2, 113, 0, 4, 0, 0, 0, 97, 0, 99, 0, 0]),
    )


def test_marshal_dict_single_float() -> None:
    inout_test(
        inp={"f": 123.45},
        exp=bytes([0x10, 0, 0, 0, 1, 0x66, 0, 0xCD, 0xCC, 0xCC, 0xCC, 0xCC, 0xDC, 0x5E, 0x40, 0]),
    )


def test_marshal_dict_single_float_empty_key() -> None:
    inout_test(inp={"": 0.0}, exp=b"\x0f\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")


def test_marshal_dict_single_float_cyrillic_infinity() -> None:
    inout_test(
        inp={"вася": float("inf")},
        exp=b"\x17\x00\x00\x00\x01\xd0\xb2\xd0\xb0\xd1\x81\xd1\x8f\x00\x00\x00\x00\x00\x00\x00\xf0\x7f\x00",
    )


def test_marshal_dict_many_floats() -> None:
    inout_test(
        inp={
            "вася": float("0.0"),
            "vasya": float("-0.0"),
            "12345": float("inf"),
            "": float("-inf"),
            "\t": float("nan"),
        },
        exp=b"J\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\xf0\xff\x01\t\x00\x00\x00\x00\x00\x00\x00\xf8\x7f\x0112345\x00\x00\x00\x00\x00\x00\x00\xf0\x7f\x01vasya\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01\xd0\xb2\xd0\xb0\xd1\x81\xd1\x8f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    )


def test_marshal_bool() -> None:
    for v in [False, True]:
        inout_test(
            inp={
                "b": v,
            },
            exp=bytes([9, 0, 0, 0, 8, 98, 0, int(v), 0]),
        )


def test_marshal_bytes() -> None:
    inout_test(
        inp={
            "k": bytes([0, 255, 128]),
        },
        exp=bytes([16, 0, 0, 0, 5, 107, 0, 3, 0, 0, 0, 0, 0, 255, 128, 0]),
    )


def test_marshal_bytearray() -> None:
    inout_test(
        inp={
            "k": bytearray([0, 255, 128]),
        },
        exp=bytearray([16, 0, 0, 0, 5, 107, 0, 3, 0, 0, 0, 0, 0, 255, 128, 0]),
    )


def test_marshal_datetime_epoch() -> None:
    for d in (
        datetime(1970, 1, 1, tzinfo=timezone.utc),
        datetime(1970, 1, 1, 0, 0, 0, 1, tzinfo=timezone.utc),
        datetime(1970, 1, 1, 0, 0, 0, 999, tzinfo=timezone.utc),
    ):
        inout_test(
            inp={
                "k": d,
            },
            exp=bytes([16, 0, 0, 0, 9, 107, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        )


def test_marshal_datetime_millisecond() -> None:
    for ms in 1, 2, 10, 23:
        inout_test(
            inp={
                "k": datetime(1970, 1, 1, 0, 0, 0, ms * 1000, tzinfo=timezone.utc),
            },
            exp=bytes([16, 0, 0, 0, 9, 107, 0, ms, 0, 0, 0, 0, 0, 0, 0, 0]),
        )


def test_marshal_dict_inside_dict() -> None:
    inout_test(
        inp={
            "d1": {},
            "d2": {},
        },
        exp=bytes([23, 0, 0, 0, 3, 100, 49, 0, 5, 0, 0, 0, 0, 3, 100, 50, 0, 5, 0, 0, 0, 0, 0]),
    )


def test_marshal_dict_inside_second_level() -> None:
    inout_test(
        inp={
            "d1": {"d2": {}},
        },
        exp=bytes([23, 0, 0, 0, 3, 100, 49, 0, 14, 0, 0, 0, 3, 100, 50, 0, 5, 0, 0, 0, 0, 0, 0]),
    )


def test_marshal_array_empty() -> None:
    for ctr in list, tuple:
        inout_test(
            inp={
                "ea": ctr(),
            },
            exp=bytes([14, 0, 0, 0, 4, 101, 97, 0, 5, 0, 0, 0, 0, 0]),
        )


def test_marshal_array_single() -> None:
    for ctr in list, tuple:
        inout_test(
            inp={
                "sa": ctr([0x55]),
            },
            exp=bytes([21, 0, 0, 0, 4, 115, 97, 0, 12, 0, 0, 0, 16, 48, 0, 85, 0, 0, 0, 0, 0]),
        )


def test_marshal_array_many() -> None:
    for ctr in list, tuple:
        inout_test(
            inp={
                "ma": ctr(range(5, 16)),
            },
            exp=bytes(
                [
                    92,
                    0,
                    0,
                    0,
                    4,
                    109,
                    97,
                    0,
                    83,
                    0,
                    0,
                    0,
                    16,
                    48,
                    0,
                    5,
                    0,
                    0,
                    0,
                    16,
                    49,
                    0,
                    6,
                    0,
                    0,
                    0,
                    16,
                    50,
                    0,
                    7,
                    0,
                    0,
                    0,
                    16,
                    51,
                    0,
                    8,
                    0,
                    0,
                    0,
                    16,
                    52,
                    0,
                    9,
                    0,
                    0,
                    0,
                    16,
                    53,
                    0,
                    10,
                    0,
                    0,
                    0,
                    16,
                    54,
                    0,
                    11,
                    0,
                    0,
                    0,
                    16,
                    55,
                    0,
                    12,
                    0,
                    0,
                    0,
                    16,
                    56,
                    0,
                    13,
                    0,
                    0,
                    0,
                    16,
                    57,
                    0,
                    14,
                    0,
                    0,
                    0,
                    16,
                    49,
                    48,
                    0,
                    15,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            ),
        )


def test_marshal_array_many_rev() -> None:
    for ctr in list, tuple:
        inout_test(
            inp={
                "ma": ctr(range(5, 16))[::-1],
            },
            exp=bytes(
                [
                    92,
                    0,
                    0,
                    0,
                    4,
                    109,
                    97,
                    0,
                    83,
                    0,
                    0,
                    0,
                    16,
                    48,
                    0,
                    15,
                    0,
                    0,
                    0,
                    16,
                    49,
                    0,
                    14,
                    0,
                    0,
                    0,
                    16,
                    50,
                    0,
                    13,
                    0,
                    0,
                    0,
                    16,
                    51,
                    0,
                    12,
                    0,
                    0,
                    0,
                    16,
                    52,
                    0,
                    11,
                    0,
                    0,
                    0,
                    16,
                    53,
                    0,
                    10,
                    0,
                    0,
                    0,
                    16,
                    54,
                    0,
                    9,
                    0,
                    0,
                    0,
                    16,
                    55,
                    0,
                    8,
                    0,
                    0,
                    0,
                    16,
                    56,
                    0,
                    7,
                    0,
                    0,
                    0,
                    16,
                    57,
                    0,
                    6,
                    0,
                    0,
                    0,
                    16,
                    49,
                    48,
                    0,
                    5,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            ),
        )


def test_unmarshal_dict_empty() -> None:
    unmarshal_inout_test(
        exp={},
        inp=bytes([5, 0, 0, 0, 0]),
    )


def test_unmarshal_dict_simple_string() -> None:
    unmarshal_inout_test(
        exp={"q": "abc"},
        inp=bytes([16, 0, 0, 0, 2, 113, 0, 4, 0, 0, 0, 97, 98, 99, 0, 0]),
    )


def test_unmarshal_dict_zero_string() -> None:
    unmarshal_inout_test(
        exp={"q": chr(0)},
        inp=bytes([14, 0, 0, 0, 2, 113, 0, 2, 0, 0, 0, 00, 0, 0]),
    )


def test_unmarshal_dict_zero_inside_string() -> None:
    unmarshal_inout_test(
        exp={"q": "a\x00c"},
        inp=bytes([16, 0, 0, 0, 2, 113, 0, 4, 0, 0, 0, 97, 0, 99, 0, 0]),
    )


def test_unmarshal_dict_single_float() -> None:
    unmarshal_inout_test(
        exp={"f": 123.45},
        inp=bytes([0x10, 0, 0, 0, 1, 0x66, 0, 0xCD, 0xCC, 0xCC, 0xCC, 0xCC, 0xDC, 0x5E, 0x40, 0]),
    )


def test_unmarshal_dict_single_float_empty_key() -> None:
    unmarshal_inout_test(exp={"": 0.0}, inp=b"\x0f\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")


def test_unmarshal_dict_single_float_cyrillic_infinity() -> None:
    unmarshal_inout_test(
        exp={"вася": float("inf")},
        inp=b"\x17\x00\x00\x00\x01\xd0\xb2\xd0\xb0\xd1\x81\xd1\x8f\x00\x00\x00\x00\x00\x00\x00\xf0\x7f\x00",
    )


def test_unmarshal_dict_many_floats() -> None:
    unmarshal_inout_test(
        exp={
            "вася": float("0.0"),
            "vasya": float("-0.0"),
            "12345": float("inf"),
            "": float("-inf"),
            "\t": float("nan"),
        },
        inp=b"J\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\xf0\xff\x01\t\x00\x00\x00\x00\x00\x00\x00\xf8\x7f\x0112345\x00\x00\x00\x00\x00\x00\x00\xf0\x7f\x01vasya\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01\xd0\xb2\xd0\xb0\xd1\x81\xd1\x8f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        nan_keys=("\t",),
    )


def test_unmarshal_bool() -> None:
    for v in [False, True]:
        unmarshal_inout_test(
            exp={
                "b": v,
            },
            inp=bytes([9, 0, 0, 0, 8, 98, 0, int(v), 0]),
        )


def test_unmarshal_binary() -> None:
    unmarshal_inout_test(
        exp={
            "k": bytes([0, 255, 128]),
        },
        inp=bytes([16, 0, 0, 0, 5, 107, 0, 3, 0, 0, 0, 0, 0, 255, 128, 0]),
    )


def test_unmarshal_datetime_millisecond() -> None:
    for ms in 0, 1, 2, 10, 23:
        unmarshal_inout_test(
            exp={
                "k": datetime(1970, 1, 1, 0, 0, 0, ms * 1000, tzinfo=timezone.utc),
            },
            inp=bytes([16, 0, 0, 0, 9, 107, 0, ms, 0, 0, 0, 0, 0, 0, 0, 0]),
        )


def test_unmarshal_dict_inside_dict() -> None:
    unmarshal_inout_test(
        exp={
            "d1": {},
            "d2": {},
        },
        inp=bytes([23, 0, 0, 0, 3, 100, 49, 0, 5, 0, 0, 0, 0, 3, 100, 50, 0, 5, 0, 0, 0, 0, 0]),
    )


def test_unmarshal_dict_inside_second_level() -> None:
    unmarshal_inout_test(
        exp={
            "d1": {"d2": {}},
        },
        inp=bytes([23, 0, 0, 0, 3, 100, 49, 0, 14, 0, 0, 0, 3, 100, 50, 0, 5, 0, 0, 0, 0, 0, 0]),
    )


def test_unmarshal_array_empty() -> None:
    unmarshal_inout_test(
        exp={
            "ea": [],
        },
        inp=bytes([14, 0, 0, 0, 4, 101, 97, 0, 5, 0, 0, 0, 0, 0]),
    )


def test_unmarshal_array_single() -> None:
    unmarshal_inout_test(
        exp={
            "sa": [0x55],
        },
        inp=bytes([21, 0, 0, 0, 4, 115, 97, 0, 12, 0, 0, 0, 16, 48, 0, 85, 0, 0, 0, 0, 0]),
    )


def test_unmarshal_array_many() -> None:
    unmarshal_inout_test(
        exp={"ma": list(range(5, 16))},
        inp=bytes(
            [
                92,
                0,
                0,
                0,
                4,
                109,
                97,
                0,
                83,
                0,
                0,
                0,
                16,
                48,
                0,
                5,
                0,
                0,
                0,
                16,
                49,
                0,
                6,
                0,
                0,
                0,
                16,
                50,
                0,
                7,
                0,
                0,
                0,
                16,
                51,
                0,
                8,
                0,
                0,
                0,
                16,
                52,
                0,
                9,
                0,
                0,
                0,
                16,
                53,
                0,
                10,
                0,
                0,
                0,
                16,
                54,
                0,
                11,
                0,
                0,
                0,
                16,
                55,
                0,
                12,
                0,
                0,
                0,
                16,
                56,
                0,
                13,
                0,
                0,
                0,
                16,
                57,
                0,
                14,
                0,
                0,
                0,
                16,
                49,
                48,
                0,
                15,
                0,
                0,
                0,
                0,
                0,
            ]
        ),
    )


def test_unmarshal_array_many_rev() -> None:
    unmarshal_inout_test(
        exp={
            "ma": list(range(5, 16))[::-1],
        },
        inp=bytes(
            [
                92,
                0,
                0,
                0,
                4,
                109,
                97,
                0,
                83,
                0,
                0,
                0,
                16,
                48,
                0,
                15,
                0,
                0,
                0,
                16,
                49,
                0,
                14,
                0,
                0,
                0,
                16,
                50,
                0,
                13,
                0,
                0,
                0,
                16,
                51,
                0,
                12,
                0,
                0,
                0,
                16,
                52,
                0,
                11,
                0,
                0,
                0,
                16,
                53,
                0,
                10,
                0,
                0,
                0,
                16,
                54,
                0,
                9,
                0,
                0,
                0,
                16,
                55,
                0,
                8,
                0,
                0,
                0,
                16,
                56,
                0,
                7,
                0,
                0,
                0,
                16,
                57,
                0,
                6,
                0,
                0,
                0,
                16,
                49,
                48,
                0,
                5,
                0,
                0,
                0,
                0,
                0,
            ]
        ),
    )


def test_round_dict_bool() -> None:
    dicts = [
        {
            "prop1": True,
        },
        {
            "prop1": True,
            "prop2": False,
        },
        {"prop1": True, "prop2": None},
    ]
    for d in dicts:
        round_dict_test(d)


def round_dict_string() -> None:
    dicts = [
        {
            "prop1": "abc",
        },
        {
            "prop1": "\x00",
            "prop2": "a\x00",
        },
        {"prop1": "a\x00bc", "prop2": "ab\x00c"},
    ]
    for d in dicts:
        round_dict_test(d)


def test_round_dict_unicode() -> None:
    d = {"p" + str(i): "".join(map(chr, range(1, 2**i))) for i in range(16)}
    round_dict_test(d)


def test_round_dict_small_ints() -> None:
    d = {"p" + str(i): i for i in range(-1000, 1000)}
    round_dict_test(d)


def test_round_dict_around_pos_boundary() -> None:
    d = {"p" + str(i): (1 << 31) + i for i in range(-1000, 1000)}
    round_dict_test(d)


def test_round_dict_around_neg_boundary() -> None:
    d = {"p" + str(i): -(1 << 31) + i for i in range(-1000, 1000)}
    round_dict_test(d)


def test_round_dict_dict() -> None:
    dicts = [
        {
            "prop1": {},
        },
        {
            "prop1": {"k": {"k": "value"}},
            "prop2": False,
        },
        {"prop1": True, "prop2": {"p": None}},
    ]
    for d in dicts:
        round_dict_test(d)


def test_round_dict_list() -> None:
    dicts = [
        {
            "prop1": [],
        },
        {
            "prop1": [12, 34, 65],
            "prop2": [False],
        },
        {"prop1": True, "prop2": []},
    ]
    for d in dicts:
        round_dict_test(d)


def test_round_dict_list_multidim() -> None:
    dicts = [
        {
            "prop1": [],
        },
        {
            "prop1": [12, (34, 65)],
            "prop2": [False, [123, {"kkkkk": [[]]}]],
        },
        {"prop1": True, "prop2": []},
    ]
    for d in dicts:
        round_dict_test(d)


def test_round_dict_tuple() -> None:
    dicts = [
        {
            "prop1": [],
        },
        {
            "prop1": (12, 34, 65),
            "prop2": (False,),
        },
        {"prop1": True, "prop2": ()},
    ]

    for d in dicts:
        round_dict_test(d)


def test_round_dict_bytes() -> None:
    dicts = [
        {
            "prop1": bytes(),
        },
        {"prop1": bytes([12, 34, 65]), "prop2": bytes(1000), "prop3": 100 * bytes([123]), "prop4": bytes(range(256))},
    ]

    for d in dicts:
        round_dict_test(d)


def test_round_dict_bytearray() -> None:
    dicts = [
        {
            "prop1": bytearray(),
        },
        {
            "prop1": bytearray([12, 34, 65]),
            "prop2": bytearray(1000),
            "prop3": 100 * bytearray([123]),
            "prop4": bytearray(range(256)),
        },
    ]

    for d in dicts:
        round_dict_test(d)


def test_round_datetime_epoch() -> None:
    for d in (
        datetime(1970, 1, 1, tzinfo=timezone.utc),
        datetime(1970, 1, 1, 0, 0, 0, 1, tzinfo=timezone.utc),
        datetime(1970, 1, 1, 0, 0, 0, 999, tzinfo=timezone.utc),
    ):
        round_dict_test({"p1": d})


def test_round_list_long() -> None:
    random.seed(42)
    for _ in range(10):
        data = list(range(random.randint(0, 1000)))
        random.shuffle(data)
        round_dict_test({"p1": data})


def test_key_order() -> None:
    random.seed(42)
    base_chars = list(string.ascii_letters)
    random.shuffle(base_chars)
    chars = "".join(base_chars)
    keys = sorted({(chars + chars)[(r := random.randint(0, len(chars))) : r + i % len(chars)] for i in range(5, 100)})
    pairs = [(k, k[::-1]) for k in keys]
    round_dict_test(dict(pairs))
    blob = bson.marshal(dict(pairs))
    for i in range(50):
        sh_pairs = pairs[:]
        random.shuffle(sh_pairs)
        sh_blob = bson.marshal(dict(sh_pairs))
        assert blob == sh_blob
        d = bson.unmarshal(sh_blob)
        assert list(pairs) == list(d.items())


def test_marshal_dict_int32() -> None:
    inout_test(
        inp={
            "v1": 0x7FFFFFFF,
            "v2": -0x80000000,
            "s": "abc",
            "v": 0,
        },
        exp=bytes(
            [
                39,
                0,
                0,
                0,
                2,
                115,
                0,
                4,
                0,
                0,
                0,
                97,
                98,
                99,
                0,
                16,
                118,
                0,
                0,
                0,
                0,
                0,
                16,
                118,
                49,
                0,
                255,
                255,
                255,
                127,
                16,
                118,
                50,
                0,
                0,
                0,
                0,
                128,
                0,
            ]
        ),
    )


def test_marshal_dict_int64() -> None:
    inout_test(
        inp={
            "abc": 0x80000000,
        },
        exp=bytes([18, 0, 0, 0, 18, 97, 98, 99, 0, 0, 0, 0, 128, 0, 0, 0, 0, 0]),
    )


def test_unmarshal_dict_int32() -> None:
    unmarshal_inout_test(
        exp={
            "v1": 0x7FFFFFFF,
            "v2": -0x80000000,
            "s": "abc",
            "v": 0,
        },
        inp=bytes(
            [
                39,
                0,
                0,
                0,
                2,
                115,
                0,
                4,
                0,
                0,
                0,
                97,
                98,
                99,
                0,
                16,
                118,
                0,
                0,
                0,
                0,
                0,
                16,
                118,
                49,
                0,
                255,
                255,
                255,
                127,
                16,
                118,
                50,
                0,
                0,
                0,
                0,
                128,
                0,
            ]
        ),
    )


def test_unmarshal_dict_int64() -> None:
    unmarshal_inout_test(
        exp={
            "abc": 0x80000000,
        },
        inp=bytes([18, 0, 0, 0, 18, 97, 98, 99, 0, 0, 0, 0, 128, 0, 0, 0, 0, 0]),
    )


def test_exceptions() -> None:
    for exc_name in [
        "BsonError",
        "BsonMarshalError",
        "BsonUnsupportedObjectError",
        "BsonUnsupportedKeyError",
        "BsonKeyWithZeroByteError",
        "BsonInputTooBigError",
        "BsonBinaryTooBigError",
        "BsonIntegerTooBigError",
        "BsonStringTooBigError",
        "BsonDocumentTooBigError",
        "BsonCycleDetectedError",
        "BsonUnmarshalError",
        "BsonBrokenDataError",
        "BsonIncorrectSizeError",
        "BsonTooManyDataError",
        "BsonNotEnoughDataError",
        "BsonInvalidElementTypeError",
        "BsonInvalidStringError",
        "BsonStringSizeError",
        "BsonInconsistentStringSizeError",
        "BsonBadStringDataError",
        "BsonBadKeyDataError",
        "BsonRepeatedKeyDataError",
        "BsonInvalidBinarySubtypeError",
        "BsonBadArrayIndexError",
        "MapperConfigError",
    ]:
        assert hasattr(bson, exc_name)
        v = getattr(bson, exc_name)
        assert type(v) is type


def test_exceptions_inheritance() -> None:
    for sub, sup in [
        (bson.MapperConfigError, ValueError),
        (bson.BsonError, ValueError),
        (bson.BsonMarshalError, bson.BsonError),
        (bson.BsonUnsupportedObjectError, bson.BsonMarshalError),
        (bson.BsonUnsupportedKeyError, bson.BsonMarshalError),
        (bson.BsonKeyWithZeroByteError, bson.BsonUnsupportedKeyError),
        (bson.BsonInputTooBigError, bson.BsonMarshalError),
        (bson.BsonBinaryTooBigError, bson.BsonInputTooBigError),
        (bson.BsonIntegerTooBigError, bson.BsonInputTooBigError),
        (bson.BsonStringTooBigError, bson.BsonInputTooBigError),
        (bson.BsonDocumentTooBigError, bson.BsonInputTooBigError),
        (bson.BsonCycleDetectedError, bson.BsonMarshalError),
        (bson.BsonUnmarshalError, bson.BsonError),
        (bson.BsonBrokenDataError, bson.BsonUnmarshalError),
        (bson.BsonIncorrectSizeError, bson.BsonBrokenDataError),
        (bson.BsonTooManyDataError, bson.BsonBrokenDataError),
        (bson.BsonNotEnoughDataError, bson.BsonBrokenDataError),
        (bson.BsonInvalidElementTypeError, bson.BsonBrokenDataError),
        (bson.BsonInvalidStringError, bson.BsonBrokenDataError),
        (bson.BsonStringSizeError, bson.BsonBrokenDataError),
        (bson.BsonInconsistentStringSizeError, bson.BsonBrokenDataError),
        (bson.BsonBadStringDataError, bson.BsonBrokenDataError),
        (bson.BsonBadKeyDataError, bson.BsonBrokenDataError),
        (bson.BsonRepeatedKeyDataError, bson.BsonBrokenDataError),
        (bson.BsonInvalidBinarySubtypeError, bson.BsonBrokenDataError),
        (bson.BsonBadArrayIndexError, bson.BsonBrokenDataError),
    ]:
        print(sub, sup)
        assert sub.__bases__ == (sup,)


def test_marshal_unsupported() -> None:
    for unsupported in [
        object(),
        None,
        "",
        "hello",
        [],
    ]:
        print(unsupported)
        with pytest.raises(bson.BsonUnsupportedObjectError):
            bson.marshal(unsupported)


def test_marshal_unsupported_value() -> None:
    for unsupported in [
        object(),
        set(),
    ]:
        print(unsupported)
        with pytest.raises(bson.BsonUnsupportedObjectError):
            bson.marshal({"key": unsupported})


def test_marshal_unsupported_key() -> None:
    for unsupported in [
        object(),
        frozenset(),
        None,
    ]:
        print(unsupported)
        with pytest.raises(bson.BsonUnsupportedKeyError):
            bson.marshal({unsupported: "value"})


def test_marshal_unsupported_key_unsupported_value() -> None:
    for unsup_key in [
        object(),
        frozenset(),
        None,
    ]:
        for unsup_value in [
            object(),
            frozenset(),
        ]:
            with pytest.raises(bson.BsonUnsupportedKeyError):
                bson.marshal({unsup_key: unsup_value})
            with pytest.raises(bson.BsonUnsupportedKeyError):
                bson.marshal({"": unsup_value, unsup_key: ""})
            with pytest.raises(bson.BsonUnsupportedKeyError):
                bson.marshal({None: unsup_value, unsup_key: ""})


def test_marshal_key_with_zero() -> None:
    for unsupported in [
        chr(0),
        "\x00abc",
        "abc\x00",
        "hello\x00world",
    ]:
        print(unsupported)
        with pytest.raises(bson.BsonKeyWithZeroByteError):
            bson.marshal({unsupported: "value"})


def test_marshal_key_with_zero_unsupported_value() -> None:
    for unsup_key in [
        chr(0),
        "\x00abc",
        "abc\x00",
        "hello\x00world",
    ]:
        for unsup_value in [
            object(),
            frozenset(),
            None,
        ]:
            with pytest.raises(bson.BsonKeyWithZeroByteError):
                bson.marshal({unsup_key: unsup_value})
            with pytest.raises(bson.BsonKeyWithZeroByteError):
                bson.marshal({"": unsup_value, unsup_key: ""})


def test_marshal_unsupported_key_key_with_zero() -> None:
    for key1 in [
        object(),
        frozenset(),
        None,
    ]:
        for key2 in [
            chr(0),
            "\x00abc",
            "abc\x00",
            "hello\x00world",
        ]:
            with pytest.raises(bson.BsonUnsupportedKeyError):
                bson.marshal({key1: "", key2: ""})
            with pytest.raises(bson.BsonUnsupportedKeyError):
                bson.marshal({key2: "", key1: ""})


def test_marshal_cycle_simplest() -> None:
    data: Dict[str, Any] = {}
    data["k"] = data
    with pytest.raises(bson.BsonCycleDetectedError):
        bson.marshal(data)


def test_marshal_cycle_implicit() -> None:
    data1: Dict[str, Any] = {"k0": 123}
    data2: Dict[str, Any] = {"k1": data1, "k0": 234}
    data1["k2"] = data2
    with pytest.raises(bson.BsonCycleDetectedError):
        bson.marshal(data1)
    with pytest.raises(bson.BsonCycleDetectedError):
        bson.marshal(data2)


def test_marshal_cycle_simple_list() -> None:
    data = {"lst": ["", 123, None]}
    data["lst"].append(data["lst"])
    with pytest.raises(bson.BsonCycleDetectedError):
        bson.marshal(data)


def test_marshal_cycle_mixed() -> None:
    data = {"lst": ["", 123, None]}
    data["lst"].append((222, data))
    with pytest.raises(bson.BsonCycleDetectedError):
        bson.marshal(data)


def test_marshal_pseudo_cycle_list() -> None:
    data = {"k1": [123, "hello"]}
    data["k2"] = data["k1"]
    round_dict_test(data)


def test_marshal_pseudo_cycle_map() -> None:
    data = {"k1": [{"hhh": 123}]}
    data["k1"].extend(data["k1"])
    round_dict_test(data)


def inout_test(inp: Any, exp: Any, mapper: Any = None) -> None:
    if mapper is None:
        mapper = bson
    result = mapper.marshal(inp)
    print(repr(result), repr(exp))
    assert type(result) is bytes or type(result) is bytearray  # noqa: E721
    assert len(result) == len(exp)
    assert bytes(result) == exp


def check_types(inp: Any, exp: Any) -> None:
    for k in inp.keys():
        assert type(inp[k]) is type(exp[k])  # noqa: E721
        if type(inp[k]) is dict:  # noqa: E721
            check_types(inp[k], exp[k])


def unmarshal_inout_test(inp: Any, exp: Any, nan_keys: Any = (), mapper: Any = None) -> None:
    print("unmarshal_inout_test-1", inp, exp)
    if mapper is None:
        mapper = bson
    result = mapper.unmarshal(inp)
    print("result", result, type(result))
    assert type(result) is type(exp)
    assert len(result) == len(exp)
    for nk in nan_keys:
        assert nk in result
        assert result[nk] != result[nk]
        assert nk in exp
        assert exp[nk] != exp[nk]
        del result[nk]
        del exp[nk]
    assert result == exp
    check_types(result, exp)


def to_canonical(data: Any) -> Any:
    if type(data) in (list, tuple):
        return [to_canonical(e) for e in data]
    elif type(data) in (bytes, bytearray):
        return bytes(data)
    elif type(data) in (datetime,):
        return datetime(
            data.year,
            data.month,
            data.day,
            data.hour,
            data.minute,
            data.second,
            data.microsecond // 1000 * 1000,
            tzinfo=data.tzinfo,
        )
    elif type(data) is dict:  # noqa: E721
        return {k: to_canonical(e) for k, e in data.items()}
    return data


def round_dict_test(inp: Any, mapper: Any = None) -> None:
    if mapper is None:
        mapper = bson
    result = mapper.unmarshal(mapper.marshal(inp))
    assert type(result) is dict  # noqa: E721
    assert len(result) == len(inp)
    assert result == to_canonical(inp)


def round_dict_with_mapper_test(inp: Any) -> None:
    result = bson.unmarshal(bson.Mapper().marshal(inp))
    assert type(result) is dict  # noqa: E721
    assert len(result) == len(inp)
    assert result == to_canonical(inp)

    result = bson.Mapper().unmarshal(bson.marshal(inp))
    assert type(result) is dict  # noqa: E721
    assert len(result) == len(inp)
    assert result == to_canonical(inp)

    result = bson.Mapper().unmarshal(bson.Mapper().marshal(inp))
    assert type(result) is dict  # noqa: E721
    assert len(result) == len(inp)
    assert result == to_canonical(inp)


def mappers_dont_differ_test(mapper1: Any, mapper2: Any, inputs: Any) -> None:
    for inp in inputs:
        data1 = mapper1.marshal(inp)
        data2 = mapper2.marshal(inp)
        print(data1)
        print(data2)
        assert data1 == data2


def mappers_differ_by_keep_types_dict_test(mapper1: Any, mapper2: Any, inputs: Any) -> None:
    added = b"\x05__metadata__\x00\x04\x00\x00\x00\x80dict"
    for inp in inputs:
        data1 = mapper1.marshal(inp)
        data2 = mapper2.marshal(inp)
        print(repr(data1))
        print(repr(data2))
        assert data1[-1] == data2[-1]
        assert data1[1:-1] == data2[1 : len(data1) - 1]
        assert added == data2[len(data1) - 1 : -1]


def test_exceptions_broken_data_tiny() -> None:
    for broken_data in [
        bytes(),
        bytes([0]),
        bytes([1]),
        bytes([0, 0]),
        bytes([2, 3]),
        bytes([0, 0, 0]),
        bytes([255, 255, 255]),
    ]:
        print(broken_data)
        with pytest.raises(bson.BsonBrokenDataError):
            bson.unmarshal(broken_data)


def test_exceptions_broken_data_too_small_size() -> None:
    for broken_data in [
        bytes([0, 0, 0, 0]),
        bytes([0, 0, 0, 0]),
        bytes([1, 0, 0, 0]),
        bytes([2, 0, 0, 0]),
        bytes([3, 0, 0, 0]),
    ]:
        print(broken_data)
        with pytest.raises(bson.BsonIncorrectSizeError):
            bson.unmarshal(broken_data)


def test_exceptions_broken_data_too_many_data() -> None:
    for broken_data in [
        bytes([5, 0, 0, 0, 0, 0]),
        bytes([5, 0, 0, 0, 0, 5, 0, 0, 0, 0]),
    ]:
        print(broken_data)
        with pytest.raises(bson.BsonTooManyDataError):
            bson.unmarshal(broken_data)


def test_exceptions_broken_data_not_enough_data() -> None:
    for broken_data in [
        bytes([5, 0, 0, 0]),
        bytes([6, 0, 0, 0, 0]),
        bytes([23, 25, 0, 0, 0]),
        bytes([17, 0, 0, 0, 2, 113, 0, 4, 0, 0, 0, 97, 98, 99, 0, 0]),
    ]:
        print(broken_data)
        with pytest.raises(bson.BsonNotEnoughDataError):
            bson.unmarshal(broken_data)


def test_exceptions_broken_data_invalid_element_type() -> None:
    for broken_data in [
        [6, 0, 0, 0, -1, 0],
        [16, 0, 0, 0, -1, 113, 0, 4, 0, 0, 0, 97, 98, 99, 0, 0],
        [9, 0, 0, 0, -1, 98, 0, 0x55, 0],
    ]:
        for i in list(range(20, 127)) + list(range(128, 255)):
            data: list[int] = broken_data[:]
            data[4] = i
            with pytest.raises(bson.BsonInvalidElementTypeError):
                bson.unmarshal(bytes(data))


def test_exceptions_broken_data_invalid_element_type_inside() -> None:
    data = [21, 0, 0, 0, 3, 115, 97, 0, 12, 0, 0, 0, 16, 48, 0, 85, 0, 0, 0, 0, 0]
    for i in range(20, 127):
        data[12] = i
        with pytest.raises(bson.BsonInvalidElementTypeError):
            bson.unmarshal(bytes(data))
    for i in range(128, 255):
        data[12] = i
        with pytest.raises(bson.BsonInvalidElementTypeError):
            bson.unmarshal(bytes(data))


def test_skip_min_max_key() -> None:
    for b in 127, 255:
        assert {} == bson.unmarshal(bytes([7, 0, 0, 0, b, 0, 0]))
        assert {} == bson.unmarshal(bytes([8, 0, 0, 0, b, 32, 0, 0]))
        assert {} == bson.unmarshal(bytes([8, 0, 0, 0, b, 16, 0, 0]))
        assert {} == bson.unmarshal(bytes([8, 0, 0, 0, b, 10, 0, 0]))


def test_skip_objectid() -> None:
    for v in ([0] * 12, [255] * 12, [8, 107, 108, 109, 0, 1] + list(range(1, 7))):
        assert {} == bson.unmarshal(bytes([20, 0, 0, 0, 7, ord("a"), 0] + v + [0]))


def test_skip_decimal128() -> None:
    for v in ([0] * 16, [255] * 16, [8, 107, 108, 109, 0, 1] + list(range(1, 11))):
        assert {} == bson.unmarshal(bytes([24, 0, 0, 0, 19, ord("a"), 0] + v + [0]))


def test_skip_timestamp() -> None:
    for v in ([0] * 8, [255] * 8, [8, 107, 108, 109, 0, 0, 0, 0]):
        assert {} == bson.unmarshal(bytes([16, 0, 0, 0, 17, ord("a"), 0] + v + [0]))


def test_skip_javascript_code() -> None:
    for v in ("", "{}", "\x02k\x00hello"):
        data = v.encode()
        inp = bytes([13 + len(data), 0, 0, 0, 13, 107, 0, 1 + len(data), 0, 0, 0]) + data + bytes([0, 0])
        assert {} == bson.unmarshal(inp)


def test_skip_symbol() -> None:
    for v in ("", "abc", "\x02k\x00hello"):
        data = v.encode()
        inp = bytes([13 + len(data), 0, 0, 0, 14, 107, 0, 1 + len(data), 0, 0, 0]) + data + bytes([0, 0])
        assert {} == bson.unmarshal(inp)


def test_skip_regex() -> None:
    str_input = ("", "abc", r"\d")
    for v1 in str_input:
        for v2 in str_input:
            data1 = v1.encode() + bytes([0])
            data2 = v2.encode() + bytes([0])
            inp = [0, 0, 0, 0, 11] + [115, 97, 0] + list(data1) + list(data2) + [16, 115, 98, 0, 0x55, 0, 0, 0] + [0]
            inp[0] = len(inp)
            assert {"sb": 85} == bson.unmarshal(bytes(inp))


def test_skip_dbpointer() -> None:
    for v in ("", "abc"):
        data = v.encode()
        inp = (
            bytes([25 + len(data), 0, 0, 0, 12, 107, 0, 1 + len(data), 0, 0, 0])
            + data
            + bytes(list(range(12)))
            + bytes([0, 0])
        )
        assert {} == bson.unmarshal(inp)


def test_exceptions_out_of_doc() -> None:
    broken_data = [
        [6, 0, 0, 0, 10, 0],
        [12, 0, 0, 0, 2, 100, 0, 1, 0, 0, 0, 0],
    ]
    for d in broken_data:
        with pytest.raises(bson.BsonBrokenDataError):
            bson.unmarshal(bytes(d))


def test_skip_undefined() -> None:
    inp = [15, 0, 0, 0, 6, 48, 0, 16, 106, 0, 0, 1, 0, 0, 0]
    assert {"j": 256} == bson.unmarshal(bytes(inp))


def test_skip_javascript_code_with_scope() -> None:
    for v in ("", "{}"):
        data = v.encode()
        inp = (
            bytes([18 + len(data), 0, 0, 0, 15, 107, 0, 1 + len(data), 0, 0, 0])
            + data
            + bytes([0])
            + bytes([5, 0, 0, 0, 0])
            + bytes([0])
        )
        assert {} == bson.unmarshal(inp)


def test_exception_broken_object_id() -> None:
    with pytest.raises(bson.BsonBrokenDataError):
        assert {} == bson.unmarshal(bytes([9, 0, 0, 0, 7, 0, 11, 22, 0]))


def test_exceptions_broken_decimal() -> None:
    with pytest.raises(bson.BsonBrokenDataError):
        assert {} == bson.unmarshal(bytes([21, 0, 0, 0, 19, 0] + [0] * 14 + [0]))


def test_exceptions_invalid_binary_subtype() -> None:
    for tp in range(10, 128):
        data = [
            [12, 0, 0, 0, 5, 0, 0, 0, 0, 0, tp, 0],
            [13, 0, 0, 0, 5, 0, 1, 0, 0, 0, tp, 0x55, 0],
        ]
        for d in data:
            with pytest.raises(bson.BsonInvalidBinarySubtypeError):
                bson.unmarshal(bytes(d))


def test_skip_correct_binary_subtype() -> None:
    for tp in range(1, 10):
        assert {} == bson.unmarshal(bytes([12, 0, 0, 0, 5, 0, 0, 0, 0, 0, tp, 0]))
        assert {} == bson.unmarshal(bytes([13, 0, 0, 0, 5, 0, 1, 0, 0, 0, tp, 0x55, 0]))


def test_zero_binary_subtype() -> None:
    assert {"": bytes()} == bson.unmarshal(bytes([12, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0]))
    assert {"": bytes([0x55])} == bson.unmarshal(bytes([13, 0, 0, 0, 5, 0, 1, 0, 0, 0, 0, 0x55, 0]))


def test_skip_user_defined_binary_subtype() -> None:
    for tp in range(128, 256):
        assert {} == bson.unmarshal(bytes([12, 0, 0, 0, 5, 0, 0, 0, 0, 0, tp, 0]))


def test_exceptions_bad_key() -> None:
    with pytest.raises(bson.BsonBadKeyDataError):
        bson.unmarshal(bytes([8, 0, 0, 0, 10, 200, 0, 0]))


def test_exceptions_repeated_key() -> None:
    data = [
        [9, 0, 0, 0, 10, 0, 10, 0, 0],
        [12, 0, 0, 0, 10, 100, 0, 8, 100, 0, 1, 0],
        [15, 0, 0, 0, 10, 100, 0, 10, 101, 0, 8, 100, 0, 1, 0],
    ]
    for d in data:
        with pytest.raises(bson.BsonRepeatedKeyDataError):
            assert {} == bson.unmarshal(bytes(d))


def test_repeated_key_in_subdoc() -> None:
    assert {"": {"": "value"}} == bson.unmarshal(
        bytes([24, 0, 0, 0, 3, 0, 17, 0, 0, 0, 2, 0, 6, 0, 0, 0, 118, 97, 108, 117, 101, 0, 0, 0])
    )


def test_exceptions_string_size_error() -> None:
    data = [
        [13, 0, 0, 0, 2, 113, 0, 0, 0, 0, 0, 0, 0],
        [12, 0, 0, 0, 2, 113, 0, 0, 0, 0, 0, 0],
        [13, 0, 0, 0, 14, 113, 0, 0, 0, 0, 0, 0, 0],
        [12, 0, 0, 0, 14, 113, 0, 0, 0, 0, 0, 0],
    ]
    for d in data:
        with pytest.raises(bson.BsonStringSizeError):
            bson.unmarshal(bytes(d))


def test_exceptions_inconsistent_string_size_error() -> None:
    data = [
        [14, 0, 0, 0, 2, 0, 4, 0, 0, 0, 100, 100, 0, 0],
    ]
    for d in data:
        with pytest.raises(bson.BsonInconsistentStringSizeError):
            bson.unmarshal(bytes(d))


def test_exceptions_bad_string_data() -> None:
    data = [
        [13, 0, 0, 0, 2, 0, 2, 0, 0, 0, 200, 0, 0],
        [13, 0, 0, 0, 14, 0, 2, 0, 0, 0, 200, 0, 0],
    ]
    for d in data:
        with pytest.raises(bson.BsonBadStringDataError):
            bson.unmarshal(bytes(d))


def test_exceptions_bad_cstring_data() -> None:
    bson.unmarshal(bytes([11, 0, 0, 0, 11, 0, 100, 0, 100, 0, 0]))
    data = [
        [11, 0, 0, 0, 11, 0, 200, 0, 100, 0, 0],
        [11, 0, 0, 0, 11, 0, 100, 0, 200, 0, 0],
    ]
    for d in data:
        with pytest.raises(bson.BsonBadStringDataError):
            bson.unmarshal(bytes(d))


def test_exceptions_no_zero_byte_after_string() -> None:
    bson.unmarshal(bytes([14, 0, 0, 0, 2, 97, 98, 0, 1, 0, 0, 0, 0, 0]))
    data = [
        [14, 0, 0, 0, 2, 97, 98, 0, 1, 0, 0, 0, 1, 0],
        [14, 0, 0, 0, 2, 97, 98, 0, 2, 0, 0, 0, 100, 255, 0],
    ]
    for d in data:
        with pytest.raises(bson.BsonBrokenDataError):
            bson.unmarshal(bytes(d))


def test_exceptions_no_zero_byte_after_dict() -> None:
    data = [
        [5, 0, 0, 0, 1],
        [12, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 1],
        [12, 0, 0, 0, 3, 0, 5, 0, 0, 0, 1, 0],
    ]
    for d in data:
        with pytest.raises(bson.BsonBrokenDataError):
            bson.unmarshal(bytes(d))


def test_exceptions_bad_index() -> None:
    data = [
        [15, 0, 0, 0, 4, 0, 8, 0, 0, 0, 10, 100, 0, 0, 0],
        [14, 0, 0, 0, 4, 0, 7, 0, 0, 0, 10, 0, 0, 0],
    ]
    for d in data:
        with pytest.raises(bson.BsonBadArrayIndexError):
            bson.unmarshal(bytes(d))


def test_array_indices_no() -> None:
    assert {"": []} == bson.unmarshal(bytes([12, 0, 0, 0, 4, 0, 5, 0, 0, 0, 0, 0]))


def test_array_indices_just_zero() -> None:
    assert {"": [123]} == bson.unmarshal(bytes([19, 0, 0, 0, 4, 0, 12, 0, 0, 0, 16, 48, 0, 123, 0, 0, 0, 0, 0]))


def test_array_indices_just_one() -> None:
    assert {"": [None, 123]} == bson.unmarshal(bytes([19, 0, 0, 0, 4, 0, 12, 0, 0, 0, 16, 49, 0, 123, 0, 0, 0, 0, 0]))


def test_array_indices_just_five() -> None:
    assert {"": [None, None, None, None, None, 123]} == bson.unmarshal(
        bytes([19, 0, 0, 0, 4, 0, 12, 0, 0, 0, 16, 53, 0, 123, 0, 0, 0, 0, 0])
    )


def test_array_indices_just_ten() -> None:
    assert {"": [None] * 10 + [123]} == bson.unmarshal(
        bytes([20, 0, 0, 0, 4, 0, 13, 0, 0, 0, 16, 49, 48, 0, 123, 0, 0, 0, 0, 0])
    )


def test_array_indices_just_zero_one() -> None:
    assert {"": [123, 32]} == bson.unmarshal(
        bytes([26, 0, 0, 0, 4, 0, 19, 0, 0, 0, 16, 48, 0, 123, 0, 0, 0, 16, 49, 0, 32, 0, 0, 0, 0, 0])
    )


def test_array_indices_just_one_zero() -> None:
    assert {"": [32, 123]} == bson.unmarshal(
        bytes([26, 0, 0, 0, 4, 0, 19, 0, 0, 0, 16, 49, 0, 123, 0, 0, 0, 16, 48, 0, 32, 0, 0, 0, 0, 0])
    )


def test_array_indices_26_3() -> None:
    assert {"": [None, None, None, 32] + [None] * 22 + [123]} == bson.unmarshal(
        bytes([27, 0, 0, 0, 4, 0, 20, 0, 0, 0, 16, 50, 54, 0, 123, 0, 0, 0, 16, 51, 0, 32, 0, 0, 0, 0, 0])
    )


def test_array_indices_just_empty() -> None:
    data = [18, 0, 0, 0, 4, 0, 11, 0, 0, 0, 16, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_empty_zero() -> None:
    data = [25, 0, 0, 0, 4, 0, 18, 0, 0, 0, 16, 0, 123, 0, 0, 0, 16, 48, 0, 32, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_one_empty() -> None:
    data = [25, 0, 0, 0, 4, 0, 18, 0, 0, 0, 16, 49, 0, 32, 0, 0, 0, 16, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_just_space() -> None:
    data = [19, 0, 0, 0, 4, 0, 12, 0, 0, 0, 16, 32, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_space_before() -> None:
    data = [20, 0, 0, 0, 4, 0, 13, 0, 0, 0, 16, 32, 48, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_space_after() -> None:
    data = [20, 0, 0, 0, 4, 0, 13, 0, 0, 0, 16, 48, 32, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_double_zero() -> None:
    data = [20, 0, 0, 0, 4, 0, 13, 0, 0, 0, 16, 48, 48, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_leading_zero() -> None:
    data = [20, 0, 0, 0, 4, 0, 13, 0, 0, 0, 16, 48, 50, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_just_negative() -> None:
    data = [20, 0, 0, 0, 4, 0, 13, 0, 0, 0, 16, 45, 49, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_negative_one() -> None:
    data = [27, 0, 0, 0, 4, 0, 20, 0, 0, 0, 16, 45, 49, 0, 123, 0, 0, 0, 16, 49, 0, 32, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_one_negative() -> None:
    data = [27, 0, 0, 0, 4, 0, 20, 0, 0, 0, 16, 49, 0, 32, 0, 0, 0, 16, 45, 49, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_minus_zero() -> None:
    data = [20, 0, 0, 0, 4, 0, 13, 0, 0, 0, 16, 45, 48, 0, 123, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonBadArrayIndexError):
        bson.unmarshal(bytes(data))


def test_array_indices_zero_zero() -> None:
    data = [26, 0, 0, 0, 4, 0, 19, 0, 0, 0, 16, 48, 0, 32, 0, 0, 0, 16, 48, 0, 32, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonRepeatedKeyDataError):
        bson.unmarshal(bytes(data))


def test_array_indices_one_one() -> None:
    data = [18, 0, 0, 0, 4, 0, 11, 0, 0, 0, 10, 49, 0, 10, 49, 0, 0, 0]
    with pytest.raises(bson.BsonRepeatedKeyDataError):
        bson.unmarshal(bytes(data))


def test_array_indices_zero_one_zero() -> None:
    data = [29, 0, 0, 0, 4, 0, 22, 0, 0, 0, 10, 48, 0, 16, 49, 0, 32, 0, 0, 0, 16, 48, 0, 32, 0, 0, 0, 0, 0]
    with pytest.raises(bson.BsonRepeatedKeyDataError):
        bson.unmarshal(bytes(data))


def test_mapper_defaults() -> None:
    m = bson.Mapper()
    assert not m.python_only


def test_mapper_explicit_python_only() -> None:
    for v in True, False:
        m = bson.Mapper(python_only=v)
        assert m.python_only is v


def test_mapper_assign() -> None:
    m = bson.Mapper()
    for v in True, False:
        with pytest.raises(AttributeError):
            m.python_only = v  # type: ignore


def test_mapper_delete() -> None:
    for v in True, False:
        m = bson.Mapper(python_only=v)
        with pytest.raises(AttributeError):
            del m.python_only
    m = bson.Mapper()
    with pytest.raises(AttributeError):
        del m.python_only


def test_mapper_config_error() -> None:
    for v in True, False, "", None:
        with pytest.raises(bson.MapperConfigError):
            bson.Mapper(something=v)


def test_mapper_positional_parameter() -> None:
    for v in True, False, "", None:
        with pytest.raises(TypeError):
            bson.Mapper(*[v])


def test_round_dict_bool_with_mapper() -> None:
    dicts = [
        {
            "prop1": True,
        },
        {
            "prop1": True,
            "prop2": False,
        },
        {"prop1": True, "prop2": None},
    ]
    for d in dicts:
        round_dict_with_mapper_test(d)


def round_dict_string_with_mapper() -> None:
    dicts = [
        {
            "prop1": "abc",
        },
        {
            "prop1": "\x00",
            "prop2": "a\x00",
        },
        {"prop1": "a\x00bc", "prop2": "ab\x00c"},
    ]
    for d in dicts:
        round_dict_with_mapper_test(d)


def test_round_dict_unicode_with_mapper() -> None:
    d = {"p" + str(i): "".join(map(chr, range(1, 2**i))) for i in range(16)}
    round_dict_with_mapper_test(d)


def test_round_dict_small_ints_with_mapper() -> None:
    d = {"p" + str(i): i for i in range(-1000, 1000)}
    round_dict_with_mapper_test(d)


def test_round_dict_around_pos_boundary_with_mapper() -> None:
    d = {"p" + str(i): (1 << 31) + i for i in range(-1000, 1000)}
    round_dict_with_mapper_test(d)


def test_round_dict_around_neg_boundary_with_mapper() -> None:
    d = {"p" + str(i): -(1 << 31) + i for i in range(-1000, 1000)}
    round_dict_with_mapper_test(d)


def test_round_dict_dict_with_mapper() -> None:
    dicts = [
        {
            "prop1": {},
        },
        {
            "prop1": {"k": {"k": "value"}},
            "prop2": False,
        },
        {"prop1": True, "prop2": {"p": None}},
    ]
    for d in dicts:
        round_dict_with_mapper_test(d)


def test_round_dict_list_with_mapper() -> None:
    dicts = [
        {
            "prop1": [],
        },
        {
            "prop1": [12, 34, 65],
            "prop2": [False],
        },
        {"prop1": True, "prop2": []},
    ]
    for d in dicts:
        round_dict_with_mapper_test(d)


def test_round_dict_list_multidim_with_mapper() -> None:
    dicts = [
        {
            "prop1": [],
        },
        {
            "prop1": [12, (34, 65)],
            "prop2": [False, [123, {"kkkkk": [[]]}]],
        },
        {"prop1": True, "prop2": []},
    ]
    for d in dicts:
        round_dict_with_mapper_test(d)


def test_round_dict_tuple_with_mapper() -> None:
    dicts = [
        {
            "prop1": [],
        },
        {
            "prop1": (12, 34, 65),
            "prop2": (False,),
        },
        {"prop1": True, "prop2": ()},
    ]

    for d in dicts:
        round_dict_with_mapper_test(d)


def test_round_dict_bytes_with_mapper() -> None:
    dicts = [
        {
            "prop1": bytes(),
        },
        {"prop1": bytes([12, 34, 65]), "prop2": bytes(1000), "prop3": 100 * bytes([123]), "prop4": bytes(range(256))},
    ]

    for d in dicts:
        round_dict_with_mapper_test(d)


def test_round_dict_bytearray_with_mapper() -> None:
    dicts = [
        {
            "prop1": bytearray(),
        },
        {
            "prop1": bytearray([12, 34, 65]),
            "prop2": bytearray(1000),
            "prop3": 100 * bytearray([123]),
            "prop4": bytearray(range(256)),
        },
    ]

    for d in dicts:
        round_dict_with_mapper_test(d)


def test_round_datetime_epoch_with_mapper() -> None:
    for d in (
        datetime(1970, 1, 1, tzinfo=timezone.utc),
        datetime(1970, 1, 1, 0, 0, 0, 1, tzinfo=timezone.utc),
        datetime(1970, 1, 1, 0, 0, 0, 999, tzinfo=timezone.utc),
    ):
        round_dict_with_mapper_test({"p1": d})


def test_round_list_long_with_mapper() -> None:
    random.seed(42)
    for _ in range(10):
        data = list(range(random.randint(0, 1000)))
        random.shuffle(data)
        round_dict_with_mapper_test({"p1": data})


def test_key_order_with_mapper() -> None:
    random.seed(42)
    base_chars = list(string.ascii_letters)
    random.shuffle(base_chars)
    chars = "".join(base_chars)
    keys = sorted({(chars + chars)[(r := random.randint(0, len(chars))) : r + i % len(chars)] for i in range(5, 100)})
    pairs = [(k, k[::-1]) for k in keys]
    round_dict_with_mapper_test(dict(pairs))
    blob = bson.marshal(dict(pairs))
    for i in range(50):
        sh_pairs = pairs[:]
        random.shuffle(sh_pairs)
        sh_blob = bson.marshal(dict(sh_pairs))
        assert blob == sh_blob
        d = bson.unmarshal(sh_blob)
        assert list(pairs) == list(d.items())


def test_marshal_pseudo_cycle_list_with_mapper() -> None:
    data = {"k1": [123, "hello"]}
    data["k2"] = data["k1"]
    round_dict_with_mapper_test(data)


def test_marshal_pseudo_cycle_map_with_mapper() -> None:
    data = {"k1": [{"hhh": 123}]}
    data["k1"].extend(data["k1"])
    round_dict_with_mapper_test(data)


def test_skip_min_max_key_with_nonstrict_mapper() -> None:
    for b in 127, 255:
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            assert {} == m.unmarshal(bytes([7, 0, 0, 0, b, 0, 0]))


def test_exceptions_min_max_key_with_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for b in 127, 255:
        with pytest.raises(bson.BsonInvalidElementTypeError):
            m.unmarshal(bytes([7, 0, 0, 0, b, 0, 0]))


def test_skip_decimal128_with_nonstrict_mapper() -> None:
    for v in ([0] * 16, [255] * 16):
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            assert {} == m.unmarshal(bytes([24, 0, 0, 0, 19, ord("a"), 0] + v + [0]))


def test_exceptions_decimal128_with_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for v in ([0] * 16, [255] * 16):
        with pytest.raises(bson.BsonInvalidElementTypeError):
            m.unmarshal(bytes([24, 0, 0, 0, 19, ord("a"), 0] + v + [0]))


def test_skip_timestamp_nonstrict_mapper() -> None:
    for v in ([0] * 8, [255] * 8):
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            assert {} == m.unmarshal(bytes([16, 0, 0, 0, 17, ord("a"), 0] + v + [0]))


def test_exceptions_timestamp_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for v in ([0] * 8, [255] * 8):
        with pytest.raises(bson.BsonInvalidElementTypeError):
            m.unmarshal(bytes([16, 0, 0, 0, 17, ord("a"), 0] + v + [0]))


def test_skip_javascript_code_nonstrict_mapper() -> None:
    for v in ("", "{}"):
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            data = v.encode()
            inp = bytes([13 + len(data), 0, 0, 0, 13, 107, 0, 1 + len(data), 0, 0, 0]) + data + bytes([0, 0])
            assert {} == m.unmarshal(inp)


def test_exceptions_javascript_code_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for v in ("", "{}"):
        data = v.encode()
        inp = bytes([13 + len(data), 0, 0, 0, 13, 107, 0, 1 + len(data), 0, 0, 0]) + data + bytes([0, 0])
        with pytest.raises(bson.BsonInvalidElementTypeError):
            m.unmarshal(inp)


def test_skip_javascript_code_with_scope_non_strict_mapper() -> None:
    for v in ("", "{}"):
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            data = v.encode()
            inp = (
                bytes([18 + len(data), 0, 0, 0, 15, 107, 0, 1 + len(data), 0, 0, 0])
                + data
                + bytes([0])
                + bytes([5, 0, 0, 0, 0])
                + bytes([0])
            )
            assert {} == m.unmarshal(inp)


def test_skip_javascript_code_with_scope_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for v in ("", "{}"):
        data = v.encode()
        inp = (
            bytes([18 + len(data), 0, 0, 0, 15, 107, 0, 1 + len(data), 0, 0, 0])
            + data
            + bytes([0])
            + bytes([5, 0, 0, 0, 0])
            + bytes([0])
        )
        with pytest.raises(bson.BsonInvalidElementTypeError):
            m.unmarshal(inp)


def test_skip_symbol_non_strict_mapper() -> None:
    for v in ("", "abc", "\x02k\x00hello"):
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            data = v.encode()
            inp = bytes([13 + len(data), 0, 0, 0, 14, 107, 0, 1 + len(data), 0, 0, 0]) + data + bytes([0, 0])
            assert {} == m.unmarshal(inp)


def test_exceptions_symbol_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for v in ("", "abc", "\x02k\x00hello"):
        data = v.encode()
        inp = bytes([13 + len(data), 0, 0, 0, 14, 107, 0, 1 + len(data), 0, 0, 0]) + data + bytes([0, 0])
        with pytest.raises(bson.BsonInvalidElementTypeError):
            m.unmarshal(inp)


def test_skip_dbpointer_non_strict_mapper() -> None:
    for v in ("", "abc"):
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            data = v.encode()
            inp = (
                bytes([25 + len(data), 0, 0, 0, 12, 107, 0, 1 + len(data), 0, 0, 0])
                + data
                + bytes(list(range(12)))
                + bytes([0, 0])
            )
            assert {} == m.unmarshal(inp)


def test_exceptions_dbpointer_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for v in ("", "abc"):
        data = v.encode()
        inp = (
            bytes([25 + len(data), 0, 0, 0, 12, 107, 0, 1 + len(data), 0, 0, 0])
            + data
            + bytes(list(range(12)))
            + bytes([0, 0])
        )
        with pytest.raises(bson.BsonInvalidElementTypeError):
            m.unmarshal(inp)


def test_skip_regex_non_strict_mapper() -> None:
    str_input = ("", "abc", r"\d")
    for v1 in str_input:
        for v2 in str_input:
            for m in (bson.Mapper(), bson.Mapper(python_only=False)):
                data1 = v1.encode() + bytes([0])
                data2 = v2.encode() + bytes([0])
                inp = (
                    [0, 0, 0, 0, 11] + [115, 97, 0] + list(data1) + list(data2) + [16, 115, 98, 0, 0x55, 0, 0, 0] + [0]
                )
                inp[0] = len(inp)
                assert {"sb": 85} == m.unmarshal(bytes(inp))


def test_exceptions_regex_strict_mapper() -> None:
    str_input = ("", "abc", r"\d")
    m = bson.Mapper(python_only=True)
    for v1 in str_input:
        for v2 in str_input:
            data1 = v1.encode() + bytes([0])
            data2 = v2.encode() + bytes([0])
            inp = [0, 0, 0, 0, 11] + [115, 97, 0] + list(data1) + list(data2) + [16, 115, 98, 0, 0x55, 0, 0, 0] + [0]
            inp[0] = len(inp)
        with pytest.raises(bson.BsonInvalidElementTypeError):
            m.unmarshal(bytes(inp))


def test_skip_objectid_non_strict_mapper() -> None:
    for v in ([0] * 12, [255] * 12, [8, 107, 108, 109, 0, 1] + list(range(1, 7))):
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            assert {} == m.unmarshal(bytes([20, 0, 0, 0, 7, ord("a"), 0] + v + [0]))


def test_skip_objectid_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for v in ([0] * 12, [255] * 12, [8, 107, 108, 109, 0, 1] + list(range(1, 7))):
        with pytest.raises(bson.BsonInvalidElementTypeError):
            m.unmarshal(bytes([20, 0, 0, 0, 7, ord("a"), 0] + v + [0]))


def test_skip_undefined_non_strict_mapper() -> None:
    inp = [15, 0, 0, 0, 6, 48, 0, 16, 106, 0, 0, 1, 0, 0, 0]
    for m in (bson.Mapper(), bson.Mapper(python_only=False)):
        assert {"j": 256} == m.unmarshal(bytes(inp))


def test_skip_undefined_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    inp = [15, 0, 0, 0, 6, 48, 0, 16, 106, 0, 0, 1, 0, 0, 0]
    with pytest.raises(bson.BsonInvalidElementTypeError):
        m.unmarshal(bytes(inp))


def test_exceptions_invalid_binary_subtype_all_mappers() -> None:
    for tp in range(10, 128):
        data = [
            [12, 0, 0, 0, 5, 0, 0, 0, 0, 0, tp, 0],
            [13, 0, 0, 0, 5, 0, 1, 0, 0, 0, tp, 0x55, 0],
        ]
        for d in data:
            for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
                with pytest.raises(bson.BsonInvalidBinarySubtypeError):
                    m.unmarshal(bytes(d))


def test_skip_correct_binary_subtype_non_strict_mapper() -> None:
    for tp in range(1, 10):
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            assert {} == m.unmarshal(bytes([12, 0, 0, 0, 5, 0, 0, 0, 0, 0, tp, 0]))
            assert {} == m.unmarshal(bytes([13, 0, 0, 0, 5, 0, 1, 0, 0, 0, tp, 0x55, 0]))


def test_skip_correct_binary_subtype_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for tp in range(1, 10):
        data = [
            [12, 0, 0, 0, 5, 0, 0, 0, 0, 0, tp, 0],
            [13, 0, 0, 0, 5, 0, 1, 0, 0, 0, tp, 0x55, 0],
        ]
        for d in data:
            with pytest.raises(bson.BsonInvalidBinarySubtypeError):
                m.unmarshal(bytes(d))


def test_zero_binary_subtype_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"": bytes()} == m.unmarshal(bytes([12, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0]))
        assert {"": bytes([0x55])} == m.unmarshal(bytes([13, 0, 0, 0, 5, 0, 1, 0, 0, 0, 0, 0x55, 0]))


def test_skip_user_defined_binary_subtype_non_strict_mapper() -> None:
    for tp in range(128, 256):
        for m in (bson.Mapper(), bson.Mapper(python_only=False)):
            assert {} == m.unmarshal(bytes([12, 0, 0, 0, 5, 0, 0, 0, 0, 0, tp, 0]))


def test_skip_user_defined_binary_subtype_strict_mapper() -> None:
    m = bson.Mapper(python_only=True)
    for tp in range(128, 256):
        with pytest.raises(bson.BsonInvalidBinarySubtypeError):
            m.unmarshal(bytes([12, 0, 0, 0, 5, 0, 0, 0, 0, 0, tp, 0]))


def test_array_indices_no_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"": []} == m.unmarshal(bytes([12, 0, 0, 0, 4, 0, 5, 0, 0, 0, 0, 0]))


def test_array_indices_just_zero_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"": [123]} == m.unmarshal(bytes([19, 0, 0, 0, 4, 0, 12, 0, 0, 0, 16, 48, 0, 123, 0, 0, 0, 0, 0]))


def test_array_indices_just_one_non_strict_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False)):
        assert {"": [None, 123]} == m.unmarshal(bytes([19, 0, 0, 0, 4, 0, 12, 0, 0, 0, 16, 49, 0, 123, 0, 0, 0, 0, 0]))


def test_array_indices_just_one_strict_mappers() -> None:
    m = bson.Mapper(python_only=True)

    with pytest.raises(bson.BsonInvalidArrayError):
        assert {"": [None, 123]} == m.unmarshal(bytes([19, 0, 0, 0, 4, 0, 12, 0, 0, 0, 16, 49, 0, 123, 0, 0, 0, 0, 0]))


def test_array_indices_just_ten_non_strict_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False)):
        assert {"": [None] * 10 + [123]} == m.unmarshal(
            bytes([20, 0, 0, 0, 4, 0, 13, 0, 0, 0, 16, 49, 48, 0, 123, 0, 0, 0, 0, 0])
        )


def test_array_indices_just_ten_strict_mappers() -> None:
    m = bson.Mapper(python_only=True)

    with pytest.raises(bson.BsonInvalidArrayError):
        assert {"": [None] * 10 + [123]} == m.unmarshal(
            bytes([20, 0, 0, 0, 4, 0, 13, 0, 0, 0, 16, 49, 48, 0, 123, 0, 0, 0, 0, 0])
        )


def test_array_indices_just_zero_one_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"": [123, 32]} == bson.unmarshal(
            bytes([26, 0, 0, 0, 4, 0, 19, 0, 0, 0, 16, 48, 0, 123, 0, 0, 0, 16, 49, 0, 32, 0, 0, 0, 0, 0])
        )


def test_array_indices_just_one_zero_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"": [32, 123]} == bson.unmarshal(
            bytes([26, 0, 0, 0, 4, 0, 19, 0, 0, 0, 16, 49, 0, 123, 0, 0, 0, 16, 48, 0, 32, 0, 0, 0, 0, 0])
        )


def test_unmarshal_int64_zero_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"abc": 0} == bson.unmarshal(
            bytes(
                [18, 0, 0, 0, 18, 97, 98, 99, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            )
        )


def test_unmarshal_int64_123_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"abc": 123} == bson.unmarshal(
            bytes(
                [18, 0, 0, 0, 18, 97, 98, 99, 0, 123, 0, 0, 0, 0, 0, 0, 0, 0],
            )
        )


def test_unmarshal_int64_max_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"abc": 0x7FFFFFFFFFFFFFFF} == bson.unmarshal(
            bytes(
                [18, 0, 0, 0, 18, 97, 98, 99, 0, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x7F, 0],
            )
        )


def test_unmarshal_int64_min_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"abc": -0x8000000000000000} == bson.unmarshal(
            bytes(
                [18, 0, 0, 0, 18, 97, 98, 99, 0, 0, 0, 0, 0, 0, 0, 0, 0x80, 0],
            )
        )


def test_unmarshal_int64_m1_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        assert {"abc": -1} == bson.unmarshal(
            bytes(
                [18, 0, 0, 0, 18, 97, 98, 99, 0, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0],
            )
        )


def test_unmarshal_all_bool_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(python_only=False), bson.Mapper(python_only=True)):
        for v in range(256):
            assert {"b": v != 0} == bson.unmarshal(
                bytes(
                    [9, 0, 0, 0, 8, 98, 0, v, 0],
                )
            )


def test_mapper_defaults_keep_types() -> None:
    m = bson.Mapper()
    assert not m.keep_types
    assert not m.python_only


def test_mapper_explicit_keep_types() -> None:
    for v in True, False:
        m = bson.Mapper(keep_types=v)
        assert m.keep_types is v
        assert not m.python_only


def test_mapper_assign_keep_types() -> None:
    m = bson.Mapper()
    for v in True, False:
        with pytest.raises(AttributeError):
            m.keep_types = v  # type: ignore


def test_mapper_delete_keep_types() -> None:
    for v in True, False:
        m = bson.Mapper(keep_types=v)
        with pytest.raises(AttributeError):
            del m.keep_types
    m = bson.Mapper()
    with pytest.raises(AttributeError):
        del m.keep_types


def test_mapper_config_error_keep_types() -> None:
    for v in True, False, "", None:
        with pytest.raises(bson.MapperConfigError):
            bson.Mapper(something=v)


def test_mapper_positional_parameter_keep_types() -> None:
    for v in True, False, "", None:
        with pytest.raises(TypeError):
            bson.Mapper(*[v])


def test_marshal_dict_empty_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={},
            exp=bytes([5, 0, 0, 0, 0]),
            mapper=m,
        )


def test_marshal_dict_simple_string_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={"q": "abc"},
            exp=bytes([16, 0, 0, 0, 2, 113, 0, 4, 0, 0, 0, 97, 98, 99, 0, 0]),
            mapper=m,
        )


def test_marshal_dict_zero_string_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={"q": chr(0)},
            exp=bytes([14, 0, 0, 0, 2, 113, 0, 2, 0, 0, 0, 00, 0, 0]),
            mapper=m,
        )


def test_marshal_dict_zero_inside_string_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={"q": "a\x00c"},
            exp=bytes([16, 0, 0, 0, 2, 113, 0, 4, 0, 0, 0, 97, 0, 99, 0, 0]),
            mapper=m,
        )


def test_marshal_dict_single_float_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={"f": 123.45},
            exp=bytes([0x10, 0, 0, 0, 1, 0x66, 0, 0xCD, 0xCC, 0xCC, 0xCC, 0xCC, 0xDC, 0x5E, 0x40, 0]),
            mapper=m,
        )


def test_marshal_dict_single_float_empty_key_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={"": 0.0},
            exp=b"\x0f\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            mapper=m,
        )


def test_marshal_dict_single_float_cyrillic_infinity_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={"вася": float("inf")},
            exp=b"\x17\x00\x00\x00\x01\xd0\xb2\xd0\xb0\xd1\x81\xd1\x8f\x00\x00\x00\x00\x00\x00\x00\xf0\x7f\x00",
            mapper=m,
        )


def test_marshal_dict_many_floats_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={
                "вася": float("0.0"),
                "vasya": float("-0.0"),
                "12345": float("inf"),
                "": float("-inf"),
                "\t": float("nan"),
            },
            exp=b"J\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\xf0\xff\x01\t\x00\x00\x00\x00\x00\x00\x00\xf8\x7f\x0112345\x00\x00\x00\x00\x00\x00\x00\xf0\x7f\x01vasya\x00\x00\x00\x00\x00\x00\x00\x00\x80\x01\xd0\xb2\xd0\xb0\xd1\x81\xd1\x8f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            mapper=m,
        )


def test_marshal_bool_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        for v in [False, True]:
            inout_test(
                inp={
                    "b": v,
                },
                exp=bytes([9, 0, 0, 0, 8, 98, 0, int(v), 0]),
                mapper=m,
            )


def test_marshal_bytes_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={
                "k": bytes([0, 255, 128]),
            },
            exp=bytes([16, 0, 0, 0, 5, 107, 0, 3, 0, 0, 0, 0, 0, 255, 128, 0]),
            mapper=m,
        )


def test_marshal_bytearray_not_keeping() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False)):
        inout_test(
            inp={
                "k": bytearray([0, 255, 128]),
            },
            exp=bytearray([16, 0, 0, 0, 5, 107, 0, 3, 0, 0, 0, 0, 0, 255, 128, 0]),
            mapper=m,
        )


def test_marshal_bytearray_keeping() -> None:
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={
            "k": bytearray([0, 255, 128]),
        },
        exp=bytearray(
            [
                44,
                0,
                0,
                0,
                5,
                107,
                0,
                3,
                0,
                0,
                0,
                0,
                0,
                255,
                128,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                9,
                0,
                0,
                0,
                128,
                98,
                121,
                116,
                101,
                97,
                114,
                114,
                97,
                121,
                0,
            ]
        ),
        mapper=m,
    )


def test_marshal_datetime_epoch_all_mappers() -> None:
    for d in (
        datetime(1970, 1, 1, tzinfo=timezone.utc),
        datetime(1970, 1, 1, 0, 0, 0, 1, tzinfo=timezone.utc),
        datetime(1970, 1, 1, 0, 0, 0, 999, tzinfo=timezone.utc),
    ):
        for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
            inout_test(
                inp={
                    "k": d,
                },
                exp=bytes([16, 0, 0, 0, 9, 107, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                mapper=m,
            )


def test_marshal_datetime_millisecond_all_mappers() -> None:
    for ms in 1, 2, 10, 23:
        for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
            inout_test(
                inp={
                    "k": datetime(1970, 1, 1, 0, 0, 0, ms * 1000, tzinfo=timezone.utc),
                },
                exp=bytes([16, 0, 0, 0, 9, 107, 0, ms, 0, 0, 0, 0, 0, 0, 0, 0]),
                mapper=m,
            )


def test_marshal_dict_inside_dict_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={
                "d1": {},
                "d2": {},
            },
            exp=bytes([23, 0, 0, 0, 3, 100, 49, 0, 5, 0, 0, 0, 0, 3, 100, 50, 0, 5, 0, 0, 0, 0, 0]),
            mapper=m,
        )


def test_marshal_dict_inside_second_level_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        inout_test(
            inp={
                "d1": {"d2": {}},
            },
            exp=bytes([23, 0, 0, 0, 3, 100, 49, 0, 14, 0, 0, 0, 3, 100, 50, 0, 5, 0, 0, 0, 0, 0, 0]),
            mapper=m,
        )


def test_marshal_array_empty_not_keeping() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False)):
        for ctr in list, tuple:
            inout_test(
                inp={
                    "ea": ctr(),
                },
                exp=bytes([14, 0, 0, 0, 4, 101, 97, 0, 5, 0, 0, 0, 0, 0]),
                mapper=m,
            )


def test_marshal_list_empty_keeping() -> None:
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={
            "ea": [],
        },
        exp=bytes([14, 0, 0, 0, 4, 101, 97, 0, 5, 0, 0, 0, 0, 0]),
        mapper=m,
    )


def test_marshal_tuple_empty_keeping() -> None:
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={
            "ea": (),
        },
        exp=bytes(
            [
                38,
                0,
                0,
                0,
                4,
                101,
                97,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                5,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                0,
            ]
        ),
        mapper=m,
    )


def test_marshal_two_tuples_keeping() -> None:
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={
            "ea2": (),
            "ea1": (123,),
        },
        exp=bytes(
            [
                62,
                0,
                0,
                0,
                4,
                101,
                97,
                49,
                0,
                12,
                0,
                0,
                0,
                16,
                48,
                0,
                123,
                0,
                0,
                0,
                0,
                4,
                101,
                97,
                50,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                11,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                58,
                116,
                117,
                112,
                108,
                101,
                0,
            ]
        ),
        mapper=m,
    )


def test_unmarshal_dict_empty_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={},
            inp=bytes([5, 0, 0, 0, 0]),
            mapper=m,
        )


def test_unmarshal_dict_simple_string_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"q": "abc"},
            inp=bytes([16, 0, 0, 0, 2, 113, 0, 4, 0, 0, 0, 97, 98, 99, 0, 0]),
            mapper=m,
        )


def test_unmarshal_dict_zero_string_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"q": chr(0)},
            inp=bytes([14, 0, 0, 0, 2, 113, 0, 2, 0, 0, 0, 00, 0, 0]),
            mapper=m,
        )


def test_unmarshal_dict_zero_inside_string_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"q": "a\x00c"},
            inp=bytes([16, 0, 0, 0, 2, 113, 0, 4, 0, 0, 0, 97, 0, 99, 0, 0]),
            mapper=m,
        )


def test_unmarshal_dict_single_float_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"f": 123.45},
            inp=bytes([0x10, 0, 0, 0, 1, 0x66, 0, 0xCD, 0xCC, 0xCC, 0xCC, 0xCC, 0xDC, 0x5E, 0x40, 0]),
            mapper=m,
        )


def test_unmarshal_dict_single_float_empty_key_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"": 0.0},
            inp=b"\x0f\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            mapper=m,
        )


def test_unmarshal_dict_single_float_cyrillic_infinity_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"вася": float("inf")},
            inp=b"\x17\x00\x00\x00\x01\xd0\xb2\xd0\xb0\xd1\x81\xd1\x8f\x00\x00\x00\x00\x00\x00\x00\xf0\x7f\x00",
            mapper=m,
        )


def test_unmarshal_dict_many_floats_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={
                "вася": float("0.0"),
                "vasya": float("-0.0"),
                "12345": float("inf"),
                "": float("-inf"),
            },
            inp=bytes(
                [
                    63,
                    0,
                    0,
                    0,
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    240,
                    255,
                    1,
                    49,
                    50,
                    51,
                    52,
                    53,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    240,
                    127,
                    1,
                    118,
                    97,
                    115,
                    121,
                    97,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    128,
                    1,
                    208,
                    178,
                    208,
                    176,
                    209,
                    129,
                    209,
                    143,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            ),
            mapper=m,
        )


def test_unmarshal_bool_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        for v in [False, True]:
            unmarshal_inout_test(
                exp={
                    "b": v,
                },
                inp=bytes([9, 0, 0, 0, 8, 98, 0, int(v), 0]),
                mapper=m,
            )


def test_unmarshal_bytes_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={
                "k": bytes([0, 255, 128]),
            },
            inp=bytes([16, 0, 0, 0, 5, 107, 0, 3, 0, 0, 0, 0, 0, 255, 128, 0]),
            mapper=m,
        )


def test_unmarshal_bytearray_not_keeping() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False)):
        unmarshal_inout_test(
            exp={
                "k": bytes([0, 255, 128]),
            },
            inp=bytearray(
                [
                    44,
                    0,
                    0,
                    0,
                    5,
                    107,
                    0,
                    3,
                    0,
                    0,
                    0,
                    0,
                    0,
                    255,
                    128,
                    5,
                    95,
                    95,
                    109,
                    101,
                    116,
                    97,
                    100,
                    97,
                    116,
                    97,
                    95,
                    95,
                    0,
                    9,
                    0,
                    0,
                    0,
                    128,
                    98,
                    121,
                    116,
                    101,
                    97,
                    114,
                    114,
                    97,
                    121,
                    0,
                ]
            ),
            mapper=m,
        )


def test_unmarshal_bytearray_keeping() -> None:
    m = bson.Mapper(keep_types=True)
    unmarshal_inout_test(
        exp={
            "k": bytearray([0, 255, 128]),
        },
        inp=bytearray(
            [
                44,
                0,
                0,
                0,
                5,
                107,
                0,
                3,
                0,
                0,
                0,
                0,
                0,
                255,
                128,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                9,
                0,
                0,
                0,
                128,
                98,
                121,
                116,
                101,
                97,
                114,
                114,
                97,
                121,
                0,
            ]
        ),
        mapper=m,
    )


def test_unmarshal_datetime_epoch_all_mappers() -> None:
    d = datetime(1970, 1, 1, tzinfo=timezone.utc)
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={
                "k": d,
            },
            inp=bytes([16, 0, 0, 0, 9, 107, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
            mapper=m,
        )


def test_unmarshal_datetime_millisecond_all_mappers() -> None:
    for ms in 1, 2, 10, 23:
        for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
            unmarshal_inout_test(
                exp={
                    "k": datetime(1970, 1, 1, 0, 0, 0, ms * 1000, tzinfo=timezone.utc),
                },
                inp=bytes([16, 0, 0, 0, 9, 107, 0, ms, 0, 0, 0, 0, 0, 0, 0, 0]),
                mapper=m,
            )


def test_unmarshal_dict_inside_dict_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={
                "d1": {},
                "d2": {},
            },
            inp=bytes([23, 0, 0, 0, 3, 100, 49, 0, 5, 0, 0, 0, 0, 3, 100, 50, 0, 5, 0, 0, 0, 0, 0]),
            mapper=m,
        )


def test_unmarshal_dict_inside_second_level_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={
                "d1": {"d2": {}},
            },
            inp=bytes([23, 0, 0, 0, 3, 100, 49, 0, 14, 0, 0, 0, 3, 100, 50, 0, 5, 0, 0, 0, 0, 0, 0]),
            mapper=m,
        )


def test_unmarshal_list_empty_all_mappers() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={
                "ea": [],
            },
            inp=bytes([14, 0, 0, 0, 4, 101, 97, 0, 5, 0, 0, 0, 0, 0]),
            mapper=m,
        )


def test_unmarshal_tuple_empty_not_keeping() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False)):
        unmarshal_inout_test(
            exp={
                "ea": [],
            },
            inp=bytes(
                [
                    38,
                    0,
                    0,
                    0,
                    4,
                    101,
                    97,
                    0,
                    5,
                    0,
                    0,
                    0,
                    0,
                    5,
                    95,
                    95,
                    109,
                    101,
                    116,
                    97,
                    100,
                    97,
                    116,
                    97,
                    95,
                    95,
                    0,
                    5,
                    0,
                    0,
                    0,
                    128,
                    116,
                    117,
                    112,
                    108,
                    101,
                    0,
                ]
            ),
            mapper=m,
        )


def test_unmarshal_tuple_empty_keeping() -> None:
    m = bson.Mapper(keep_types=True)
    unmarshal_inout_test(
        exp={
            "ea": (),
        },
        inp=bytes(
            [
                38,
                0,
                0,
                0,
                4,
                101,
                97,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                5,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                0,
            ]
        ),
        mapper=m,
    )


def test_unmarshal_two_tuples_keeping() -> None:
    m = bson.Mapper(keep_types=True)
    unmarshal_inout_test(
        exp={
            "ea2": (),
            "ea1": (123,),
        },
        inp=bytes(
            [
                62,
                0,
                0,
                0,
                4,
                101,
                97,
                49,
                0,
                12,
                0,
                0,
                0,
                16,
                48,
                0,
                123,
                0,
                0,
                0,
                0,
                4,
                101,
                97,
                50,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                11,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                58,
                116,
                117,
                112,
                108,
                101,
                0,
            ]
        ),
        mapper=m,
    )


def test_marshal_inside_array() -> None:
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={
            "abc": [(), [], 123, [], ()],
        },
        exp=bytes(
            [
                87,
                0,
                0,
                0,
                4,
                97,
                98,
                99,
                0,
                77,
                0,
                0,
                0,
                4,
                48,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                49,
                0,
                5,
                0,
                0,
                0,
                0,
                16,
                50,
                0,
                123,
                0,
                0,
                0,
                4,
                51,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                52,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                14,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                58,
                58,
                58,
                58,
                116,
                117,
                112,
                108,
                101,
                0,
                0,
            ]
        ),
        mapper=m,
    )


def test_unmarshal_inside_array() -> None:
    m = bson.Mapper(keep_types=True)
    unmarshal_inout_test(
        exp={
            "abc": [(), [], 123, [], ()],
        },
        inp=bytes(
            [
                87,
                0,
                0,
                0,
                4,
                97,
                98,
                99,
                0,
                77,
                0,
                0,
                0,
                4,
                48,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                49,
                0,
                5,
                0,
                0,
                0,
                0,
                16,
                50,
                0,
                123,
                0,
                0,
                0,
                4,
                51,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                52,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                14,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                58,
                58,
                58,
                58,
                116,
                117,
                112,
                108,
                101,
                0,
                0,
            ]
        ),
        mapper=m,
    )


def test_marshal_inside_array_many() -> None:
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={
            "abc": [(), [], 123, [], (), bytes(), bytearray(), "abc", True, None, bytearray(), bytes()],
        },
        exp=bytes(
            [
                164,
                0,
                0,
                0,
                4,
                97,
                98,
                99,
                0,
                154,
                0,
                0,
                0,
                4,
                48,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                49,
                0,
                5,
                0,
                0,
                0,
                0,
                16,
                50,
                0,
                123,
                0,
                0,
                0,
                4,
                51,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                52,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                53,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                54,
                0,
                0,
                0,
                0,
                0,
                0,
                2,
                55,
                0,
                4,
                0,
                0,
                0,
                97,
                98,
                99,
                0,
                8,
                56,
                0,
                1,
                10,
                57,
                0,
                5,
                49,
                48,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                49,
                49,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                39,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                58,
                58,
                58,
                58,
                116,
                117,
                112,
                108,
                101,
                58,
                58,
                98,
                121,
                116,
                101,
                97,
                114,
                114,
                97,
                121,
                58,
                58,
                58,
                58,
                98,
                121,
                116,
                101,
                97,
                114,
                114,
                97,
                121,
                58,
                0,
                0,
            ]
        ),
        mapper=m,
    )


def test_unmarshal_inside_array_many() -> None:
    m = bson.Mapper(keep_types=True)
    unmarshal_inout_test(
        exp={
            "abc": [(), [], 123, [], (), bytes(), bytearray(), "abc", True, None, bytearray(), bytes()],
        },
        inp=bytes(
            [
                164,
                0,
                0,
                0,
                4,
                97,
                98,
                99,
                0,
                154,
                0,
                0,
                0,
                4,
                48,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                49,
                0,
                5,
                0,
                0,
                0,
                0,
                16,
                50,
                0,
                123,
                0,
                0,
                0,
                4,
                51,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                52,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                53,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                54,
                0,
                0,
                0,
                0,
                0,
                0,
                2,
                55,
                0,
                4,
                0,
                0,
                0,
                97,
                98,
                99,
                0,
                8,
                56,
                0,
                1,
                10,
                57,
                0,
                5,
                49,
                48,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                49,
                49,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                39,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                58,
                58,
                58,
                58,
                116,
                117,
                112,
                108,
                101,
                58,
                58,
                98,
                121,
                116,
                101,
                97,
                114,
                114,
                97,
                121,
                58,
                58,
                58,
                58,
                98,
                121,
                116,
                101,
                97,
                114,
                114,
                97,
                121,
                58,
                0,
                0,
            ]
        ),
        mapper=m,
    )


def test_marshal_metadata_key() -> None:
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={
            "__metadata__": (),
        },
        exp=bytes(
            [
                48,
                0,
                0,
                0,
                4,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                5,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                0,
            ]
        ),
        mapper=m,
    )


def test_unmarshal_metadata_key() -> None:
    m = bson.Mapper(keep_types=True)
    unmarshal_inout_test(
        exp={
            "__metadata__": (),
        },
        inp=bytes(
            [
                48,
                0,
                0,
                0,
                4,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                5,
                0,
                0,
                0,
                128,
                116,
                117,
                112,
                108,
                101,
                0,
            ]
        ),
        mapper=m,
    )


def test_marshal_metadata_bytearray_key() -> None:
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={
            "__metadata__": bytearray(),
        },
        exp=bytes(
            [
                52,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                9,
                0,
                0,
                0,
                128,
                98,
                121,
                116,
                101,
                97,
                114,
                114,
                97,
                121,
                0,
            ],
        ),
        mapper=m,
    )


def test_unmarshal_metadata_bytearray_key() -> None:
    m = bson.Mapper(keep_types=True)
    unmarshal_inout_test(
        exp={
            "__metadata__": bytearray(),
        },
        inp=bytes(
            [
                52,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                0,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                9,
                0,
                0,
                0,
                128,
                98,
                121,
                116,
                101,
                97,
                114,
                114,
                97,
                121,
                0,
            ],
        ),
        mapper=m,
    )


def test_unmarshal_does_not_break_python_only() -> None:
    for m in (bson.Mapper(keep_types=True, python_only=False), bson.Mapper(keep_types=True, python_only=True)):
        m.unmarshal(
            bytes(
                [
                    38,
                    0,
                    0,
                    0,
                    4,
                    101,
                    97,
                    0,
                    5,
                    0,
                    0,
                    0,
                    0,
                    5,
                    95,
                    95,
                    109,
                    101,
                    116,
                    97,
                    100,
                    97,
                    116,
                    97,
                    95,
                    95,
                    0,
                    5,
                    0,
                    0,
                    0,
                    128,
                    116,
                    117,
                    112,
                    108,
                    101,
                    0,
                ]
            )
        )


def round_dict_test_keep(inp: Any, mapper: Any = None) -> None:
    if mapper is None:
        mapper = bson
    result = mapper.unmarshal(mapper.marshal(inp))
    assert type(result) is dict  # noqa: E721
    assert len(result) == len(inp)
    check_types(result, inp)


def test_round_dict_bytes_keeping() -> None:
    dicts = [
        {
            "prop1": bytes(),
        },
        {"prop1": bytes([12, 34, 65]), "prop2": bytes(1000), "prop3": 100 * bytes([123]), "prop4": bytes(range(256))},
    ]

    for d in dicts:
        round_dict_test_keep(d, bson.Mapper(keep_types=True))


def test_round_dict_bytearray_keeping() -> None:
    dicts = [
        {
            "prop1": bytearray(),
        },
        {
            "prop1": bytearray([12, 34, 65]),
            "prop2": bytearray(1000),
            "prop3": 100 * bytearray([123]),
            "prop4": bytearray(range(256)),
        },
    ]

    for d in dicts:
        round_dict_test_keep(d, bson.Mapper(keep_types=True))


def test_round_dict_mix_keeping() -> None:
    dicts = [
        {
            "prop1": bytes(),
        },
        {"prop1": bytes([12, 34, 65]), "prop2": bytes(1000), "prop3": 100 * bytes([123]), "prop4": bytes(range(256))},
        {
            "prop1": bytearray(),
        },
        {
            "prop1": bytearray([12, 34, 65]),
            "prop2": bytearray(1000),
            "prop3": 100 * bytearray([123]),
            "prop4": bytearray(range(256)),
        },
    ]

    round_dict_test_keep({"data": dicts}, bson.Mapper(keep_types=True))


def test_round_dict_mix_in_dict_keeping() -> None:
    data = {
        "prop1": tuple(),
        "prop2": tuple([12, 34, 65]),
        "prop3": 1000 * (None,),
        "prop9": 100 * tuple([123]),
        "_prop4": tuple(range(256)),
        "prop11": bytearray(),
        "prop": bytearray([12, 34, 65]),
        "prop22": bytearray(1000),
        "p": 100 * bytearray([123]),
        "4": bytearray(range(256)),
    }

    round_dict_test_keep(data, bson.Mapper(keep_types=True))


def test_round_dict_mix_in_tuple_keeping() -> None:
    data = {
        "prop1": tuple(
            [
                tuple(),
                tuple([12, 34, 65]),
                1000 * (None,),
                100 * tuple([123]),
                tuple(range(256)),
                bytearray(),
                bytearray([12, 34, 65]),
                bytearray(1000),
                100 * bytearray([123]),
                bytearray(range(256)),
            ]
        ),
    }

    round_dict_test_keep(data, bson.Mapper(keep_types=True))


def test_nt_like_dict_empty() -> None:
    C = nt("C", [])
    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({})
        data2 = m.marshal(C())
        assert data1 == data2


def test_nt_like_dict_empty_via_defaults() -> None:
    C = nt("C", ["f1", "f2"], defaults=("hello", 123))
    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"f2": 123, "f1": "hello"})
        data2 = m.marshal(C())
        assert data1 == data2


def test_nt_like_dict_explicit() -> None:
    C = nt("C", ["f1", "f2"], defaults=("hello", 123))
    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"f2": 123, "f1": "hello"})
        data2 = m.marshal(C(f1="hello", f2=123))
        assert data1 == data2


def test_nt_like_dict_mixed1() -> None:
    C = nt("C", ["f1", "f2"], defaults=("hello", 123))
    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"f2": "100", "f1": "hello"})
        data2 = m.marshal(C(f2="100"))
        assert data1 == data2


def test_nt_like_dict_mixed2() -> None:
    C = nt("C", ["f1", "f2"], defaults=("hello", 123))
    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"f2": 123, "f1": "abc"})
        data2 = m.marshal(C(f1="abc"))
        assert data1 == data2


def test_nt_like_dict_inside_array() -> None:
    C = nt("C", ["f1", "f2"], defaults=("hello", 123))
    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"q": [{"f2": 123, "f1": "hello"}, {"f2": 999, "f1": 123}]})
        data2 = m.marshal({"q": [C("hello"), C(123, 999)]})
        assert data1 == data2


def test_nt_like_dict_inside_long_array() -> None:
    C = nt("C", ["f1", "f2"], defaults=("hello", 123))
    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"q": [{"f2": i, "f1": 123} for i in range(20)]})
        data2 = m.marshal({"q": [C(123, i) for i in range(20)]})
        assert data1 == data2


def test_nt_like_dict_no_defaults() -> None:
    C = nt("C", ["f1", "f2"])
    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"q": [{"f2": i, "f1": 123} for i in range(20)]})
        data2 = m.marshal({"q": [C(123, i) for i in range(20)]})
        assert data1 == data2


def test_marshal_nt_not_keeping() -> None:
    C = nt("C", ["v", "f"])

    for m in (bson.Mapper(), bson.Mapper(keep_types=False), None):
        inout_test(
            inp=C(11, 22),
            exp=bytes([19, 0, 0, 0, 16, 118, 0, 11, 0, 0, 0, 16, 102, 0, 22, 0, 0, 0, 0]),
            mapper=m,
        )


def test_unmarshal_nt_all() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), None, bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"v": 11, "f": 22},
            inp=bytes([19, 0, 0, 0, 16, 118, 0, 11, 0, 0, 0, 16, 102, 0, 22, 0, 0, 0, 0]),
            mapper=m,
        )


def test_marshal_nt_inside_nt_not_keeping() -> None:
    C = nt("C", ["v", "f"])

    for m in (bson.Mapper(), bson.Mapper(keep_types=False), None):
        inout_test(
            inp=C(C(11, 22), C(33, 44)),
            exp=bytes(
                [
                    49,
                    0,
                    0,
                    0,
                    3,
                    118,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    11,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    22,
                    0,
                    0,
                    0,
                    0,
                    3,
                    102,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    33,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    44,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            ),
            mapper=m,
        )


def test_unmarshal_nt_inside_nt_all() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), None, bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"f": {"f": 44, "v": 33}, "v": {"f": 22, "v": 11}},
            inp=bytes(
                [
                    49,
                    0,
                    0,
                    0,
                    3,
                    118,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    11,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    22,
                    0,
                    0,
                    0,
                    0,
                    3,
                    102,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    33,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    44,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            ),
            mapper=m,
        )


def test_marshal_nt_inside_dict_not_keeping() -> None:
    C = nt("C", ["v", "f"])

    for m in (bson.Mapper(), bson.Mapper(keep_types=False), None):
        inout_test(
            inp={"v": C(11, 22), "f": C(33, 44)},
            exp=bytes(
                [
                    49,
                    0,
                    0,
                    0,
                    3,
                    102,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    33,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    44,
                    0,
                    0,
                    0,
                    0,
                    3,
                    118,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    11,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    22,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            ),
            mapper=m,
        )


def test_unmarshal_nt_inside_dict_all() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), None, bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"f": {"f": 44, "v": 33}, "v": {"f": 22, "v": 11}},
            inp=bytes(
                [
                    49,
                    0,
                    0,
                    0,
                    3,
                    102,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    33,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    44,
                    0,
                    0,
                    0,
                    0,
                    3,
                    118,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    11,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    22,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            ),
            mapper=m,
        )


def test_marshal_nt_double_inside_not_keeping() -> None:
    C = nt("C", ["v", "f"])

    for m in (bson.Mapper(), bson.Mapper(keep_types=False), None):
        inout_test(
            inp=C({"v": C(11, 22), "f": C(33, 44)}, None),
            exp=bytes(
                [
                    60,
                    0,
                    0,
                    0,
                    3,
                    118,
                    0,
                    49,
                    0,
                    0,
                    0,
                    3,
                    102,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    33,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    44,
                    0,
                    0,
                    0,
                    0,
                    3,
                    118,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    11,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    22,
                    0,
                    0,
                    0,
                    0,
                    0,
                    10,
                    102,
                    0,
                    0,
                ]
            ),
            mapper=m,
        )


def test_unmarshal_nt_double_inside_dict_all() -> None:
    for m in (bson.Mapper(), bson.Mapper(keep_types=False), None, bson.Mapper(keep_types=True)):
        unmarshal_inout_test(
            exp={"v": {"v": {"v": 11, "f": 22}, "f": {"v": 33, "f": 44}}, "f": None},
            inp=bytes(
                [
                    60,
                    0,
                    0,
                    0,
                    3,
                    118,
                    0,
                    49,
                    0,
                    0,
                    0,
                    3,
                    102,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    33,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    44,
                    0,
                    0,
                    0,
                    0,
                    3,
                    118,
                    0,
                    19,
                    0,
                    0,
                    0,
                    16,
                    118,
                    0,
                    11,
                    0,
                    0,
                    0,
                    16,
                    102,
                    0,
                    22,
                    0,
                    0,
                    0,
                    0,
                    0,
                    10,
                    102,
                    0,
                    0,
                ]
            ),
            mapper=m,
        )


def test_dc_like_dict_empty() -> None:
    @dataclass
    class C:
        pass

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({})
        data2 = m.marshal(C())
        assert data1 == data2


def test_dc_like_dict_empty_via_defaults() -> None:
    @dataclass
    class C:
        f1: str = "hello"
        f2: int = 123

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"f2": 123, "f1": "hello"})
        data2 = m.marshal(C())
        assert data1 == data2


def test_dc_like_dict_explicit() -> None:
    @dataclass
    class C:
        f1: str = "hello"
        f2: int = 123

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"f2": 123, "f1": "hello"})
        data2 = m.marshal(C(f1="hello", f2=123))
        assert data1 == data2


def test_dc_like_dict_mixed1() -> None:
    @dataclass
    class C:
        f1: str = "hello"
        f2: int = 123

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"f2": 100, "f1": "hello"})
        data2 = m.marshal(C(f2=100))
        assert data1 == data2


def test_dc_like_dict_mixed2() -> None:
    @dataclass
    class C:
        f1: str = "hello"
        f2: int = 123

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"f2": 123, "f1": "abc"})
        data2 = m.marshal(C(f1="abc"))
        assert data1 == data2


def test_dc_like_dict_inside_array() -> None:
    @dataclass
    class C:
        f1: str = "hello"
        f2: int = 123

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"q": [{"f2": 123, "f1": "hello"}, {"f2": 999, "f1": "123"}]})
        data2 = m.marshal({"q": [C("hello"), C("123", 999)]})
        assert data1 == data2


def test_dc_like_dict_inside_long_array() -> None:
    @dataclass
    class C:
        f1: int
        f2: int = 123

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"q": [{"f2": i, "f1": 123} for i in range(20)]})
        data2 = m.marshal({"q": [C(123, i) for i in range(20)]})
        assert data1 == data2


def test_dc_like_dict_no_defaults() -> None:
    @dataclass
    class C:
        f1: int
        f2: int

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"q": [{"f2": i, "f1": 123} for i in range(20)]})
        data2 = m.marshal({"q": [C(123, i) for i in range(20)]})
        assert data1 == data2


def test_marshal_dc_not_keeping() -> None:
    C1 = nt("C1", ["v", "f"])

    @dataclass
    class C2:
        v: Any
        f: Any

    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson):
        data1 = m.marshal(C1(11, 22))
        data2 = m.marshal(C2(11, 22))
        assert data1 == data2


def test_marshal_dc_inside_itselt_not_keeping() -> None:
    C1 = nt("C1", ["v", "f"])

    @dataclass
    class C2:
        v: Any
        f: Any

    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson):
        data1 = m.marshal(C1(C1(11, 22), C1(33, 44)))
        data2 = m.marshal(C2(C2(11, 22), C2(33, 44)))
        assert data1 == data2


def test_marshal_dc_inside_dict_not_keeping() -> None:
    C1 = nt("C1", ["v", "f"])

    @dataclass
    class C2:
        v: Any
        f: Any

    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson):
        data1 = m.marshal({"v": C1(11, 22), "f": C1(33, 44)})
        data2 = m.marshal({"v": C2(11, 22), "f": C2(33, 44)})
        assert data1 == data2


def test_marshal_dc_inside_dict_mixed_not_keeping() -> None:
    C1 = nt("C1", ["v", "f"])

    @dataclass
    class C2:
        v: Any
        f: Any

    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson):
        data1 = m.marshal({"v": C1(11, 22), "f": C2(33, 44)})
        data2 = m.marshal({"v": C2(11, 22), "f": C1(33, 44)})
        assert data1 == data2


def test_marshal_dc_double_inside_not_keeping() -> None:
    C1 = nt("C1", ["v", "f"])

    @dataclass
    class C2:
        v: Any
        f: Any

    for m in (bson.Mapper(), bson.Mapper(keep_types=False), bson):
        data1 = m.marshal(C1({"v": C1(11, 22), "f": C1(33, 44)}, None))
        data2 = m.marshal(C2({"v": C2(11, 22), "f": C2(33, 44)}, None))
        assert data1 == data2


def test_props_like_dict_empty() -> None:
    class C:
        pass

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        with pytest.raises(bson.BsonUnsupportedObjectError):
            m.marshal(C())


def test_props_like_dict_exc() -> None:
    class C:
        @property
        def x(self) -> None:
            raise ValueError()

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        with pytest.raises(bson.BsonUnsupportedObjectError):
            m.marshal(C())


def test_props_like_dict_single() -> None:
    class C:
        @property
        def x(self) -> int:
            return 123

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"x": 123})
        data2 = m.marshal(C())
        assert data1 == data2


def test_props_like_dict_single_with_exc() -> None:
    class C:
        @property
        def x0(self) -> None:
            raise ValueError()

        @property
        def x1(self) -> int:
            return 123

        @property
        def x2(self) -> None:
            raise ValueError()

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"x1": 123})
        data2 = m.marshal(C())
        assert data1 == data2


def test_props_like_dict_two_asc() -> None:
    class C:
        @property
        def x0(self) -> None:
            pass

        @property
        def x1(self) -> int:
            return 123

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"x0": None, "x1": 123})
        data2 = m.marshal(C())
        assert data1 == data2


def test_props_like_dict_two_desc() -> None:
    class C:
        @property
        def x0(self) -> None:
            pass

        @property
        def x1(self) -> int:
            return 123

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"x0": None, "x1": 123})
        data2 = m.marshal(C())
        assert data1 == data2


def test_props_like_dict_with_attr() -> None:
    class C:
        def __init__(self: Any, v: int) -> None:
            self.v = v

        @property
        def f0(self) -> int:
            return self.v * 2

        @property
        def f1(self) -> int:
            return self.v + 2

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"f0": 0, "f1": 2})
        data2 = m.marshal(C(0))
        assert data1 == data2


def test_props_cycle() -> None:
    class C:
        @property
        def x0(self) -> Any:
            return self

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        with pytest.raises(bson.BsonCycleDetectedError):
            m.marshal(C())


def test_props_mutual_cycle() -> None:
    class C:
        @property
        def x0(self) -> Any:
            return self.x1

        @property
        def x1(self) -> Any:
            return self.x0

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        with pytest.raises(RecursionError):
            m.marshal(C())


def test_props_like_dict_inside_dict() -> None:
    class C:
        def __init__(self: Any, v: int) -> None:
            self.v = v

        @property
        def f0(self) -> int:
            return self.v * 2

        @property
        def f1(self) -> int:
            return self.v + 2

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"q": {"f0": 0, "f1": 2}})
        data2 = m.marshal({"q": C(0)})
        assert data1 == data2


def test_props_like_dict_inside_array() -> None:
    class C:
        def __init__(self: Any, v: int) -> None:
            self.v = v

        @property
        def f0(self) -> int:
            return self.v * 2

        @property
        def f1(self) -> int:
            return self.v + 2

    for m in (bson, bson.Mapper(keep_types=False), bson.Mapper()):
        data1 = m.marshal({"q": [{"f0": i * 2, "f1": i + 2} for i in range(20)]})
        data2 = m.marshal({"q": [C(i) for i in range(20)]})
        assert data1 == data2


def test_marshal_keep_nt_typeinfo_double_inside_empty() -> None:
    C = nt("C", [])
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={"a": {"b": C()}},
        exp=bytes(
            [
                132,
                0,
                0,
                0,
                3,
                97,
                0,
                36,
                0,
                0,
                0,
                3,
                98,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                4,
                0,
                0,
                0,
                128,
                110,
                116,
                45,
                48,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                69,
                0,
                0,
                0,
                128,
                0,
                68,
                0,
                0,
                0,
                3,
                116,
                121,
                112,
                101,
                115,
                0,
                56,
                0,
                0,
                0,
                3,
                110,
                116,
                45,
                48,
                0,
                45,
                0,
                0,
                0,
                3,
                100,
                101,
                102,
                97,
                117,
                108,
                116,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                102,
                105,
                101,
                108,
                100,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                2,
                110,
                97,
                109,
                101,
                0,
                2,
                0,
                0,
                0,
                67,
                0,
                0,
                0,
                0,
                0,
            ]
        ),
        mapper=m,
    )


def test_unmarshal_keep_nt_typeinfo_double_inside_empty() -> None:
    C = nt("C", [])
    m = bson.Mapper(keep_types=True)
    result = m.unmarshal(
        bytes(
            [
                132,
                0,
                0,
                0,
                3,
                97,
                0,
                36,
                0,
                0,
                0,
                3,
                98,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                4,
                0,
                0,
                0,
                128,
                110,
                116,
                45,
                48,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                69,
                0,
                0,
                0,
                128,
                0,
                68,
                0,
                0,
                0,
                3,
                116,
                121,
                112,
                101,
                115,
                0,
                56,
                0,
                0,
                0,
                3,
                110,
                116,
                45,
                48,
                0,
                45,
                0,
                0,
                0,
                3,
                100,
                101,
                102,
                97,
                117,
                108,
                116,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                102,
                105,
                101,
                108,
                100,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                2,
                110,
                97,
                109,
                101,
                0,
                2,
                0,
                0,
                0,
                67,
                0,
                0,
                0,
                0,
                0,
            ]
        )
    )
    assert {"a": {"b": C()}} == result


def test_marshal_keep_nt_typeinfo_inside_empty() -> None:
    C = nt("C", [])
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp={"a": C()},
        exp=bytes(
            [
                120,
                0,
                0,
                0,
                3,
                97,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                88,
                0,
                0,
                0,
                128,
                0,
                87,
                0,
                0,
                0,
                2,
                99,
                104,
                105,
                108,
                100,
                114,
                101,
                110,
                0,
                5,
                0,
                0,
                0,
                110,
                116,
                45,
                48,
                0,
                3,
                116,
                121,
                112,
                101,
                115,
                0,
                56,
                0,
                0,
                0,
                3,
                110,
                116,
                45,
                48,
                0,
                45,
                0,
                0,
                0,
                3,
                100,
                101,
                102,
                97,
                117,
                108,
                116,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                102,
                105,
                101,
                108,
                100,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                2,
                110,
                97,
                109,
                101,
                0,
                2,
                0,
                0,
                0,
                67,
                0,
                0,
                0,
                0,
                0,
            ]
        ),
        mapper=m,
    )


def test_unmarshal_keep_nt_typeinfo_inside_empty() -> None:
    C = nt("C", [])
    m = bson.Mapper(keep_types=True)
    result = m.unmarshal(
        bytes(
            [
                120,
                0,
                0,
                0,
                3,
                97,
                0,
                5,
                0,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                88,
                0,
                0,
                0,
                128,
                0,
                87,
                0,
                0,
                0,
                2,
                99,
                104,
                105,
                108,
                100,
                114,
                101,
                110,
                0,
                5,
                0,
                0,
                0,
                110,
                116,
                45,
                48,
                0,
                3,
                116,
                121,
                112,
                101,
                115,
                0,
                56,
                0,
                0,
                0,
                3,
                110,
                116,
                45,
                48,
                0,
                45,
                0,
                0,
                0,
                3,
                100,
                101,
                102,
                97,
                117,
                108,
                116,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                102,
                105,
                101,
                108,
                100,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                2,
                110,
                97,
                109,
                101,
                0,
                2,
                0,
                0,
                0,
                67,
                0,
                0,
                0,
                0,
                0,
            ]
        )
    )
    assert {"a": C()} == result


def test_bidi_keep_nt_typeinfo_two_instances_double_inside_empty() -> None:
    C = nt("C", [])
    v = {"a": {"b1": C(), "b2": C()}}
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
    assert v2["a"]["b1"].__class__ is v2["a"]["b2"].__class__


def test_bidi_keep_nt_typeinfo_two_instances_inside_empty() -> None:
    C = nt("C", [])
    v = {"b1": C(), "b2": C()}
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
    assert v2["b1"].__class__ is v2["b2"].__class__


def test_bidi_keep_nt_typeinfo_just_name_doesnt_matter() -> None:
    C = nt("C", [])
    v = {"b1": C(), "b2": C()}
    C = nt("C", [])  # type: ignore
    v["b3"] = C()
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
    assert v2["b1"].__class__ is v2["b2"].__class__
    assert v2["b1"].__class__ is not v2["b3"].__class__


def test_bidi_with_single_field() -> None:
    C = nt("C", ["v"])
    v = {"a": {"b1": C(123), "b2": C(None)}}
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
    assert v2["a"]["b1"].__class__ is v2["a"]["b2"].__class__


def test_bidi_with_single_field_keep_default() -> None:
    C = nt("C", ["v"], defaults=["hello"])
    v = {"a": {"b1": C(12.3), "b2": C()}}
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
    assert v2["a"]["b1"].__class__ is v2["a"]["b2"].__class__
    assert "hello" == v2["a"]["b2"].__class__().v


def test_bidi_with_several_values() -> None:
    C = nt("C", ["v1", "v2"], defaults=["hello"])
    v = {"a": {"b1": C(12.3), "b2": C("abc", "cde")}}
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
    assert v2["a"]["b1"].__class__ is v2["a"]["b2"].__class__
    assert "hello" == v2["a"]["b2"].__class__(12).v2


def test_bidi_with_several_values_inverted_order() -> None:
    C = nt("C", ["v2", "v1"], defaults=["hello"])
    v = {"a": {"b1": C(12.3), "b2": C("abc", "cde")}}
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
    assert v2["a"]["b1"].__class__ is v2["a"]["b2"].__class__


def test_bidi_keeping_types() -> None:
    C = nt("C", ["v1", "v2"])
    v = {"a": {"b": C((12, 23), [21, 23])}}
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
    assert v2["a"]["b"].v1.__class__ is v["a"]["b"].v1.__class__
    assert v2["a"]["b"].v2.__class__ is v["a"]["b"].v2.__class__


def test_bidi_keeping_types_2() -> None:
    C = nt("C", ["v1", "v2"])
    v = {"a": C((12, 23), [21, 23])}
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
    assert v2["a"].v1.__class__ is v["a"].v1.__class__
    assert v2["a"].v2.__class__ is v["a"].v2.__class__


def test_bidi_keeping_types_many() -> None:
    C1 = nt("C1", ["v1", "v2"])
    C2 = nt("C2", ["f1", "f2", "f3"])
    v = {
        "a": C1(None, C1(123, None)),
        "b": {
            "c": C2(1, 2, f3=C1([], ())),
        },
    }
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v


def test_marshal_nt_as_root() -> None:
    C = nt("C", [])
    m = bson.Mapper(keep_types=True)
    inout_test(
        inp=C(),
        exp=bytes(
            [
                108,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                84,
                0,
                0,
                0,
                128,
                0,
                83,
                0,
                0,
                0,
                2,
                115,
                101,
                108,
                102,
                0,
                5,
                0,
                0,
                0,
                110,
                116,
                45,
                48,
                0,
                3,
                116,
                121,
                112,
                101,
                115,
                0,
                56,
                0,
                0,
                0,
                3,
                110,
                116,
                45,
                48,
                0,
                45,
                0,
                0,
                0,
                3,
                100,
                101,
                102,
                97,
                117,
                108,
                116,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                102,
                105,
                101,
                108,
                100,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                2,
                110,
                97,
                109,
                101,
                0,
                2,
                0,
                0,
                0,
                67,
                0,
                0,
                0,
                0,
                0,
            ]
        ),
        mapper=m,
    )


def test_unmarshal_nt_as_root() -> None:
    C = nt("C", [])
    m = bson.Mapper(keep_types=True)
    result = m.unmarshal(
        bytes(
            [
                108,
                0,
                0,
                0,
                5,
                95,
                95,
                109,
                101,
                116,
                97,
                100,
                97,
                116,
                97,
                95,
                95,
                0,
                84,
                0,
                0,
                0,
                128,
                0,
                83,
                0,
                0,
                0,
                2,
                115,
                101,
                108,
                102,
                0,
                5,
                0,
                0,
                0,
                110,
                116,
                45,
                48,
                0,
                3,
                116,
                121,
                112,
                101,
                115,
                0,
                56,
                0,
                0,
                0,
                3,
                110,
                116,
                45,
                48,
                0,
                45,
                0,
                0,
                0,
                3,
                100,
                101,
                102,
                97,
                117,
                108,
                116,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                4,
                102,
                105,
                101,
                108,
                100,
                115,
                0,
                5,
                0,
                0,
                0,
                0,
                2,
                110,
                97,
                109,
                101,
                0,
                2,
                0,
                0,
                0,
                67,
                0,
                0,
                0,
                0,
                0,
            ]
        )
    )
    assert result == C()


def test_bidi_empty_nt_as_root() -> None:
    C1 = nt("C1", [])
    v = C1()
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v


def test_bidi_singleton_nt_with_array_as_root() -> None:
    C1 = nt("C1", ["v"])
    v = C1([C1(123), C1(12.3)])
    m = bson.Mapper(keep_types=True)
    v2 = m.unmarshal(m.marshal(v))
    assert v2 == v
