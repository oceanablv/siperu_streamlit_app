from abc import ABC, abstractmethod


class BaseModel(ABC):
    """OOP - Abstraction: abstract class untuk seluruh model SIPERU."""

    @abstractmethod
    def to_dict(self) -> dict:
        """Mengubah objek menjadi dictionary agar dapat disimpan ke JSON."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def from_dict(data: dict):
        """Membuat objek dari dictionary hasil baca JSON."""
        raise NotImplementedError
