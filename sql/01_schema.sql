-- Лукьянчиков Валерий Геннадьевич. Вариант 4.
-- Выполните этот файл в pgAdmin Query Tool, подключившись к базе warehouse_session_v4.
-- Схема отдельная: исходные public.rooms / public.racks и другие таблицы не изменяются.
-- Поля повторяют домашнюю работу модуля 1 (добавлены ограничения на положительные размеры).
BEGIN;
CREATE SCHEMA IF NOT EXISTS session_v4;

CREATE TABLE IF NOT EXISTS session_v4.rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    useful_volume NUMERIC(10,2) NOT NULL CHECK (useful_volume > 0),
    min_temperature NUMERIC(5,2),
    max_temperature NUMERIC(5,2),
    min_humidity NUMERIC(5,2),
    max_humidity NUMERIC(5,2),
    CONSTRAINT rooms_name_valid CHECK (
        length(btrim(name)) BETWEEN 1 AND 100 AND name = btrim(name)
    ),
    CONSTRAINT rooms_temperature_order CHECK (min_temperature <= max_temperature),
    CONSTRAINT rooms_min_humidity_range CHECK (min_humidity BETWEEN 0 AND 100),
    CONSTRAINT rooms_max_humidity_range CHECK (max_humidity BETWEEN 0 AND 100),
    CONSTRAINT rooms_humidity_order CHECK (min_humidity <= max_humidity)
);

CREATE TABLE IF NOT EXISTS session_v4.racks (
    id SERIAL PRIMARY KEY,
    rack_number INTEGER NOT NULL CHECK (rack_number > 0),
    room_id INTEGER NOT NULL REFERENCES session_v4.rooms(id) ON DELETE RESTRICT,
    places_count INTEGER NOT NULL CHECK (places_count > 0),
    place_height NUMERIC(10,2) NOT NULL CHECK (place_height > 0),
    place_width NUMERIC(10,2) NOT NULL CHECK (place_width > 0),
    place_length NUMERIC(10,2) NOT NULL CHECK (place_length > 0),
    max_load NUMERIC(10,2) NOT NULL CHECK (max_load > 0),
    CONSTRAINT racks_room_number_unique UNIQUE (room_id, rack_number)
);
COMMIT;

-- Проверка структуры (видна в Data Output pgAdmin):
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'session_v4' AND table_name IN ('rooms', 'racks')
ORDER BY table_name;
