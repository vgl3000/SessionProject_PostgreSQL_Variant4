"""Проверка меню без подключения к PostgreSQL.

Сами SQL-запросы проверяются отдельно при запуске приложения с базой.
"""
import unittest
from decimal import Decimal
from unittest.mock import Mock, patch

from main import Main


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = Main.__new__(Main)
        self.app.rooms = Mock()
        self.app.racks = Mock()

    def test_choice_uses_screen_number_not_id(self):
        rows = [{"id": 105, "name": "Склад 1"}, {"id": 999, "name": "Склад 2"}]
        with patch.object(self.app, "ask", side_effect=["999", "3", "2"]):
            selected = self.app.choose_visible_row(rows, "помещения")
        self.assertEqual(selected["name"], "Склад 2")
        self.assertEqual(selected["id"], 999)

    def test_cancel_selection(self):
        with patch.object(self.app, "ask", return_value="0"):
            self.assertIsNone(self.app.choose_visible_row([{"id": 4}], "стеллажа"))

    def test_delete_room_requires_confirmation(self):
        self.app.rooms.get.return_value = {"id": 32, "name": "Склад 1"}
        self.app.racks.count_by_room.return_value = 2
        with patch.object(self.app, "confirm", return_value=False):
            self.app.delete_room({"id": 32})
        self.app.rooms.delete_one.assert_not_called()

    def test_delete_room_with_racks(self):
        self.app.rooms.get.return_value = {"id": 32, "name": "Склад 1"}
        self.app.racks.count_by_room.return_value = 2
        self.app.rooms.delete_one.return_value = True
        with patch.object(self.app, "confirm", return_value=True):
            self.app.delete_room({"id": 32})
        self.app.rooms.delete_one.assert_called_once_with(32, 2, delete_racks=True)

    def test_add_rack_attaches_selected_room(self):
        values = [1, 10, Decimal("1.5"), Decimal("1.2"), Decimal("1"), Decimal("1000")]
        with patch.object(self.app, "ask_fields", return_value=values):
            self.app.add_rack(42)
        self.app.racks.insert_one.assert_called_once()
        self.assertEqual(self.app.racks.insert_one.call_args.args[0], 42)

    def test_cancel_add_room(self):
        with patch.object(self.app, "room_values", return_value=None):
            self.app.add_room()
        self.app.rooms.insert_one.assert_not_called()

    def test_invalid_temperature_order_is_caught(self):
        values = ["Склад", Decimal("500"), Decimal("30"), Decimal("20"), None, None]
        with patch.object(self.app, "ask_fields", side_effect=[values, None]):
            self.assertIsNone(self.app.room_values())


if __name__ == "__main__":
    unittest.main()
