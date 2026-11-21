"""Настройки подключения, которые считываются рядом с исходным кодом."""

import os
from pathlib import Path

import yaml


class ConfigError(Exception):
    """Отсутствует конфигурация либо в ней указаны неверные параметры."""


class ProjectConfig:
    def __init__(self, path=None):
        location = Path(path) if path is not None else Path(__file__).resolve().parent / "config.yaml"
        try:
            with location.open(encoding="utf-8") as stream:
                options = yaml.safe_load(stream)
        except (OSError, yaml.YAMLError) as exc:
            raise ConfigError("Не удалось прочитать config.yaml. Проверьте файл настроек.") from exc

        if not isinstance(options, dict):
            raise ConfigError("config.yaml должен содержать параметры подключения.")

        def get(name, env, default=None):
            result = os.environ.get(env, options.get(name, default))
            if result is None:
                raise ConfigError(f"В config.yaml не указан параметр {name}.")
            return str(result)

        self.dbname = get("dbname", "PGDATABASE")
        self.user = get("user", "PGUSER")
        self.password = get("password", "PGPASSWORD", "")
        self.host = get("host", "PGHOST", "localhost")
        self.port = get("port", "PGPORT", "5432")

        # Поддерживаем старое имя параметра эталонного проекта.
        old_prefix = str(options.get("dbtableprefix", "public.")).rstrip(".")
        self.schema = get("schema", "PGSCHEMA", old_prefix)
        for key in ("dbname", "user", "host", "schema"):
            if not getattr(self, key).strip():
                raise ConfigError(f"Параметр {key} не может быть пустым.")
        if not self.port.isdecimal() or not 1 <= int(self.port) <= 65535:
            raise ConfigError("port должен быть числом от 1 до 65535.")


if __name__ == "__main__":
    config = ProjectConfig()
    print("Конфигурация считана. База:", config.dbname, "схема:", config.schema)
