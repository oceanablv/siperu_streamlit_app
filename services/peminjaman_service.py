from datetime import date
from models.buku import Buku
from models.transaksi import PeminjamanBuku, AntrianBuku
from models.user import Anggota
from services.helpers import generate_id, now_date
from storage.json_storage import JsonStorage


class PeminjamanService:
    """Service untuk proses peminjaman, pengembalian, dan antrian buku.

    UML Relationship:
    - Aggregation: PeminjamanService menyimpan referensi book_storage,
      loan_storage, queue_storage, dan user_storage bertipe JsonStorage.
    - Dependency: PeminjamanService menggunakan Buku, Anggota, PeminjamanBuku,
      dan AntrianBuku untuk menjalankan aturan peminjaman.
    - Association: relasi transaksi ke Buku dan Anggota tetap menggunakan
      id_buku dan id_anggota pada PeminjamanBuku/AntrianBuku.
    - Composition: tidak diterapkan karena service tidak memiliki objek Buku,
      Anggota, atau transaksi secara eksklusif.
    """

    LAMA_PINJAM_HARI = 14

    def __init__(self, book_storage: JsonStorage, loan_storage: JsonStorage, queue_storage: JsonStorage, user_storage: JsonStorage):
        self.book_storage = book_storage
        self.loan_storage = loan_storage
        self.queue_storage = queue_storage
        self.user_storage = user_storage

    def list_loans(self) -> list[PeminjamanBuku]:
        return self.loan_storage.load()

    def list_queues(self) -> list[AntrianBuku]:
        return self.queue_storage.load()

    def active_loans_by_user(self, id_anggota: str) -> list[PeminjamanBuku]:
        return [loan for loan in self.list_loans() if loan.id_anggota == id_anggota and loan.sedang_dipinjam()]

    def loans_by_user(self, id_anggota: str) -> list[PeminjamanBuku]:
        return [loan for loan in self.list_loans() if loan.id_anggota == id_anggota]

    def queues_by_user(self, id_anggota: str) -> list[AntrianBuku]:
        return [queue for queue in self.list_queues() if queue.id_anggota == id_anggota]

    def _get_member(self, id_anggota: str) -> Anggota | None:
        for user in self.user_storage.load():
            if isinstance(user, Anggota) and user.id_user == id_anggota:
                return user
        return None

    def pinjam_buku(self, id_anggota: str, id_buku: str, lama_pinjam_hari: int | None = None) -> tuple[str, str]:
        """Membuat transaksi peminjaman buku dengan lama pinjam tetap 14 hari."""
        lama_pinjam_hari = self.LAMA_PINJAM_HARI

        member = self._get_member(id_anggota)
        if member is None:
            raise ValueError("Anggota tidak ditemukan.")
        if not member.status_aktif:
            raise ValueError("Akun anggota tidak aktif.")
        if len(self.active_loans_by_user(id_anggota)) >= member.kuota_pinjam:
            raise ValueError("Kuota peminjaman sudah penuh.")
        if any(loan.id_buku == id_buku for loan in self.active_loans_by_user(id_anggota)):
            raise ValueError("Buku ini sedang Anda pinjam.")

        books: list[Buku] = self.book_storage.load()
        target_book = None
        for book in books:
            if book.id_buku == id_buku:
                target_book = book
                break
        if target_book is None:
            raise ValueError("Buku tidak ditemukan.")
        if not target_book.bisa_dibaca_pdf():
            raise ValueError("Buku belum memiliki path/link PDF untuk reader. Silakan hubungi admin.")

        if not target_book.cek_stok():
            queues = self.list_queues()
            already_waiting = any(q.id_buku == id_buku and q.id_anggota == id_anggota and q.status_antrian == "Menunggu" for q in queues)
            if already_waiting:
                return "queue", "Anda sudah berada dalam antrian buku ini."
            urutan = len([q for q in queues if q.id_buku == id_buku and q.status_antrian == "Menunggu"]) + 1
            queue = AntrianBuku(generate_id("AN", [q.id_antrian for q in queues]), id_buku, id_anggota, now_date(), urutan, "Menunggu")
            queues.append(queue)
            self.queue_storage.save(queues)
            return "queue", f"Stok buku habis. Anda masuk antrian urutan ke-{urutan}."

        loans = self.list_loans()
        tanggal_pinjam = date.today()
        loan = PeminjamanBuku.buat_baru(
            id_peminjaman_buku=generate_id("PB", [l.id_peminjaman_buku for l in loans]),
            id_buku=id_buku,
            id_anggota=id_anggota,
            tanggal_pinjam=tanggal_pinjam,
            lama_pinjam_hari=lama_pinjam_hari,
        )
        target_book.update_stok(-1)
        loans.append(loan)
        self.book_storage.save(books)
        self.loan_storage.save(loans)
        return "success", f"Buku berhasil dipinjam. Buka menu Baca Buku untuk membaca PDF sampai {loan.tanggal_kembali}."

    def kembalikan_buku(self, id_peminjaman_buku: str) -> float:
        loans = self.list_loans()
        books = self.book_storage.load()
        target_loan = None
        for loan in loans:
            if loan.id_peminjaman_buku == id_peminjaman_buku:
                target_loan = loan
                break
        if target_loan is None:
            raise ValueError("Data peminjaman tidak ditemukan.")
        if target_loan.status_peminjaman != "Dipinjam":
            raise ValueError("Buku sudah dikembalikan atau status tidak valid.")

        denda = target_loan.proses_pengembalian()
        for book in books:
            if book.id_buku == target_loan.id_buku:
                book.update_stok(1)
                break

        queues = self.list_queues()
        waiting_for_book = sorted(
            [q for q in queues if q.id_buku == target_loan.id_buku and q.status_antrian == "Menunggu"],
            key=lambda q: q.urutan,
        )
        if waiting_for_book:
            waiting_for_book[0].status_antrian = "Dipanggil"

        self.loan_storage.save(loans)
        self.book_storage.save(books)
        self.queue_storage.save(queues)
        return denda

    def cancel_queue(self, id_antrian: str, id_anggota: str) -> bool:
        queues = self.list_queues()
        for queue in queues:
            if queue.id_antrian == id_antrian and queue.id_anggota == id_anggota:
                queue.status_antrian = "Dibatalkan"
                self.queue_storage.save(queues)
                return True
        raise ValueError("Data antrian tidak ditemukan.")
