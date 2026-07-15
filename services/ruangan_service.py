from models.ruangan import Ruangan
from services.helpers import generate_id
from storage.json_storage import JsonStorage


class RuanganService:
    """Service untuk pengelolaan ruangan.

    UML Relationship:
    - Aggregation: RuanganService menyimpan referensi room_storage bertipe
      JsonStorage.
    - Dependency: RuanganService menggunakan Ruangan untuk operasi tambah,
      ubah, hapus, dan import data.
    - Composition: tidak diterapkan karena objek Ruangan dimuat/disimpan lewat
      storage, bukan menjadi bagian permanen dari RuanganService.
    """

    def __init__(self, room_storage: JsonStorage):
        self.room_storage = room_storage

    def seed_default_data(self) -> None:
        if self.room_storage.load():
            return
        self.room_storage.save(
            [
                Ruangan("RG001", "Ruang Diskusi A", 6, "Lantai 2", "AC, Whiteboard, Wi-Fi", "Tersedia"),
                Ruangan("RG002", "Ruang Diskusi B", 8, "Lantai 2", "AC, TV, Wi-Fi", "Tersedia"),
                Ruangan("RG003", "Ruang Seminar Mini", 20, "Lantai 3", "Projector, Sound System, Wi-Fi", "Tersedia"),
            ]
        )

    def list_rooms(self) -> list[Ruangan]:
        return self.room_storage.load()

    def get_room(self, id_ruangan: str) -> Ruangan | None:
        for ruangan in self.list_rooms():
            if ruangan.id_ruangan == id_ruangan:
                return ruangan
        return None

    def add_room(self, nama_ruangan: str, kapasitas: int, lokasi: str, fasilitas: str, status_ruangan: str = "Tersedia") -> Ruangan:
        if not nama_ruangan:
            raise ValueError("Nama ruangan tidak boleh kosong.")
        rooms = self.list_rooms()
        room = Ruangan(generate_id("RG", [r.id_ruangan for r in rooms]), nama_ruangan, int(kapasitas), lokasi, fasilitas, status_ruangan)
        rooms.append(room)
        self.room_storage.save(rooms)
        return room

    def update_room(self, id_ruangan: str, nama_ruangan: str, kapasitas: int, lokasi: str, fasilitas: str, status_ruangan: str) -> bool:
        rooms = self.list_rooms()
        for room in rooms:
            if room.id_ruangan == id_ruangan:
                room.nama_ruangan = nama_ruangan
                room.kapasitas = int(kapasitas)
                room.lokasi = lokasi
                room.fasilitas = fasilitas
                room.status_ruangan = status_ruangan
                self.room_storage.save(rooms)
                return True
        raise ValueError("Ruangan tidak ditemukan.")

    def delete_room(self, id_ruangan: str) -> bool:
        rooms = self.list_rooms()
        updated = [r for r in rooms if r.id_ruangan != id_ruangan]
        if len(updated) == len(rooms):
            raise ValueError("Ruangan tidak ditemukan.")
        self.room_storage.save(updated)
        return True

    def import_rooms(self, records: list[dict], replace: bool = False) -> int:
        existing_rooms = [] if replace else self.list_rooms()
        existing_ids = {r.id_ruangan for r in existing_rooms}
        imported = 0
        for record in records:
            record = {str(k).strip(): v for k, v in record.items()}
            room = Ruangan.from_dict(record)
            if not room.id_ruangan:
                room._id_ruangan = generate_id("RG", [r.id_ruangan for r in existing_rooms])
            if room.id_ruangan in existing_ids:
                continue
            existing_rooms.append(room)
            existing_ids.add(room.id_ruangan)
            imported += 1
        self.room_storage.save(existing_rooms)
        return imported
