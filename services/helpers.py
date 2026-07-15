from datetime import datetime


def generate_id(prefix: str, existing_ids: list[str]) -> str:
    numbers = []
    for item_id in existing_ids:
        item_id = str(item_id)
        if item_id.startswith(prefix):
            number_part = item_id.replace(prefix, "", 1)
            if number_part.isdigit():
                numbers.append(int(number_part))
    next_number = max(numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def now_date() -> str:
    return datetime.now().date().isoformat()
