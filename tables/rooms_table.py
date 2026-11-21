"""Помещения (поля сохранены из домашней работы модуля 1, вариант 4)."""
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from dbtable import DataChangedError, DbTable


class RoomsTable(DbTable):
    table = "rooms"

    def create(self):
        query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                useful_volume NUMERIC(10, 2) NOT NULL CHECK (useful_volume > 0),
                min_temperature NUMERIC(5, 2),
                max_temperature NUMERIC(5, 2),
                min_humidity NUMERIC(5, 2),
                max_humidity NUMERIC(5, 2),
                CONSTRAINT rooms_name_valid CHECK (
                    length(btrim(name)) BETWEEN 1 AND 100 AND name = btrim(name)
                ),
                CONSTRAINT rooms_temperature_order CHECK (min_temperature <= max_temperature),
                CONSTRAINT rooms_min_humidity_range CHECK (min_humidity BETWEEN 0 AND 100),
                CONSTRAINT rooms_max_humidity_range CHECK (max_humidity BETWEEN 0 AND 100),
                CONSTRAINT rooms_humidity_order CHECK (min_humidity <= max_humidity)
            )
        """).format(self.table_ref)
        with self.dbconn.conn:
            with self.dbconn.conn.cursor() as cursor:
                cursor.execute(query)

    def count(self):
        return self._one(sql.SQL("SELECT COUNT(*) AS total FROM {}").format(self.table_ref))["total"]

    def list_page(self, limit, offset):
        query = sql.SQL("""
            SELECT r.id, r.name, r.useful_volume, r.min_temperature, r.max_temperature,
                   r.min_humidity, r.max_humidity,
                   (SELECT COUNT(*) FROM {} k WHERE k.room_id = r.id) AS racks_count
            FROM {} r ORDER BY lower(r.name), r.name, r.id LIMIT %s OFFSET %s
        """).format(sql.Identifier(self.dbconn.schema, "racks"), self.table_ref)
        return self._all(query, (limit, offset))

    def get(self, room_id):
        return self._one(sql.SQL("""
            SELECT id, name, useful_volume, min_temperature, max_temperature,
                   min_humidity, max_humidity FROM {} WHERE id = %s
        """).format(self.table_ref), (room_id,))

    def insert_one(self, name, useful_volume, min_temp, max_temp, min_hum, max_hum):
        return self._execute(sql.SQL("""
            INSERT INTO {} (name, useful_volume, min_temperature, max_temperature,
                            min_humidity, max_humidity)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """).format(self.table_ref), (name, useful_volume, min_temp, max_temp, min_hum, max_hum), returning=True)

    def update_one(self, room_id, name, useful_volume, min_temp, max_temp, min_hum, max_hum):
        return self._execute(sql.SQL("""
            UPDATE {} SET name=%s, useful_volume=%s, min_temperature=%s,
                          max_temperature=%s, min_humidity=%s, max_humidity=%s
            WHERE id=%s RETURNING id
        """).format(self.table_ref),
            (name, useful_volume, min_temp, max_temp, min_hum, max_hum, room_id), returning=True) is not None

    def delete_one(self, room_id, expected_racks, delete_racks=False):
        """Удаление помещения и его стеллажей одной транзакцией после подтверждения."""
        racks_ref = sql.Identifier(self.dbconn.schema, "racks")
        with self.dbconn.conn:
            with self.dbconn.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql.SQL("SELECT id FROM {} WHERE id=%s FOR UPDATE").format(self.table_ref), (room_id,))
                if cursor.fetchone() is None:
                    return False
                cursor.execute(sql.SQL("SELECT COUNT(*) AS total FROM {} WHERE room_id=%s").format(racks_ref), (room_id,))
                actual = cursor.fetchone()["total"]
                if actual != expected_racks:
                    raise DataChangedError("Число стеллажей изменилось. Обновите список и подтвердите заново.")
                if actual and not delete_racks:
                    raise DataChangedError("Удаление связанных стеллажей не подтверждено.")
                if delete_racks:
                    cursor.execute(sql.SQL("DELETE FROM {} WHERE room_id=%s").format(racks_ref), (room_id,))
                cursor.execute(sql.SQL("DELETE FROM {} WHERE id=%s").format(self.table_ref), (room_id,))
                return cursor.rowcount == 1
