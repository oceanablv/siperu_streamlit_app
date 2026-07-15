from abc import ABC, abstractmethod


class LibraryResource(ABC):
    """OOP - Abstraction untuk resource perpustakaan.

    OOP - Inheritance:
    class domain seperti Buku dan Ruangan dapat mewarisi kontrak ini.

    OOP - Polymorphism:
    method kode_resource(), nama_resource(), dan tersedia() dipanggil dengan
    nama yang sama, tetapi implementasinya berbeda sesuai resource.
    """

    @property
    @abstractmethod
    def kode_resource(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def nama_resource(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def tersedia(self) -> bool:
        raise NotImplementedError

    def ringkasan_resource(self) -> str:
        """OOP - Polymorphism: bekerja untuk Buku maupun Ruangan.

        Method ini memanggil kontrak abstract yang di-override child class.
        Hasil akhirnya mengikuti implementasi masing-masing child class.
        """
        status = "Tersedia" if self.tersedia() else "Tidak tersedia"
        return f"{self.kode_resource} - {self.nama_resource} ({status})"

    @staticmethod
    def bersihkan_teks(value: str) -> str:
        """OOP - Static method: helper umum tanpa membutuhkan state objek."""
        return str(value or "").strip()
