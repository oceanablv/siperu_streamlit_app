from models.base import BaseModel
from models.exceptions import DomainValidationError, ResourceUnavailableError
from models.resource import LibraryResource


class KategoriBuku(BaseModel):
    """Kategori untuk pengelompokan buku.

    UML Relationship:
    - Association: satu KategoriBuku dapat digunakan oleh banyak Buku.
      Di kode, relasi ini disimpan sebagai kategori_id pada class Buku.
    - Aggregation/Composition: tidak diterapkan langsung karena KategoriBuku
      tidak menyimpan list objek Buku sebagai atribut internal.
    """

    def __init__(self, id_kategori: str, nama_kategori: str):
        self.id_kategori = str(id_kategori)
        self.nama_kategori = nama_kategori

    def to_dict(self) -> dict:
        return {"id_kategori": self.id_kategori, "nama_kategori": self.nama_kategori}

    @staticmethod
    def from_dict(data: dict):
        return KategoriBuku(data.get("id_kategori", ""), data.get("nama_kategori", ""))


class Buku(LibraryResource, BaseModel):
    """Model buku digital SIPERU.

    OOP - Inheritance:
    Buku mewarisi LibraryResource dan BaseModel.

    OOP - Encapsulation:
    atribut inti disimpan sebagai protected attribute (_judul, _stok, dst.)
    dan diakses melalui property agar validasi tetap terpusat.

    OOP - Polymorphism:
    method kode_resource, nama_resource, dan tersedia punya kontrak sama
    dengan Ruangan, tetapi hasilnya mengikuti konteks buku.

    UML Relationship:
    - Generalization/Inheritance: Buku mewarisi BaseModel dan LibraryResource.
    - Association: Buku berelasi dengan KategoriBuku melalui kategori_id.
    - Association: Buku berelasi dengan PeminjamanBuku dan AntrianBuku melalui
      id_buku pada class transaksi.
    - Composition: tidak diterapkan langsung; Buku tidak menyimpan objek
      KategoriBuku, PeminjamanBuku, atau AntrianBuku sebagai atribut.
    """

    def __init__(
        self,
        id_buku: str,
        judul: str,
        penulis: str,
        penerbit: str,
        tahun_terbit: int,
        stok: int,
        kategori_id: str,
        cover_buku: str = "",
        link_pdf: str = "",
    ):
        self._id_buku = str(id_buku)
        self._judul = judul
        self._penulis = penulis
        self._penerbit = penerbit
        self._tahun_terbit = int(tahun_terbit)
        self._stok = int(stok)
        self._kategori_id = str(kategori_id)
        self._cover_buku = cover_buku
        self._link_pdf = ""
        self.link_pdf = link_pdf

    @property
    def id_buku(self) -> str:
        return self._id_buku

    @property
    def kode_resource(self) -> str:
        return self.id_buku

    @property
    def judul(self) -> str:
        return self._judul

    @judul.setter
    def judul(self, value: str) -> None:
        if not value:
            raise DomainValidationError("Judul buku tidak boleh kosong.")
        self._judul = value

    @property
    def nama_resource(self) -> str:
        return self.judul

    @property
    def penulis(self) -> str:
        return self._penulis

    @penulis.setter
    def penulis(self, value: str) -> None:
        self._penulis = value

    @property
    def penerbit(self) -> str:
        return self._penerbit

    @penerbit.setter
    def penerbit(self, value: str) -> None:
        self._penerbit = value

    @property
    def tahun_terbit(self) -> int:
        return self._tahun_terbit

    @tahun_terbit.setter
    def tahun_terbit(self, value: int) -> None:
        self._tahun_terbit = int(value)

    @property
    def stok(self) -> int:
        return self._stok

    @stok.setter
    def stok(self, value: int) -> None:
        if int(value) < 0:
            raise DomainValidationError("Stok buku tidak boleh negatif.")
        self._stok = int(value)

    @property
    def kategori_id(self) -> str:
        return self._kategori_id

    @kategori_id.setter
    def kategori_id(self, value: str) -> None:
        self._kategori_id = str(value)

    @property
    def cover_buku(self) -> str:
        return self._cover_buku

    @cover_buku.setter
    def cover_buku(self, value: str) -> None:
        self._cover_buku = value

    @property
    def link_pdf(self) -> str:
        return self._link_pdf

    @link_pdf.setter
    def link_pdf(self, value: str) -> None:
        cleaned_value = self.bersihkan_teks(value)
        if cleaned_value and not self.is_valid_pdf_source(cleaned_value):
            raise DomainValidationError("Link PDF harus berupa URL http/https atau path file .pdf.")
        self._link_pdf = cleaned_value

    @staticmethod
    def is_valid_pdf_source(value: str) -> bool:
        """OOP - Static method: validasi tidak membutuhkan state objek."""
        cleaned_value = str(value or "").strip().lower()
        return (
            not cleaned_value
            or cleaned_value.startswith(("http://", "https://"))
            or cleaned_value.endswith(".pdf")
        )

    @classmethod
    def from_pdf_catalog(
        cls,
        id_buku: str,
        judul: str,
        penulis: str,
        penerbit: str,
        tahun_terbit: int,
        stok: int,
        kategori_id: str,
        cover_buku: str,
        link_pdf: str,
    ):
        """OOP - Class method: factory untuk buku yang punya reader PDF."""
        return cls(id_buku, judul, penulis, penerbit, tahun_terbit, stok, kategori_id, cover_buku, link_pdf)

    def cek_stok(self) -> bool:
        return self.stok > 0

    def tersedia(self) -> bool:
        return self.cek_stok()

    def bisa_dibaca_pdf(self) -> bool:
        return bool(self.link_pdf)

    def bisa_dibaca_online(self) -> bool:
        return self.bisa_dibaca_pdf()

    def update_stok(self, perubahan: int) -> None:
        stok_baru = self.stok + int(perubahan)
        if stok_baru < 0:
            raise ResourceUnavailableError("Stok tidak mencukupi.")
        self.stok = stok_baru

    def get_detail(self) -> str:
        return f"{self.judul} - {self.penulis} ({self.tahun_terbit})"

    def to_dict(self) -> dict:
        return {
            "id_buku": self.id_buku,
            "judul": self.judul,
            "penulis": self.penulis,
            "penerbit": self.penerbit,
            "tahun_terbit": self.tahun_terbit,
            "stok": self.stok,
            "kategori_id": self.kategori_id,
            "cover_buku": self.cover_buku,
            "link_pdf": self.link_pdf,
        }

    @staticmethod
    def from_dict(data: dict):
        return Buku(
            id_buku=str(data.get("id_buku", data.get("idBuku", ""))),
            judul=data.get("judul", ""),
            penulis=data.get("penulis", ""),
            penerbit=data.get("penerbit", ""),
            tahun_terbit=int(data.get("tahun_terbit", data.get("tahunTerbit", 0)) or 0),
            stok=int(data.get("stok", 0) or 0),
            kategori_id=str(data.get("kategori_id", data.get("idKategori", ""))),
            cover_buku=data.get("cover_buku", data.get("coverBuku", "")),
            link_pdf=data.get("link_pdf", data.get("pdf_url", data.get("pdf_buku", ""))),
        )
