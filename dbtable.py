"""Общие безопасные методы запросов PostgreSQL.

Имена таблиц подставляются только через psycopg2.sql.Identifier,
пользовательские значения — только через параметры %s.
"""

from psycopg2 import sql
from psycopg2.extras import RealDictCursor


class DataChangedError(Exception):
    """Связанные записи изменились после их показа пользователю."""


class DbTable:
    table = ""

    def __init__(self, connection):
        self.dbconn = connection

    @property
    def table_ref(self):
        return sql.Identifier(self.dbconn.schema, self.table)

    def _one(self, query, values=()):
        with self.dbconn.conn:
            with self.dbconn.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, values)
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def _all(self, query, values=()):
        with self.dbconn.conn:
            with self.dbconn.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, values)
                return [dict(row) for row in cursor.fetchall()]

    def _execute(self, query, values=(), returning=False):
        with self.dbconn.conn:
            with self.dbconn.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, values)
                if returning:
                    row = cursor.fetchone()
                    return dict(row) if row is not None else None
                return cursor.rowcount


def database_error_text(error):
    """Понятные пользователю сообщения без показа текста SQL/данных сервера."""
    code = getattr(error, "pgcode", None)
    messages = {
        "23505": "Стеллаж с таким номером уже есть в выбранном помещении. Укажите другой номер.",
        "23503": "Невозможно выполнить действие из-за связанных записей. Обновите список.",
        "23514": "Данные не соответствуют ограничениям базы. Проверьте введённые значения.",
        "23502": "Обязательное поле не заполнено.",
        "22001": "Текст слишком длинный для соответствующего поля.",
        "22003": "Число выходит за допустимый диапазон.",
        "22P02": "Введено значение неподходящего типа.",
        "42501": "У пользователя PostgreSQL недостаточно прав на эту операцию.",
        "42P01": "Таблица не найдена. Проверьте настройки схемы БД.",
        "3F000": "Схема PostgreSQL не найдена. Проверьте параметр schema.",
    }
    return messages.get(code, "Ошибка PostgreSQL: операция отменена, данные не повреждены. Проверьте подключение и настройки БД.")
