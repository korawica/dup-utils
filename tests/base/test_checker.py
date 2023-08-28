import unittest

import dup_utils.core.base.checker as ck


class CheckTestCase(unittest.TestCase):
    def setUp(self) -> None:
        ...

    def test_is_int(self):
        map_value_respect = (
            (1, True),
            (-1, True),
            (1.0, False),
            (-1.0, False),
            ("0", True),
            ("1", True),
            ("-1", True),
            ("+1", True),
            ("06", True),
            ("abc 123", False),
            (1.1, False),
            (-1.1, False),
            ("1.1", False),
            ("-1.1", False),
            ("+1.1", False),
            ("1.1.1", False),
            ("1.1.0", False),
            ("1.0.1", False),
            ("1.0.0", False),
            ("1.0.", False),
            ("1..0", False),
            ("1..", False),
            ("0.0.", False),
            ("0..0", False),
            ("0..", False),
            ("one", False),
            (object(), False),
            ((1, 2, 3), False),
            ([1, 2, 3], False),
            ({"one": "two"}, False),
            ("0.", False),
            (".0", False),
            (".01", False),
        )
        for values in map_value_respect:
            _respec, _value = values[1], values[0]
            self.assertEqual(_respec, ck.is_int(_value))

    def test_can_int(self):
        map_value_respect = (
            (1, True),
            (-1, True),
            (1.0, True),
            (-1.0, True),
            ("0.", True),
            ("0.0", True),
            ("1.0", True),
            ("-1.0", True),
            ("+1.0", True),
        )
        for values in map_value_respect:
            _respec, _value = values[1], values[0]
            self.assertEqual(_respec, ck.can_int(_value))
