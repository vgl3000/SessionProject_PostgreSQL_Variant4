"""Проверки ввода для варианта 4: склады, помещения и стеллажи."""
import re
import unicodedata
from decimal import Decimal, InvalidOperation


class ValidationError(ValueError):
    """Некорректный пользовательский ввод."""


def room_name(raw):
    if not isinstance(raw, str):
        raise ValidationError("Название помещения должно быть строкой.")
    result = raw.strip()
    if not result or len(result) > 100:
        raise ValidationError("Название помещения: от 1 до 100 символов.")
    if any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for char in result):
        raise ValidationError("Название помещения содержит недопустимые невидимые символы.")
    return result


def positive_integer(raw, title):
    value = str(raw).strip()
    if not (value.isascii() and re.fullmatch(r"\d{1,10}", value)):
        raise ValidationError(f"{title}: введите положительное целое число.")
    number = int(value)
    if not 1 <= number <= 2147483647:
        raise ValidationError(f"{title}: допустимый диапазон от 1 до 2147483647.")
    return number


def decimal_number(raw, title, minimum, maximum):
    value = str(raw).strip().replace(",", ".")
    if len(value) > 20 or not re.fullmatch(r"[+-]?\d+(?:\.\d{1,2})?", value, re.ASCII):
        raise ValidationError(f"{title}: число с точностью до двух знаков после запятой.")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValidationError(f"{title}: некорректное число.") from exc
    if not Decimal(str(minimum)) <= number <= Decimal(str(maximum)):
        raise ValidationError(f"{title}: допустимо от {minimum} до {maximum}.")
    return number.quantize(Decimal("0.01"))


def volume(raw):
    return decimal_number(raw, "Полезный объём", "0.01", "99999999.99")


def temperature(raw):
    return decimal_number(raw, "Температура", "-999.99", "999.99")


def humidity(raw):
    return decimal_number(raw, "Влажность", "0.00", "100.00")


def nullable(validator):
    """Разрешить пустой ввод как SQL NULL (в режиме создания)."""
    def wrapper(value):
        if not str(value).strip():
            return None
        return validator(value)
    return wrapper


def room_environment(min_temp, max_temp, min_humidity, max_humidity):
    """Проверить отношения значений до выполнения запроса SQL."""
    if min_temp is not None and max_temp is not None and min_temp > max_temp:
        raise ValidationError("Минимальная температура выше максимальной.")
    if min_humidity is not None and max_humidity is not None and min_humidity > max_humidity:
        raise ValidationError("Минимальная влажность выше максимальной.")


def rack_number(raw):
    return positive_integer(raw, "Номер стеллажа")


def places_count(raw):
    return positive_integer(raw, "Количество мест")


def dimension(raw):
    return decimal_number(raw, "Размер места", "0.01", "99999999.99")


def max_load(raw):
    return decimal_number(raw, "Максимальная нагрузка", "0.01", "99999999.99")
