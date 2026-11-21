"""Соединение с PostgreSQL. Пароль не записывается в сообщения об ошибках."""

import psycopg2


class DbConnection:
    def __init__(self, config):
        self.schema = config.schema
        self.conn = psycopg2.connect(
            dbname=config.dbname,
            user=config.user,
            password=config.password,
            host=config.host,
            port=int(config.port),
            connect_timeout=8,
        )

    def close(self):
        if not self.conn.closed:
            self.conn.close()
