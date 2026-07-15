from models.base import BaseModel
from models.exceptions import DomainValidationError
from models.resource import LibraryResource


class Ruangan(LibraryResource, BaseModel):
    """Model ruangan perpustakaan SIPERU.

    OOP - Inheritance:
    Ruangan mewarisi LibraryResource dan BaseModel seperti Buku.

    OOP - Encapsulation:
    atribut ruangan disimpan sebagai protected attribute dan diakses
    melalui property agar validasi tetap terpusat.

    OOP - Polymorphism:
    method kode_resource, nama_resource, dan tersedia punya nama yang sama
    dengan Buku, tetapi logikanya memakai status ketersediaan ruangan.

    UML Relationship:
    - Generalization/Inheritance: Ruangan mewarisi BaseModel dan LibraryResource.
    - Association: Ruangan berelasi dengan ReservasiRuangan melalui id_ruangan
      pada class ReservasiRuangan.
    - Association: Ruangan berelasi dengan JadwalRuangan melalui id_ruangan
      pada class JadwalRuangan.
    - Composition: tidak diterapkan langsung; Ruangan tidak menyimpan objek
      ReservasiRuangan atau JadwalRuangan sebagai atribut internal.
    """

    def __init__(self, id_ruangan: str, nama_ruangan: str, kapasitas: int, lokasi: str, fasilitas: str, status_ruangan: str = "Tersedia"):
        self._id_ruangan = str(id_ruangan)
        self._nama_ruangan = nama_ruangan
        self._kapasitas = int(kapasitas)
        self._lokasi = lokasi
        self._fasilitas = fasilitas
        self._status_ruangan = status_ruangan

    @property
    def id_ruangan(self) -> str:
        return self._id_ruangan

    @property
    def kode_resource(self) -> str:
        return self.id_ruangan

    @property
    def nama_ruangan(self) -> str:
        return self._nama_ruangan

    @nama_ruangan.setter
    def nama_ruangan(self, value: str) -> None:
        if not value:
            raise DomainValidationError("Nama ruangan tidak boleh kosong.")
        self._nama_ruangan = value

    @property
    def nama_resource(self) -> str:
        return self.nama_ruangan

    @property
    def kapasitas(self) -> int:
        return self._kapasitas

    @kapasitas.setter
    def kapasitas(self, value: int) -> None:
        if int(value) <= 0:
            raise DomainValidationError("Kapasitas harus lebih dari 0.")
        self._kapasitas = int(value)

    @property
    def lokasi(self) -> str:
        return self._lokasi

    @lokasi.setter
    def lokasi(self, value: str) -> None:
        self._lokasi = value

    @property
    def fasilitas(self) -> str:
        return self._fasilitas

    @fasilitas.setter
    def fasilitas(self, value: str) -> None:
        self._fasilitas = value

    @property
    def status_ruangan(self) -> str:
        return self._status_ruangan

    @status_ruangan.setter
    def status_ruangan(self, value: str) -> None:
        self._status_ruangan = value

    def cek_ketersediaan(self) -> bool:
        return self.status_ruangan.lower() == "tersedia"

    def tersedia(self) -> bool:
        return self.cek_ketersediaan()

    def update_status(self, status_baru: str) -> None:
        self.status_ruangan = status_baru

    def get_detail_ruangan(self) -> str:
        return f"{self.nama_ruangan} | Kapasitas {self.kapasitas} | {self.lokasi}"

    def to_dict(self) -> dict:
        return {
            "id_ruangan": self.id_ruangan,
            "nama_ruangan": self.nama_ruangan,
            "kapasitas": self.kapasitas,
            "lokasi": self.lokasi,
            "fasilitas": self.fasilitas,
            "status_ruangan": self.status_ruangan,
        }

    @staticmethod
    def from_dict(data: dict):
        return Ruangan(
            id_ruangan=str(data.get("id_ruangan", data.get("idRuangan", ""))),
            nama_ruangan=data.get("nama_ruangan", data.get("namaRuangan", "")),
            kapasitas=int(data.get("kapasitas", 0) or 0),
            lokasi=data.get("lokasi", ""),
            fasilitas=data.get("fasilitas", ""),
            status_ruangan=data.get("status_ruangan", data.get("statusRuangan", "Tersedia")),
        )


class JadwalRuangan(BaseModel):
    """Jadwal ketersediaan ruangan.

    UML Relationship:
    - Generalization/Inheritance: JadwalRuangan mewarisi BaseModel.
    - Association: JadwalRuangan berelasi dengan Ruangan melalui id_ruangan.
    - Aggregation/Composition: tidak diterapkan langsung karena jadwal tidak
      menyimpan objek Ruangan, hanya menyimpan id_ruangan.

    Catatan implementasi:
    - Class ini sudah ada sebagai model, tetapi belum dipakai oleh service atau
      storage utama aplikasi.
    """

    def __init__(self, id_jadwal: str, id_ruangan: str, tanggal: str, jam_mulai: str, jam_selesai: str, status_jadwal: str = "Terisi"):
        self.id_jadwal = str(id_jadwal)
        self.id_ruangan = str(id_ruangan)
        self.tanggal = tanggal
        self.jam_mulai = jam_mulai
        self.jam_selesai = jam_selesai
        self.status_jadwal = status_jadwal

    def cek_jadwal(self) -> bool:
        return self.status_jadwal.lower() == "kosong"

    def to_dict(self) -> dict:
        return {
            "id_jadwal": self.id_jadwal,
            "id_ruangan": self.id_ruangan,
            "tanggal": self.tanggal,
            "jam_mulai": self.jam_mulai,
            "jam_selesai": self.jam_selesai,
            "status_jadwal": self.status_jadwal,
        }

    @staticmethod
    def from_dict(data: dict):
        return JadwalRuangan(
            id_jadwal=str(data.get("id_jadwal", data.get("idJadwal", ""))),
            id_ruangan=str(data.get("id_ruangan", data.get("idRuangan", ""))),
            tanggal=str(data.get("tanggal", "")),
            jam_mulai=str(data.get("jam_mulai", data.get("jamMulai", ""))),
            jam_selesai=str(data.get("jam_selesai", data.get("jamSelesai", ""))),
            status_jadwal=data.get("status_jadwal", data.get("statusJadwal", "Terisi")),
        )
