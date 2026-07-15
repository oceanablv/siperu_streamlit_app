from abc import abstractmethod
from datetime import date, datetime, timedelta
from models.base import BaseModel


class TransaksiBase(BaseModel):
    """OOP - Abstraction untuk seluruh transaksi SIPERU.

    OOP - Polymorphism:
    setiap child class wajib memiliki ringkasan_transaksi(), tetapi isi
    ringkasannya berbeda sesuai jenis transaksi.

    UML Relationship:
    - Generalization/Inheritance: PeminjamanBuku, AntrianBuku, dan
      ReservasiRuangan adalah turunan dari TransaksiBase.
    - Composition: tidak diterapkan di level ini karena TransaksiBase hanya
      mendefinisikan kontrak method, bukan memiliki objek transaksi lain.
    """

    @abstractmethod
    def ringkasan_transaksi(self) -> str:
        raise NotImplementedError


class PeminjamanBuku(TransaksiBase):
    """Transaksi peminjaman buku oleh anggota.

    OOP - Inheritance: PeminjamanBuku mewarisi kontrak TransaksiBase.

    UML Relationship:
    - Generalization/Inheritance: PeminjamanBuku adalah turunan TransaksiBase.
    - Association: berelasi dengan Buku melalui id_buku.
    - Association: berelasi dengan Anggota melalui id_anggota.
    - Composition: tidak diterapkan langsung; objek Buku dan Anggota tidak
      disimpan sebagai atribut, hanya direferensikan menggunakan ID.
    """

    def __init__(
        self,
        id_peminjaman_buku: str,
        id_buku: str,
        id_anggota: str,
        tanggal_pinjam: str,
        tanggal_kembali: str,
        status_peminjaman: str = "Dipinjam",
        denda: float = 0.0,
        tanggal_dikembalikan: str = "",
    ):
        self.id_peminjaman_buku = str(id_peminjaman_buku)
        self.id_buku = str(id_buku)
        self.id_anggota = str(id_anggota)
        self.tanggal_pinjam = tanggal_pinjam
        self.tanggal_kembali = tanggal_kembali
        self.status_peminjaman = status_peminjaman
        self.denda = float(denda)
        self.tanggal_dikembalikan = tanggal_dikembalikan

    @classmethod
    def buat_baru(
        cls,
        id_peminjaman_buku: str,
        id_buku: str,
        id_anggota: str,
        tanggal_pinjam: date,
        lama_pinjam_hari: int,
    ):
        """OOP - Class method: factory transaksi peminjaman baru."""
        tanggal_kembali = tanggal_pinjam + timedelta(days=lama_pinjam_hari)
        return cls(
            id_peminjaman_buku=id_peminjaman_buku,
            id_buku=id_buku,
            id_anggota=id_anggota,
            tanggal_pinjam=tanggal_pinjam.isoformat(),
            tanggal_kembali=tanggal_kembali.isoformat(),
            status_peminjaman="Dipinjam",
            denda=0,
        )

    def validasi_peminjaman(self) -> bool:
        return self.status_peminjaman in ["Dipinjam", "Dikembalikan", "Terlambat"]

    def sedang_dipinjam(self) -> bool:
        return self.status_peminjaman == "Dipinjam"

    def ringkasan_transaksi(self) -> str:
        return f"Peminjaman {self.id_peminjaman_buku}: buku {self.id_buku} sampai {self.tanggal_kembali}"

    def proses_pengembalian(self, tanggal_pengembalian: str | None = None, tarif_denda: float = 2000.0) -> float:
        tanggal_pengembalian = tanggal_pengembalian or date.today().isoformat()
        self.tanggal_dikembalikan = tanggal_pengembalian
        self.denda = self.hitung_denda(tanggal_pengembalian, tarif_denda)
        self.status_peminjaman = "Terlambat" if self.denda > 0 else "Dikembalikan"
        return self.denda

    def hitung_denda(self, tanggal_pengembalian: str | None = None, tarif_denda: float = 2000.0) -> float:
        tanggal_pengembalian = tanggal_pengembalian or date.today().isoformat()
        batas = datetime.strptime(self.tanggal_kembali, "%Y-%m-%d").date()
        kembali = datetime.strptime(tanggal_pengembalian, "%Y-%m-%d").date()
        terlambat = max((kembali - batas).days, 0)
        return float(terlambat * tarif_denda)

    def to_dict(self) -> dict:
        return {
            "id_peminjaman_buku": self.id_peminjaman_buku,
            "id_buku": self.id_buku,
            "id_anggota": self.id_anggota,
            "tanggal_pinjam": self.tanggal_pinjam,
            "tanggal_kembali": self.tanggal_kembali,
            "status_peminjaman": self.status_peminjaman,
            "denda": self.denda,
            "tanggal_dikembalikan": self.tanggal_dikembalikan,
        }

    @staticmethod
    def from_dict(data: dict):
        return PeminjamanBuku(
            id_peminjaman_buku=str(data.get("id_peminjaman_buku", data.get("idPeminjamanBuku", ""))),
            id_buku=str(data.get("id_buku", data.get("idBuku", ""))),
            id_anggota=str(data.get("id_anggota", data.get("idAnggota", ""))),
            tanggal_pinjam=str(data.get("tanggal_pinjam", data.get("tanggalPinjam", ""))),
            tanggal_kembali=str(data.get("tanggal_kembali", data.get("tanggalKembali", ""))),
            status_peminjaman=data.get("status_peminjaman", data.get("statusPeminjaman", "Dipinjam")),
            denda=float(data.get("denda", 0) or 0),
            tanggal_dikembalikan=str(data.get("tanggal_dikembalikan", "")),
        )


