# ФИО студента: Лукьянчиков Валерий Геннадьевич
# Вариант: 4
# Условия варианта: таблицы «помещения» и «стеллажи» без связей с другими таблицами.
# Первая таблица: просмотр, добавление, изменение и удаление помещений.
# Вторая таблица: просмотр и добавление стеллажей выбранного помещения, удаление.
# Пользователь не видит и не вводит значения суррогатных ключей.

"""Консольное CRUD-приложение PostgreSQL. Вариант 4."""
import psycopg2
from dbconnection import DbConnection
from dbtable import DataChangedError, database_error_text
from project_config import ConfigError, ProjectConfig
from tables.rooms_table import RoomsTable
from tables.racks_table import RacksTable
from validation import (
    ValidationError, room_name, volume, temperature, humidity, nullable,
    room_environment, rack_number, places_count, dimension, max_load,
)

class UserExit(Exception):
    """Запрошено закрытие приложения."""


class Main:
    def __init__(self, connection):
        self.connection = connection
        self.rooms = RoomsTable(connection)
        self.racks = RacksTable(connection)

    def db_init(self):
        self.rooms.create()
        self.racks.create()

    @staticmethod
    def ask(prompt):
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt) as exc:
            raise UserExit from exc

    def ask_fields(self, definitions, editing=False):
        """definitions: (название поля, валидатор, текущее значение)."""
        values = []
        for title, validator, old in definitions:
            while True:
                extra = f" [{old if old is not None else 'не задано'}]" if editing else ""
                raw = self.ask(f"{title}{extra} (/отмена): ").strip()
                if raw.lower() == "/отмена":
                    print("Операция отменена.")
                    return None
                if editing and raw == "":
                    values.append(old)
                    break
                try:
                    if editing and raw == "-" and title.startswith(("Минимальная", "Максимальная")):
                        values.append(None)
                    else:
                        values.append(validator(raw))
                    break
                except ValidationError as exc:
                    print("Некорректный ввод:", exc)
        return values

    def confirm(self, message):
        while True:
            raw = self.ask(message + " (да/нет): ").strip().lower()
            if raw in {"да", "д"}:
                return True
            if raw in {"нет", "н", ""}:
                return False
            print("Введите «да» или «нет».")

    def choose_visible_row(self, rows, title):
        if not rows:
            print("Список пуст.")
            return None
        while True:
            value = self.ask(f"Номер {title} в списке (0 — отмена): ").strip()
            if value == "0":
                return None
            if value.isascii() and value.isdecimal() and 1 <= len(value) <= len(str(len(rows))) and 1 <= int(value) <= len(rows):
                return rows[int(value) - 1]
            print("Введите номер строки из списка.")

    @staticmethod
    def run_action(action, *args):
        try:
            action(*args)
        except DataChangedError as exc:
            print("Данные изменились:", exc)
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            raise
        except psycopg2.Error as exc:
            print(database_error_text(exc))

    @staticmethod
    def room_definitions(old=None):
        old = old or {}
        return [
            ("Название помещения (1–100 символов)", room_name, old.get("name")),
            ("Полезный объём, м³ (0,01…99999999,99)", volume, old.get("useful_volume")),
            ("Минимальная температура, °C (Enter — не задана)", nullable(temperature), old.get("min_temperature")),
            ("Максимальная температура, °C (Enter — не задана)", nullable(temperature), old.get("max_temperature")),
            ("Минимальная влажность, % (Enter — не задана)", nullable(humidity), old.get("min_humidity")),
            ("Максимальная влажность, % (Enter — не задана)", nullable(humidity), old.get("max_humidity")),
        ]

    @staticmethod
    def rack_definitions(old=None):
        old = old or {}
        return [
            ("Номер стеллажа (целое число > 0)", rack_number, old.get("rack_number")),
            ("Количество мест (целое число > 0)", places_count, old.get("places_count")),
            ("Высота места, м", dimension, old.get("place_height")),
            ("Ширина места, м", dimension, old.get("place_width")),
            ("Длина места, м", dimension, old.get("place_length")),
            ("Максимальная нагрузка, кг", max_load, old.get("max_load")),
        ]

    def room_values(self, old=None):
        while True:
            values = self.ask_fields(self.room_definitions(old), editing=old is not None)
            if values is None:
                return None
            try:
                room_environment(*values[2:])
                return values
            except ValidationError as exc:
                print("Некорректные условия помещения:", exc)
                print("Повторите ввод или введите /отмена.")

    def add_room(self):
        print("\nДобавление помещения (пустые климатические поля разрешены).")
        values = self.room_values()
        if values is not None:
            self.rooms.insert_one(*values)
            print("Помещение добавлено.")

    def edit_room(self, selected):
        old = self.rooms.get(selected["id"])
        if old is None:
            print("Помещение удалено другим пользователем. Обновите список.")
            return
        print(f"\nИзменение помещения «{old['name']}». Enter — оставить, - — очистить климатическое поле.")
        values = self.room_values(old)
        if values is not None:
            if self.rooms.update_one(old["id"], *values):
                print("Помещение изменено.")
            else:
                print("Помещение не найдено.")

    def delete_room(self, selected):
        room = self.rooms.get(selected["id"])
        if room is None:
            print("Помещение уже удалено.")
            return
        count = self.racks.count_by_room(room["id"])
        msg = (f"Удалить помещение «{room['name']}» и ВСЕ его стеллажи ({count} шт.)?"
               if count else f"Удалить помещение «{room['name']}»?")
        if not self.confirm(msg):
            print("Удаление отменено.")
            return
        if self.rooms.delete_one(room["id"], count, delete_racks=count > 0):
            print("Помещение удалено" + (" вместе со стеллажами." if count else "."))
        else:
            print("Помещение уже удалено.")

    @staticmethod
    def text_nullable(value):
        return "—" if value is None else str(value)

    def show_rooms(self):
        while True:
            rows = self.rooms.list_all()
            print("\n=== ПОМЕЩЕНИЯ ===")
            for number, row in enumerate(rows, 1):
                print(f"{number}. {row['name']} | объём {row['useful_volume']} м³ | стеллажей: {row['racks_count']}")
                print("   температура: " + self.text_nullable(row["min_temperature"]) + "…" +
                      self.text_nullable(row["max_temperature"]) + " °C; влажность: " +
                      self.text_nullable(row["min_humidity"]) + "…" +
                      self.text_nullable(row["max_humidity"]) + " %")
            if not rows:
                print("(Записей нет)")
            print("1 — добавить; 2 — изменить; 3 — удалить; 4 — стеллажи помещения")
            print("0 — главное меню; 9 — выход")
            choice = self.ask("Действие: ").strip()
            if choice == "0":
                return
            if choice == "9":
                raise UserExit
            if choice == "1":
                self.run_action(self.add_room)
            elif choice in {"2", "3", "4"}:
                selected = self.choose_visible_row(rows, "помещения")
                if selected is not None:
                    if choice == "2":
                        self.run_action(self.edit_room, selected)
                    elif choice == "3":
                        self.run_action(self.delete_room, selected)
                    else:
                        self.show_racks(selected["id"])
            else:
                print("Неизвестная команда.")

    def add_rack(self, room_id):
        print("\nДобавление стеллажа в выбранное помещение.")
        values = self.ask_fields(self.rack_definitions())
        if values is not None:
            self.racks.insert_one(room_id, *values)
            print("Стеллаж добавлен.")

    def delete_rack(self, room_id, selected):
        old = self.racks.get_in_room(selected["id"], room_id)
        if old is None:
            print("Стеллаж уже удалён. Обновите список.")
            return
        if self.confirm(f"Удалить стеллаж №{old['rack_number']}?"):
            if self.racks.delete_one(old["id"], room_id):
                print("Стеллаж удалён.")
            else:
                print("Стеллаж уже удалён.")
        else:
            print("Удаление отменено.")

    def show_racks(self, room_id):
        while True:
            room = self.rooms.get(room_id)
            if room is None:
                print("Помещение удалено другим пользователем. Возврат к списку.")
                return
            rows = self.racks.list_by_room(room_id)
            print(f"\n=== СТЕЛЛАЖИ: {room['name']} ===")
            for number, row in enumerate(rows, 1):
                print(f"{number}. Стеллаж №{row['rack_number']}; мест {row['places_count']}; "
                      f"размер места (В×Ш×Д) {row['place_height']}×{row['place_width']}×{row['place_length']} м; "
                      f"нагрузка {row['max_load']} кг")
            if not rows:
                print("(Стеллажей нет)")
            print("1 — добавить; 2 — удалить; 0 — к помещениям; 9 — выход")
            choice = self.ask("Действие: ").strip()
            if choice == "0":
                return
            if choice == "9":
                raise UserExit
            if choice == "1":
                self.run_action(self.add_rack, room_id)
            elif choice == "2":
                selected = self.choose_visible_row(rows, "стеллажа")
                if selected is not None:
                    self.run_action(self.delete_rack, room_id, selected)
            else:
                print("Неизвестная команда.")

    def main_cycle(self):
        print("Добро пожаловать! Вариант 4: помещения и стеллажи (PostgreSQL).")
        while True:
            print("\n=== ГЛАВНОЕ МЕНЮ ===\n1 — управление помещениями и стеллажами\n9 — выход")
            try:
                choice = self.ask("Действие: ").strip()
                if choice == "9":
                    break
                if choice == "1":
                    self.show_rooms()
                else:
                    print("Неизвестная команда.")
            except DataChangedError as exc:
                print("Данные изменились:", exc)
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                print("Потеряно соединение с PostgreSQL. Проверьте сервер и запустите программу снова.")
                break
            except psycopg2.Error as exc:
                print(database_error_text(exc))
            except UserExit:
                break
        print("До свидания!")


def main():
    connection = None
    try:
        config = ProjectConfig()
        connection = DbConnection(config)
        app = Main(connection)
        app.db_init()
        app.main_cycle()
        return 0
    except ConfigError as exc:
        print("Ошибка настроек:", exc)
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        print("Не удаётся подключиться к PostgreSQL. Проверьте config.yaml и состояние сервера.")
    except psycopg2.Error as exc:
        print("Не удалось подготовить таблицы:", database_error_text(exc))
    except UserExit:
        print("До свидания!")
        return 0
    finally:
        if connection is not None:
            connection.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
