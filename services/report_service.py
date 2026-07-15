from models.buku import Buku
from models.ruangan import Ruangan
from models.transaksi import PeminjamanBuku, ReservasiRuangan, AntrianBuku
from models.user import User, Anggota
from storage.json_storage import JsonStorage


class ReportService:
    """Service untuk membuat ringkasan dan data laporan.

    UML Relationship:
    - Aggregation: ReportService menyimpan beberapa referensi JsonStorage
      untuk user, buku, ruangan, peminjaman, reservasi, dan antrian.
    - Dependency: ReportService membaca User, Anggota, Buku, Ruangan,
      PeminjamanBuku, ReservasiRuangan, dan AntrianBuku saat menyusun laporan.
    - Association: data laporan digabungkan berdasarkan id_anggota, id_buku,
      dan id_ruangan.
    - Composition: tidak diterapkan karena ReportService tidak menyimpan objek
      laporan sebagai bagian internal permanen.
    """

    def __init__(self, user_storage: JsonStorage, book_storage: JsonStorage, room_storage: JsonStorage, loan_storage: JsonStorage, reservation_storage: JsonStorage, queue_storage: JsonStorage):
        self.user_storage = user_storage
        self.book_storage = book_storage
        self.room_storage = room_storage
        self.loan_storage = loan_storage
        self.reservation_storage = reservation_storage
        self.queue_storage = queue_storage

    def summary(self) -> dict:
        users = self.user_storage.load()
        books = self.book_storage.load()
        rooms = self.room_storage.load()
        loans = self.loan_storage.load()
        reservations = self.reservation_storage.load()
        return {
            "Anggota": len([u for u in users if isinstance(u, Anggota)]),
            "Buku": len(books),
            "Ruangan": len(rooms),
            "Peminjaman Aktif": len([l for l in loans if l.status_peminjaman == "Dipinjam"]),
            "Reservasi Menunggu": len([r for r in reservations if r.status_reservasi == "Menunggu"]),
        }

    def table_records(self, table_name: str) -> list[dict]:
        table_name = table_name.lower()
        if table_name == "users":
            return [u.to_dict() for u in self.user_storage.load()]
        if table_name == "books":
            return [b.to_dict() for b in self.book_storage.load()]
        if table_name == "rooms":
            return [r.to_dict() for r in self.room_storage.load()]
        if table_name == "loans":
            return [l.to_dict() for l in self.loan_storage.load()]
        if table_name == "reservations":
            return [r.to_dict() for r in self.reservation_storage.load()]
        if table_name == "queues":
            return [q.to_dict() for q in self.queue_storage.load()]
        raise ValueError("Nama tabel tidak dikenal.")

    def joined_loans(self) -> list[dict]:
        users = {u.id_user: u.nama for u in self.user_storage.load()}
        books = {b.id_buku: b.judul for b in self.book_storage.load()}
        records = []
        for loan in self.loan_storage.load():
            records.append(
                {
                    "ID Peminjaman": loan.id_peminjaman_buku,
                    "Nama Anggota": users.get(loan.id_anggota, "-"),
                    "Judul Buku": books.get(loan.id_buku, "-"),
                    "Tanggal Pinjam": loan.tanggal_pinjam,
                    "Batas Kembali": loan.tanggal_kembali,
                    "Status": loan.status_peminjaman,
                    "Denda": loan.denda,
                    "Tanggal Dikembalikan": loan.tanggal_dikembalikan or "-",
                }
            )
        return records

    def joined_reservations(self) -> list[dict]:
        users = {u.id_user: u.nama for u in self.user_storage.load()}
        rooms = {r.id_ruangan: r.nama_ruangan for r in self.room_storage.load()}
        records = []
        for reservation in self.reservation_storage.load():
            record = reservation.to_dict()
            record["nama_anggota"] = users.get(reservation.id_anggota, "-")
            record["nama_ruangan"] = rooms.get(reservation.id_ruangan, "-")
            records.append(record)
        return records
