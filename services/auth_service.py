from models.user import User, Anggota, Admin
from services.helpers import generate_id
from storage.json_storage import JsonStorage


class AuthService:
    """Service untuk autentikasi dan pengelolaan user.

    UML Relationship:
    - Aggregation: AuthService menyimpan referensi user_storage bertipe
      JsonStorage. Storage dibuat di main.py lalu diberikan ke service.
    - Dependency: AuthService menggunakan User, Anggota, dan Admin untuk login,
      register, update profil, dan manajemen anggota.
    - Composition: tidak diterapkan karena AuthService tidak membuat dan
      memiliki lifecycle JsonStorage secara eksklusif.
    """

    def __init__(self, user_storage: JsonStorage):
        self.user_storage = user_storage

    def _load_users(self) -> list[User]:
        return self.user_storage.load()

    def _save_users(self, users: list[User]) -> None:
        self.user_storage.save(users)

    def seed_default_users(self) -> None:
        users = self._load_users()
        if users:
            return
        default_users = [
            Admin(
                id_user="ADM001",
                nama="Admin SIPERU",
                username="admin",
                email="admin@siperu.local",
                password_hash=User.hash_password("admin123"),
                nip="19870001",
                jabatan="Admin Perpustakaan",
            ),
            Anggota(
                id_user="AGT001",
                nama="Anggota Demo",
                username="anggota",
                email="anggota@siperu.local",
                password_hash=User.hash_password("anggota123"),
                nim_nidn="1242002059",
                prodi="Sistem Informasi",
                no_telp="081234567890",
                status_aktif=True,
                kuota_pinjam=3,
            ),
        ]
        self._save_users(default_users)

    def login(self, identifier: str, password: str) -> User:
        identifier = identifier.strip().lower()
        for user in self._load_users():
            if user.username.lower() == identifier or user.email.lower() == identifier:
                if not user.verify_password(password):
                    raise ValueError("Password salah.")
                if isinstance(user, Anggota) and not user.status_aktif:
                    raise ValueError("Akun anggota tidak aktif. Silakan hubungi admin.")
                return user
        raise ValueError("Username/email tidak ditemukan.")

    def register_anggota(self, nama: str, username: str, email: str, password: str, nim_nidn: str, prodi: str, no_telp: str) -> Anggota:
        if not all([nama, username, email, password, nim_nidn, prodi, no_telp]):
            raise ValueError("Semua field register wajib diisi.")
        if len(password) < 6:
            raise ValueError("Password minimal 6 karakter.")
        if "@" not in email:
            raise ValueError("Format email tidak valid.")

        users = self._load_users()
        for user in users:
            if user.username.lower() == username.lower():
                raise ValueError("Username sudah digunakan.")
            if user.email.lower() == email.lower():
                raise ValueError("Email sudah digunakan.")

        new_user = Anggota(
            id_user=generate_id("AGT", [u.id_user for u in users]),
            nama=nama,
            username=username,
            email=email,
            password_hash=User.hash_password(password),
            nim_nidn=nim_nidn,
            prodi=prodi,
            no_telp=no_telp,
            status_aktif=True,
            kuota_pinjam=3,
        )
        users.append(new_user)
        self._save_users(users)
        return new_user

    def list_users(self) -> list[User]:
        return self._load_users()

    def list_members(self) -> list[Anggota]:
        return [user for user in self._load_users() if isinstance(user, Anggota)]

    def get_user(self, id_user: str) -> User | None:
        for user in self._load_users():
            if user.id_user == id_user:
                return user
        return None

    def update_member(self, id_user: str, status_aktif: bool, kuota_pinjam: int) -> bool:
        users = self._load_users()
        for user in users:
            if isinstance(user, Anggota) and user.id_user == id_user:
                user.status_aktif = status_aktif
                user.kuota_pinjam = int(kuota_pinjam)
                self._save_users(users)
                return True
        raise ValueError("Anggota tidak ditemukan.")

    def delete_member(self, id_user: str) -> bool:
        users = self._load_users()
        updated_users = [user for user in users if not (isinstance(user, Anggota) and user.id_user == id_user)]
        if len(updated_users) == len(users):
            raise ValueError("Anggota tidak ditemukan.")
        self._save_users(updated_users)
        return True

    def update_profile(self, id_user: str, nama: str, email: str, prodi: str | None = None, no_telp: str | None = None) -> User:
        users = self._load_users()
        for user in users:
            if user.id_user == id_user:
                user.nama = nama
                user.email = email
                if isinstance(user, Anggota):
                    user.prodi = prodi or user.prodi
                    user.no_telp = no_telp or user.no_telp
                self._save_users(users)
                return user
        raise ValueError("User tidak ditemukan.")

    def change_password(self, id_user: str, old_password: str, new_password: str) -> bool:
        users = self._load_users()
        for user in users:
            if user.id_user == id_user:
                if not user.verify_password(old_password):
                    raise ValueError("Password lama salah.")
                user.change_password(new_password)
                self._save_users(users)
                return True
        raise ValueError("User tidak ditemukan.")
