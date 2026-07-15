from datetime import datetime, timedelta
from models.ruangan import Ruangan
from models.transaksi import ReservasiRuangan
from services.helpers import generate_id
from storage.json_storage import JsonStorage


class ReservasiService:
    """Service untuk proses reservasi ruangan.

    UML Relationship:
    - Aggregation: ReservasiService menyimpan referensi room_storage dan
      reservation_storage bertipe JsonStorage.
    - Dependency: ReservasiService menggunakan Ruangan dan ReservasiRuangan
      untuk validasi jadwal dan pembuatan reservasi.
    - Association: relasi ReservasiRuangan ke Ruangan dan Anggota disimpan
      melalui id_ruangan dan id_anggota.
    - Composition: tidak diterapkan karena service tidak memiliki lifecycle
      eksklusif atas Ruangan atau ReservasiRuangan.
    """

    DURASI_DEFAULT_JAM = 2
    PERPANJANGAN_JAM = 1
    MAKSIMAL_SETELAH_PERPANJANGAN_JAM = 4

    JAM_BUKA = "08:00"
    JAM_TUTUP = "21:00"
    JAM_MULAI_TERAKHIR = "19:00"

    def __init__(self, room_storage: JsonStorage, reservation_storage: JsonStorage):
        self.room_storage = room_storage
        self.reservation_storage = reservation_storage

    def list_reservations(self) -> list[ReservasiRuangan]:
        return self.reservation_storage.load()

    def reservations_by_user(self, id_anggota: str) -> list[ReservasiRuangan]:
        return [
            reservation
            for reservation in self.list_reservations()
            if reservation.id_anggota == id_anggota
        ]

    def _now(self, reference_datetime: datetime | None = None) -> datetime:
        return reference_datetime or datetime.now()

    def _parse_time(self, value: str):
        return datetime.strptime(value, "%H:%M").time()

    def _parse_datetime(self, tanggal: str, jam: str) -> datetime:
        return datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M")

    def reservation_range(self, reservation: ReservasiRuangan) -> tuple[datetime, datetime]:
        return (
            self._parse_datetime(reservation.tanggal_reservasi, reservation.jam_mulai),
            self._parse_datetime(reservation.tanggal_reservasi, reservation.jam_selesai),
        )

    def is_current_reservation(
        self,
        reservation: ReservasiRuangan,
        reference_datetime: datetime | None = None
    ) -> bool:
        if reservation.status_reservasi != "Dikonfirmasi":
            return False
        start, end = self.reservation_range(reservation)
        now = self._now(reference_datetime)
        return start <= now < end

    def active_or_upcoming_reservations_by_user(
        self,
        id_anggota: str,
        reference_datetime: datetime | None = None
    ) -> list[ReservasiRuangan]:
        now = self._now(reference_datetime)
        active_statuses = ["Menunggu", "Dikonfirmasi"]
        reservations = []

        for reservation in self.reservations_by_user(id_anggota):
            if reservation.status_reservasi not in active_statuses:
                continue

            _, end = self.reservation_range(reservation)
            if end > now:
                reservations.append(reservation)

        return sorted(
            reservations,
            key=lambda reservation: self.reservation_range(reservation)[0],
        )

    def history_reservations_by_user(
        self,
        id_anggota: str,
        reference_datetime: datetime | None = None
    ) -> list[ReservasiRuangan]:
        now = self._now(reference_datetime)
        active_statuses = ["Menunggu", "Dikonfirmasi"]
        reservations = []

        for reservation in self.reservations_by_user(id_anggota):
            _, end = self.reservation_range(reservation)
            if reservation.status_reservasi not in active_statuses or end <= now:
                reservations.append(reservation)

        return sorted(
            reservations,
            key=lambda reservation: self.reservation_range(reservation)[0],
            reverse=True,
        )

    def _duration_hours(self, tanggal: str, jam_mulai: str, jam_selesai: str) -> float:
        start = self._parse_datetime(tanggal, jam_mulai)
        end = self._parse_datetime(tanggal, jam_selesai)
        return (end - start).total_seconds() / 3600

    def _is_overlap(self, start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
        a_start = self._parse_time(start_a)
        a_end = self._parse_time(end_a)
        b_start = self._parse_time(start_b)
        b_end = self._parse_time(end_b)

        return a_start < b_end and b_start < a_end

    def _validasi_jam_operasional(
        self,
        tanggal: str,
        jam_mulai: str,
        jam_selesai: str
    ):
        start = self._parse_datetime(tanggal, jam_mulai)
        end = self._parse_datetime(tanggal, jam_selesai)

        jam_buka = self._parse_datetime(tanggal, self.JAM_BUKA)
        jam_tutup = self._parse_datetime(tanggal, self.JAM_TUTUP)
        jam_mulai_terakhir = self._parse_datetime(tanggal, self.JAM_MULAI_TERAKHIR)

        if start < jam_buka:
            raise ValueError("Reservasi hanya dapat dimulai minimal pukul 08:00.")

        if start > jam_mulai_terakhir:
            raise ValueError("Reservasi hanya dapat dimulai maksimal pukul 19:00.")

        if end > jam_tutup:
            raise ValueError("Reservasi tidak boleh melewati jam tutup perpustakaan, yaitu pukul 21:00.")

    def hitung_jam_selesai_otomatis(
        self,
        jam_mulai: str,
        durasi_jam: int | None = None
    ) -> str:
        durasi_jam = durasi_jam or self.DURASI_DEFAULT_JAM

        start = datetime.strptime(jam_mulai, "%H:%M")
        end = start + timedelta(hours=durasi_jam)

        jam_buka = datetime.strptime(self.JAM_BUKA, "%H:%M")
        jam_tutup = datetime.strptime(self.JAM_TUTUP, "%H:%M")
        jam_mulai_terakhir = datetime.strptime(self.JAM_MULAI_TERAKHIR, "%H:%M")

        if start < jam_buka:
            raise ValueError("Reservasi hanya dapat dimulai minimal pukul 08:00.")

        if start > jam_mulai_terakhir:
            raise ValueError("Reservasi hanya dapat dimulai maksimal pukul 19:00.")

        if end > jam_tutup:
            raise ValueError("Jam selesai tidak boleh melewati pukul 21:00.")

        return end.strftime("%H:%M")

    def validasi_jadwal(
        self,
        id_ruangan: str,
        tanggal: str,
        jam_mulai: str,
        jam_selesai: str,
        ignore_reservation_id: str | None = None,
        enforce_max_duration: bool = True,
    ) -> bool:
        if self._parse_time(jam_mulai) >= self._parse_time(jam_selesai):
            raise ValueError("Jam selesai harus lebih besar dari jam mulai.")

        self._validasi_jam_operasional(tanggal, jam_mulai, jam_selesai)

        durasi = self._duration_hours(tanggal, jam_mulai, jam_selesai)

        if enforce_max_duration and durasi > self.DURASI_DEFAULT_JAM:
            raise ValueError("Durasi reservasi awal maksimal 2 jam.")

        for reservation in self.list_reservations():
            if ignore_reservation_id and reservation.id_reservasi == ignore_reservation_id:
                continue

            if reservation.id_ruangan != id_ruangan or reservation.tanggal_reservasi != tanggal:
                continue

            if reservation.status_reservasi in ["Menunggu", "Dikonfirmasi"]:
                if self._is_overlap(
                    jam_mulai,
                    jam_selesai,
                    reservation.jam_mulai,
                    reservation.jam_selesai
                ):
                    return False

        return True

    def buat_reservasi(
        self,
        id_anggota: str,
        id_ruangan: str,
        tanggal: str,
        jam_mulai: str,
        jam_selesai: str | None = None,
        keperluan: str = ""
    ) -> ReservasiRuangan:
        rooms: list[Ruangan] = self.room_storage.load()

        room = next((r for r in rooms if r.id_ruangan == id_ruangan), None)

        if room is None:
            raise ValueError("Ruangan tidak ditemukan.")

        if not room.cek_ketersediaan():
            raise ValueError("Ruangan sedang tidak tersedia untuk reservasi.")

        if not keperluan:
            raise ValueError("Keperluan reservasi wajib diisi.")

        jam_selesai = jam_selesai or self.hitung_jam_selesai_otomatis(jam_mulai)

        if not self.validasi_jadwal(
            id_ruangan,
            tanggal,
            jam_mulai,
            jam_selesai
        ):
            raise ValueError("Jadwal bentrok dengan reservasi lain.")

        reservations = self.list_reservations()

        reservation = ReservasiRuangan(
            id_reservasi=generate_id("RS", [r.id_reservasi for r in reservations]),
            id_ruangan=id_ruangan,
            id_anggota=id_anggota,
            tanggal_reservasi=tanggal,
            jam_mulai=jam_mulai,
            jam_selesai=jam_selesai,
            keperluan=keperluan,
            status_reservasi="Menunggu",
        )

        reservations.append(reservation)
        self.reservation_storage.save(reservations)

        return reservation

    def perpanjang_reservasi(
        self,
        id_reservasi: str,
        id_anggota: str,
        tambahan_jam: int | None = None
    ) -> ReservasiRuangan:
        tambahan_jam = tambahan_jam or self.PERPANJANGAN_JAM
        reservations = self.list_reservations()

        for reservation in reservations:
            if reservation.id_reservasi == id_reservasi and reservation.id_anggota == id_anggota:
                if reservation.status_reservasi != "Dikonfirmasi":
                    raise ValueError("Reservasi hanya dapat diperpanjang jika statusnya sudah dikonfirmasi.")

                _, current_end = self.reservation_range(reservation)
                now = self._now()

                if current_end <= now:
                    raise ValueError("Reservasi sudah selesai dan tidak dapat diperpanjang.")

                new_end = current_end + timedelta(hours=tambahan_jam)
                new_end_str = new_end.strftime("%H:%M")

                if new_end.date().isoformat() != reservation.tanggal_reservasi:
                    raise ValueError("Perpanjangan tidak boleh melewati pergantian hari.")

                jam_tutup = self._parse_datetime(
                    reservation.tanggal_reservasi,
                    self.JAM_TUTUP
                )

                if new_end > jam_tutup:
                    raise ValueError("Perpanjangan maksimal hanya sampai pukul 21:00.")

                total_duration = self._duration_hours(
                    reservation.tanggal_reservasi,
                    reservation.jam_mulai,
                    new_end_str
                )

                if total_duration > self.MAKSIMAL_SETELAH_PERPANJANGAN_JAM:
                    raise ValueError("Total durasi setelah perpanjangan maksimal 4 jam.")

                if not self.validasi_jadwal(
                    reservation.id_ruangan,
                    reservation.tanggal_reservasi,
                    reservation.jam_mulai,
                    new_end_str,
                    ignore_reservation_id=id_reservasi,
                    enforce_max_duration=False,
                ):
                    raise ValueError("Tidak dapat diperpanjang karena jadwal setelahnya sudah terisi.")

                reservation.jam_selesai = new_end_str
                self.reservation_storage.save(reservations)

                return reservation

        raise ValueError("Reservasi tidak ditemukan.")

    def akhiri_reservasi_sekarang(
        self,
        id_reservasi: str,
        id_anggota: str,
        reference_datetime: datetime | None = None
    ) -> ReservasiRuangan:
        reservations = self.list_reservations()
        now = self._now(reference_datetime)

        for reservation in reservations:
            if reservation.id_reservasi == id_reservasi and reservation.id_anggota == id_anggota:
                if reservation.status_reservasi != "Dikonfirmasi":
                    raise ValueError("Hanya reservasi yang sudah dikonfirmasi yang dapat diakhiri.")

                start, end = self.reservation_range(reservation)

                if now < start:
                    raise ValueError("Reservasi belum dimulai.")

                if now >= end:
                    reservation.status_reservasi = "Selesai"
                    self.reservation_storage.save(reservations)
                    return reservation

                reservation.jam_selesai = now.strftime("%H:%M")
                reservation.status_reservasi = "Selesai"
                self.reservation_storage.save(reservations)

                return reservation

        raise ValueError("Reservasi tidak ditemukan.")

    def update_status(self, id_reservasi: str, status: str) -> bool:
        reservations = self.list_reservations()

        for reservation in reservations:
            if reservation.id_reservasi == id_reservasi:
                if status == "Dikonfirmasi":
                    if not self.validasi_jadwal(
                        reservation.id_ruangan,
                        reservation.tanggal_reservasi,
                        reservation.jam_mulai,
                        reservation.jam_selesai,
                        ignore_reservation_id=id_reservasi
                    ):
                        raise ValueError("Reservasi tidak dapat dikonfirmasi karena jadwal sudah bentrok.")

                reservation.status_reservasi = status
                self.reservation_storage.save(reservations)

                return True

        raise ValueError("Reservasi tidak ditemukan.")

    def cancel_by_user(self, id_reservasi: str, id_anggota: str) -> bool:
        reservations = self.list_reservations()

        for reservation in reservations:
            if reservation.id_reservasi == id_reservasi and reservation.id_anggota == id_anggota:
                if reservation.status_reservasi == "Dikonfirmasi":
                    raise ValueError("Reservasi yang sudah dikonfirmasi hanya dapat dibatalkan oleh admin.")

                reservation.batalkan_reservasi()
                self.reservation_storage.save(reservations)

                return True

        raise ValueError("Reservasi tidak ditemukan.")
