import json
from pathlib import Path
from typing import Iterable


class JsonStorage:
    """Generic JSON storage untuk menyimpan list data model SIPERU.

    UML Relationship:
    - Aggregation: service class menyimpan referensi JsonStorage untuk akses
      data, tetapi JsonStorage tidak bergantung pada satu service tertentu.
    - Dependency: JsonStorage bergantung pada model_cls untuk mengubah data
      dictionary menjadi objek model melalui from_dict().
    - Composition: tidak diterapkan pada objek domain; file JSON tetap ada
      walaupun objek JsonStorage/service sudah tidak aktif.
    """

    def __init__(self, file_path: str | Path, model_cls=None):
        self.file_path = Path(file_path)
        self.model_cls = model_cls
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.save_raw([])

    def load_raw(self) -> list[dict]:
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            return []
        with open(self.file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                return []
        return data if isinstance(data, list) else []

    def save_raw(self, records: list[dict]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=4, ensure_ascii=False)

    def load(self) -> list:
        records = self.load_raw()
        if self.model_cls is None:
            return records
        return [self.model_cls.from_dict(record) for record in records]

    def save(self, items: Iterable) -> None:
        records = []
        for item in items:
            records.append(item.to_dict() if hasattr(item, "to_dict") else dict(item))
        self.save_raw(records)
