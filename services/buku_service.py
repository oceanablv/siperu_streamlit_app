import re
from pathlib import Path

from config import BASE_DIR, PDFS_DIR
from models.buku import Buku, KategoriBuku
from services.helpers import generate_id
from storage.json_storage import JsonStorage


class BukuService:
    """Service untuk pengelolaan buku dan kategori.

    UML Relationship:
    - Aggregation: BukuService menyimpan referensi book_storage dan
      category_storage bertipe JsonStorage.
    - Dependency: BukuService menggunakan Buku dan KategoriBuku untuk operasi
      tambah, ubah, hapus, pencarian, dan import data.
    - Association: relasi Buku-KategoriBuku tetap disimpan melalui kategori_id.
    - Composition: tidak diterapkan karena service tidak memiliki lifecycle
      eksklusif atas objek Buku, KategoriBuku, atau JsonStorage.
    """

    def __init__(self, book_storage: JsonStorage, category_storage: JsonStorage):
        self.book_storage = book_storage
        self.category_storage = category_storage

    def seed_default_data(self) -> None:
        if not self.category_storage.load():
            self.category_storage.save(
                [
                    KategoriBuku("KAT001", "Teknologi Informasi"),
                    KategoriBuku("KAT002", "Manajemen"),
                    KategoriBuku("KAT003", "Umum"),
                ]
            )
        if not self.book_storage.load():
            self.book_storage.save(
                [
                    Buku("BK001", "Object-Oriented Programming", "R. Nugroho", "Informatika", 2022, 5, "KAT001", "assets/covers/bk001.png"),
                    Buku("BK002", "Analisis dan Perancangan Sistem", "S. Hartono", "Graha Ilmu", 2021, 3, "KAT001", "assets/covers/bk002.png"),
                    Buku("BK003", "Manajemen Operasi", "A. Wijaya", "Salemba", 2020, 2, "KAT002", "assets/covers/bk003.png"),
                ]
            )

    def list_books(self) -> list[Buku]:
        return self.book_storage.load()

    def list_categories(self) -> list[KategoriBuku]:
        return self.category_storage.load()

    def category_map(self) -> dict[str, str]:
        return {kategori.id_kategori: kategori.nama_kategori for kategori in self.list_categories()}

    @staticmethod
    def safe_asset_filename(filename: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name).strip("._")
        return cleaned or "buku.pdf"

    def save_pdf_upload(self, uploaded_file) -> str:
        if uploaded_file is None:
            return ""

        if not uploaded_file.name.lower().endswith(".pdf"):
            raise ValueError("File PDF harus berformat .pdf.")

        PDFS_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = self.safe_asset_filename(uploaded_file.name)
        target_path = PDFS_DIR / safe_name
        stem = target_path.stem
        suffix = target_path.suffix
        counter = 1

        while target_path.exists():
            target_path = PDFS_DIR / f"{stem}_{counter}{suffix}"
            counter += 1

        with open(target_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        return target_path.resolve().relative_to(BASE_DIR.resolve()).as_posix()

    def get_book(self, id_buku: str) -> Buku | None:
        for buku in self.list_books():
            if buku.id_buku == id_buku:
                return buku
        return None

    def search_books(self, keyword: str = "", kategori_id: str = "Semua") -> list[Buku]:
        keyword = keyword.lower().strip()
        results = []
        for buku in self.list_books():
            cocok_keyword = not keyword or keyword in buku.judul.lower() or keyword in buku.penulis.lower() or keyword in buku.penerbit.lower()
            cocok_kategori = kategori_id == "Semua" or buku.kategori_id == kategori_id
            if cocok_keyword and cocok_kategori:
                results.append(buku)
        return results

    def add_category(self, nama_kategori: str) -> KategoriBuku:
        if not nama_kategori:
            raise ValueError("Nama kategori tidak boleh kosong.")
        categories = self.list_categories()
        new_category = KategoriBuku(generate_id("KAT", [c.id_kategori for c in categories]), nama_kategori)
        categories.append(new_category)
        self.category_storage.save(categories)
        return new_category

    def add_book(
        self,
        judul: str,
        penulis: str,
        penerbit: str,
        tahun_terbit: int,
        stok: int,
        kategori_id: str,
        cover_buku: str = "",
        link_pdf: str = "",
    ) -> Buku:
        if not judul:
            raise ValueError("Judul buku tidak boleh kosong.")
        if int(stok) < 0:
            raise ValueError("Stok tidak boleh negatif.")
        books = self.list_books()
        new_book = Buku.from_pdf_catalog(
            generate_id("BK", [b.id_buku for b in books]),
            judul,
            penulis,
            penerbit,
            int(tahun_terbit),
            int(stok),
            kategori_id,
            cover_buku,
            link_pdf,
        )
        books.append(new_book)
        self.book_storage.save(books)
        return new_book

    def update_book(
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
    ) -> bool:
        books = self.list_books()
        for buku in books:
            if buku.id_buku == id_buku:
                buku.judul = judul
                buku.penulis = penulis
                buku.penerbit = penerbit
                buku.tahun_terbit = tahun_terbit
                buku.stok = stok
                buku.kategori_id = kategori_id
                buku.cover_buku = cover_buku
                buku.link_pdf = link_pdf
                self.book_storage.save(books)
                return True
        raise ValueError("Buku tidak ditemukan.")

    def delete_book(self, id_buku: str) -> bool:
        books = self.list_books()
        updated = [b for b in books if b.id_buku != id_buku]
        if len(updated) == len(books):
            raise ValueError("Buku tidak ditemukan.")
        self.book_storage.save(updated)
        return True

    def save_books(self, books: list[Buku]) -> None:
        self.book_storage.save(books)

    def import_books(self, records: list[dict], replace: bool = False) -> int:
        existing_books = [] if replace else self.list_books()
        existing_ids = {b.id_buku for b in existing_books}
        imported = 0
        for record in records:
            record = {str(k).strip(): v for k, v in record.items()}
            buku = Buku.from_dict(record)
            if not buku.id_buku:
                buku._id_buku = generate_id("BK", [b.id_buku for b in existing_books])
            if buku.id_buku in existing_ids:
                continue
            existing_books.append(buku)
            existing_ids.add(buku.id_buku)
            imported += 1
        self.book_storage.save(existing_books)
        return imported
