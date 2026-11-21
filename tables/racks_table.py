"""Стеллажи, привязанные к конкретному помещению."""
from psycopg2 import sql
from dbtable import DbTable


class RacksTable(DbTable):
    table = "racks"

    def create(self):
        query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                id SERIAL PRIMARY KEY,
                rack_number INTEGER NOT NULL CHECK (rack_number > 0),
                room_id INTEGER NOT NULL REFERENCES {} (id) ON DELETE RESTRICT,
                places_count INTEGER NOT NULL CHECK (places_count > 0),
                place_height NUMERIC(10, 2) NOT NULL CHECK (place_height > 0),
                place_width NUMERIC(10, 2) NOT NULL CHECK (place_width > 0),
                place_length NUMERIC(10, 2) NOT NULL CHECK (place_length > 0),
                max_load NUMERIC(10, 2) NOT NULL CHECK (max_load > 0),
                CONSTRAINT racks_room_number_unique UNIQUE (room_id, rack_number)
            )
        """).format(self.table_ref, sql.Identifier(self.dbconn.schema, "rooms"))
        with self.dbconn.conn:
            with self.dbconn.conn.cursor() as cursor:
                cursor.execute(query)

    def count_by_room(self, room_id):
        return self._one(sql.SQL("SELECT COUNT(*) AS total FROM {} WHERE room_id=%s").format(self.table_ref), (room_id,))["total"]

    def list_by_room(self, room_id):
        return self._all(sql.SQL("""
            SELECT id, rack_number, places_count, place_height, place_width,
                   place_length, max_load FROM {} WHERE room_id=%s
            ORDER BY rack_number, id
        """).format(self.table_ref), (room_id,))

    def get_in_room(self, rack_id, room_id):
        return self._one(sql.SQL("""
            SELECT id, rack_number, places_count, place_height, place_width,
                   place_length, max_load FROM {} WHERE id=%s AND room_id=%s
        """).format(self.table_ref), (rack_id, room_id))

    def insert_one(self, room_id, rack_number, places_count, height, width, length, load):
        return self._execute(sql.SQL("""
            INSERT INTO {} (room_id, rack_number, places_count, place_height,
                            place_width, place_length, max_load)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """).format(self.table_ref),
            (room_id, rack_number, places_count, height, width, length, load), returning=True)

    def delete_one(self, rack_id, room_id):
        return self._execute(
            sql.SQL("DELETE FROM {} WHERE id=%s AND room_id=%s").format(self.table_ref),
            (rack_id, room_id)
        ) == 1
