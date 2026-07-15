import hashlib
from typing import Any
from models.base import BaseModel


class User(BaseModel):
    """Class induk untuk pengguna sistem.

    OOP - Encapsulation diterapkan dengan atribut protected/private dan akses melalui property.
    OOP - Inheritance diterapkan oleh class Anggota dan Admin.
    OOP - Polymorphism terlihat pada method dashboard_title() yang dioverride oleh child class.

    UML Relationship:
    - Generalization/Inheritance: Anggota dan Admin adalah turunan dari User.
    - Association: objek User dipakai oleh AuthService dan ReportService untuk proses login,
      pengelolaan anggota, dan laporan.
    """

    def __init__(self, id_user: str, nama: str, username: str, email: str, password_hash: str, role: str):
        self._id_user = str(id_user)
        self._nama = nama
        self._username = username
        self._email = email
        self.__password_hash = password_hash
        self._role = role

    @property
    def id_user(self) -> str:
        return self._id_user

    @property
    def nama(self) -> str:
        return self._nama

    @nama.setter
    def nama(self, value: str) -> None:
        if not value:
            raise ValueError("Nama tidak boleh kosong.")
        self._nama = value

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if "@" not in value:
            raise ValueError("Format email tidak valid.")
        self._email = value

    @property
    def role(self) -> str:
        return self._role

    def verify_password(self, password: str) -> bool:
        return self.__password_hash == self.hash_password(password)

    def change_password(self, new_password: str) -> None:
        if len(new_password) < 6:
            raise ValueError("Password minimal 6 karakter.")
        self.__password_hash = self.hash_password(new_password)

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def dashboard_title(self) -> str:
        return f"Dashboard {self.role.title()}"

    def logout(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {
            "id_user": self.id_user,
            "nama": self.nama,
            "username": self.username,
            "email": self.email,
            "password_hash": self.__password_hash,
            "role": self.role,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]):
        role = data.get("role", "anggota")
        password_hash = data.get("password_hash") or User.hash_password(data.get("password", "password123"))

        if role == "admin":
            return Admin(
                id_user=str(data.get("id_user", "")),
                nama=data.get("nama", ""),
                username=data.get("username", ""),
                email=data.get("email", ""),
                password_hash=password_hash,
                nip=str(data.get("nip", "")),
                jabatan=data.get("jabatan", "Admin Perpustakaan"),
            )

        return Anggota(
            id_user=str(data.get("id_user", "")),
            nama=data.get("nama", ""),
            username=data.get("username", ""),
            email=data.get("email", ""),
            password_hash=password_hash,
            nim_nidn=str(data.get("nim_nidn", data.get("nimNidn", ""))),
            prodi=data.get("prodi", ""),
            no_telp=str(data.get("no_telp", data.get("noTelp", ""))),
            status_aktif=bool(data.get("status_aktif", True)),
            kuota_pinjam=int(data.get("kuota_pinjam", data.get("kuotaPinjam", 3))),
        )


class Anggota(User):
    """Representasi anggota perpustakaan.

    UML Relationship:
    - Generalization/Inheritance: Anggota mewarisi atribut dan method dari User.
    - Association: Anggota berelasi dengan PeminjamanBuku, AntrianBuku, dan
      ReservasiRuangan melalui field id_anggota pada class transaksi.
    - Composition: tidak diterapkan langsung; Anggota tidak menyimpan objek
      transaksi sebagai bagian internalnya.
    """

    def __init__(
        self,
        id_user: str,
        nama: str,
        username: str,
        email: str,
        password_hash: str,
        nim_nidn: str,
        prodi: str,
        no_telp: str,
        status_aktif: bool = True,
        kuota_pinjam: int = 3,
    ):
        super().__init__(id_user, nama, username, email, password_hash, "anggota")
        self._nim_nidn = str(nim_nidn)
        self._prodi = prodi
        self._no_telp = str(no_telp)
        self._status_aktif = status_aktif
        self._kuota_pinjam = int(kuota_pinjam)

    @property
    def nim_nidn(self) -> str:
        return self._nim_nidn

    @property
    def prodi(self) -> str:
        return self._prodi

    @prodi.setter
    def prodi(self, value: str) -> None:
        self._prodi = value

    @property
    def no_telp(self) -> str:
        return self._no_telp

    @no_telp.setter
    def no_telp(self, value: str) -> None:
        self._no_telp = value

    @property
    def status_aktif(self) -> bool:
        return self._status_aktif

    @status_aktif.setter
    def status_aktif(self, value: bool) -> None:
        self._status_aktif = bool(value)

    @property
    def kuota_pinjam(self) -> int:
        return self._kuota_pinjam

    @kuota_pinjam.setter
    def kuota_pinjam(self, value: int) -> None:
        if int(value) < 0:
            raise ValueError("Kuota pinjam tidak boleh negatif.")
        self._kuota_pinjam = int(value)

    def dashboard_title(self) -> str:
        return "Dashboard Anggota SIPERU"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(
            {
                "nim_nidn": self.nim_nidn,
                "prodi": self.prodi,
                "no_telp": self.no_telp,
                "status_aktif": self.status_aktif,
                "kuota_pinjam": self.kuota_pinjam,
            }
        )
        return data


class Admin(User):
    """Representasi admin perpustakaan.

    UML Relationship:
    - Generalization/Inheritance: Admin mewarisi atribut dan method dari User.
    - Association/Dependency: Admin mengelola buku, ruangan, anggota, reservasi,
      dan laporan melalui service pada layer aplikasi, bukan melalui atribut
      langsung di class Admin.
    - Composition: tidak diterapkan langsung pada Admin.
    """

    def __init__(
        self,
        id_user: str,
        nama: str,
        username: str,
        email: str,
        password_hash: str,
        nip: str,
        jabatan: str,
    ):
        super().__init__(id_user, nama, username, email, password_hash, "admin")
        self._nip = str(nip)
        self._jabatan = jabatan

    @property
    def nip(self) -> str:
        return self._nip

    @property
    def jabatan(self) -> str:
        return self._jabatan

    @jabatan.setter
    def jabatan(self, value: str) -> None:
        self._jabatan = value

    def dashboard_title(self) -> str:
        return "Dashboard Admin SIPERU"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({"nip": self.nip, "jabatan": self.jabatan})
        return data
