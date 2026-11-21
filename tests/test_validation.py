"""Тестирование без подключения к серверу PostgreSQL."""
import unittest
from decimal import Decimal
from validation import (
    ValidationError, room_name, positive_integer, volume,
    temperature, humidity, nullable, room_environment,
    rack_number, places_count, dimension, max_load,
)


class ValidationTests(unittest.TestCase):
    def test_room_name(self):
        self.assertEqual(room_name("  Склад 1  "), "Склад 1")
        self.assertEqual(room_name("A' OR '1'='1"), "A' OR '1'='1")
        for value in ("", "  ", "z" * 101, "abc\x00", "abc\u200b"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                room_name(value)

    def test_positive_integers(self):
        self.assertEqual(rack_number("15"), 15)
        self.assertEqual(places_count("2147483647"), 2147483647)
        for value in ("0", "-1", "4.5", "2147483648", "1 OR 1=1", "", "١"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                positive_integer(value, "Номер")

    def test_volume_and_dimensions(self):
        self.assertEqual(volume("100,50"), Decimal("100.50"))
        self.assertEqual(dimension("0.01"), Decimal("0.01"))
        self.assertEqual(max_load("99999999.99"), Decimal("99999999.99"))
        for value in ("0", "-1", "100000000", "0.001", "NaN", "1e3", "1; DROP TABLE rooms"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                volume(value)

    def test_temperature(self):
        self.assertEqual(temperature("-999,99"), Decimal("-999.99"))
        self.assertEqual(temperature("999.99"), Decimal("999.99"))
        for value in ("1000", "-1000", "12.345", ""):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                temperature(value)

    def test_humidity(self):
        self.assertEqual(humidity("0"), Decimal("0.00"))
        self.assertEqual(humidity("100"), Decimal("100.00"))
        for value in ("-0.01", "100.01", "inf", " "):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                humidity(value)

    def test_nullable(self):
        self.assertIsNone(nullable(temperature)(""))
        self.assertEqual(nullable(humidity)("37,5"), Decimal("37.50"))

    def test_room_environment(self):
        room_environment(None, Decimal("20"), None, None)
        room_environment(Decimal("20"), Decimal("20"), Decimal("30"), Decimal("30"))
        with self.assertRaises(ValidationError):
            room_environment(Decimal("30"), Decimal("20"), None, None)
        with self.assertRaises(ValidationError):
            room_environment(None, None, Decimal("50"), Decimal("40"))


if __name__ == "__main__":
    unittest.main()