class AntrianBuku(TransaksiBase):
    """Transaksi antrian ketika stok buku habis.

    UML Relationship:
    - Generalization/Inheritance: AntrianBuku adalah turunan TransaksiBase.
    - Association: berelasi dengan Buku melalui id_buku.
    - Association: berelasi dengan Anggota melalui id_anggota.
    - Composition: tidak diterapkan langsung; objek Buku dan Anggota tidak
      menjadi bagian internal dari AntrianBuku.
    """

    def __init__(self, id_antrian: str, id_buku: str, id_anggota: str, tanggal_daftar: str, urutan: int, status_antrian: str = "Menunggu"):
        self.id_antrian = str(id_antrian)
        self.id_buku = str(id_buku)
        self.id_anggota = str(id_anggota)
        self.tanggal_daftar = tanggal_daftar
        self.urutan = int(urutan)
        self.status_antrian = status_antrian

    def cek_urutan(self) -> int:
        return self.urutan

    def ringkasan_transaksi(self) -> str:
        return f"Antrian {self.id_antrian}: buku {self.id_buku} urutan {self.urutan}"

    def to_dict(self) -> dict:
        return {
            "id_antrian": self.id_antrian,
            "id_buku": self.id_buku,
            "id_anggota": self.id_anggota,
            "tanggal_daftar": self.tanggal_daftar,
            "urutan": self.urutan,
            "status_antrian": self.status_antrian,
        }

    @staticmethod
    def from_dict(data: dict):
        return AntrianBuku(
            id_antrian=str(data.get("id_antrian", data.get("idAntrian", ""))),
            id_buku=str(data.get("id_buku", data.get("idBuku", ""))),
            id_anggota=str(data.get("id_anggota", data.get("idAnggota", ""))),
            tanggal_daftar=str(data.get("tanggal_daftar", data.get("tanggalDaftar", ""))),
            urutan=int(data.get("urutan", 1) or 1),
            status_antrian=data.get("status_antrian", data.get("statusAntrian", "Menunggu")),
        )


class ReservasiRuangan(TransaksiBase):
    """Transaksi reservasi ruangan oleh anggota.

    UML Relationship:
    - Generalization/Inheritance: ReservasiRuangan adalah turunan TransaksiBase.
    - Association: berelasi dengan Ruangan melalui id_ruangan.
    - Association: berelasi dengan Anggota melalui id_anggota.
    - Composition: tidak diterapkan langsung; objek Ruangan dan Anggota tidak
      disimpan sebagai atribut, hanya direferensikan menggunakan ID.
    """

    def __init__(
        self,
        id_reservasi: str,
        id_ruangan: str,
        id_anggota: str,
        tanggal_reservasi: str,
        jam_mulai: str,
        jam_selesai: str,
        keperluan: str,
        status_reservasi: str = "Menunggu",
    ):
        self.id_reservasi = str(id_reservasi)
        self.id_ruangan = str(id_ruangan)
        self.id_anggota = str(id_anggota)
        self.tanggal_reservasi = tanggal_reservasi
        self.jam_mulai = jam_mulai
        self.jam_selesai = jam_selesai
        self.keperluan = keperluan
        self.status_reservasi = status_reservasi

    def konfirmasi_reservasi(self) -> None:
        self.status_reservasi = "Dikonfirmasi"

    def batalkan_reservasi(self) -> None:
        self.status_reservasi = "Dibatalkan"

    def ringkasan_transaksi(self) -> str:
        return f"Reservasi {self.id_reservasi}: ruangan {self.id_ruangan} pada {self.tanggal_reservasi}"

    def to_dict(self) -> dict:
        return {
            "id_reservasi": self.id_reservasi,
            "id_ruangan": self.id_ruangan,
            "id_anggota": self.id_anggota,
            "tanggal_reservasi": self.tanggal_reservasi,
            "jam_mulai": self.jam_mulai,
            "jam_selesai": self.jam_selesai,
            "keperluan": self.keperluan,
            "status_reservasi": self.status_reservasi,
        }

    @staticmethod
    def from_dict(data: dict):
        return ReservasiRuangan(
            id_reservasi=str(data.get("id_reservasi", data.get("idReservasi", ""))),
            id_ruangan=str(data.get("id_ruangan", data.get("idRuangan", ""))),
            id_anggota=str(data.get("id_anggota", data.get("idAnggota", ""))),
            tanggal_reservasi=str(data.get("tanggal_reservasi", data.get("tanggalReservasi", ""))),
            jam_mulai=str(data.get("jam_mulai", data.get("jamMulai", ""))),
            jam_selesai=str(data.get("jam_selesai", data.get("jamSelesai", ""))),
            keperluan=data.get("keperluan", ""),
            status_reservasi=data.get("status_reservasi", data.get("statusReservasi", "Menunggu")),
        )
