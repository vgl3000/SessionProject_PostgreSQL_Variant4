-- Необязательные примеры. Повторный запуск не должен дублировать эти строки.
-- Выполнять после sql/01_schema.sql в базе warehouse_session_v4.
INSERT INTO session_v4.rooms
    (name, useful_volume, min_temperature, max_temperature, min_humidity, max_humidity)
SELECT 'Склад 1', 500.00, 15.00, 25.00, 30.00, 60.00
WHERE NOT EXISTS (SELECT 1 FROM session_v4.rooms WHERE name = 'Склад 1');

INSERT INTO session_v4.rooms
    (name, useful_volume, min_temperature, max_temperature, min_humidity, max_humidity)
SELECT 'Склад 2', 600.00, 10.00, 20.00, 30.00, 65.00
WHERE NOT EXISTS (SELECT 1 FROM session_v4.rooms WHERE name = 'Склад 2');

INSERT INTO session_v4.racks
    (rack_number, room_id, places_count, place_height, place_width, place_length, max_load)
SELECT 1, room.id, 10, 1.50, 1.20, 1.00, 1000.00
FROM session_v4.rooms AS room WHERE room.name = 'Склад 1'
AND NOT EXISTS (SELECT 1 FROM session_v4.racks AS rack
                WHERE rack.room_id=room.id AND rack.rack_number=1)
ORDER BY room.id LIMIT 1;

INSERT INTO session_v4.racks
    (rack_number, room_id, places_count, place_height, place_width, place_length, max_load)
SELECT 2, room.id, 12, 1.80, 1.00, 1.20, 1200.00
FROM session_v4.rooms AS room WHERE room.name = 'Склад 2'
AND NOT EXISTS (SELECT 1 FROM session_v4.racks AS rack
                WHERE rack.room_id=room.id AND rack.rack_number=2)
ORDER BY room.id LIMIT 1;

SELECT room.name, rack.rack_number, rack.places_count, rack.max_load
FROM session_v4.rooms AS room
LEFT JOIN session_v4.racks AS rack ON rack.room_id = room.id
ORDER BY room.name, rack.rack_number;
