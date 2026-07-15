# SIPERU - Sistem Peminjaman Buku dan Reservasi Ruangan Perpustakaan

SIPERU adalah aplikasi berbasis **Object-Oriented Programming (OOP)** dengan GUI **Streamlit**, database **JSON**, serta fitur **export/import CSV dan Excel**.

## Fitur

- Login dan register anggota
- Database JSON untuk user, buku, kategori, ruangan, peminjaman, antrian, dan reservasi
- Pencarian buku dengan tampilan cover/kartu buku, sisa stok, dan tombol pinjam/antrian
- Peminjaman buku otomatis 14 hari dan tidak bisa diubah dari sisi anggota
- Antrian buku ketika stok habis
- Pengembalian buku dan perhitungan denda otomatis
- Reservasi ruangan otomatis 2 jam dari jam mulai, tanpa input jam selesai dari anggota
- Perpanjangan reservasi 1 jam jika jadwal setelahnya masih kosong
- Admin mengelola buku, ruangan, anggota, monitoring peminjaman, validasi reservasi, dan menghapus akun anggota
- Export laporan ke CSV/PDF dan import data master dari CSV/Excel
- Struktur modular: `models`, `services`, `storage`, `views`, dan `main.py`

## Konsep OOP yang diterapkan

- **Encapsulation**: atribut penting dibuat private/protected dan diakses melalui property, contoh pada class `User`, `Buku`, dan `Ruangan`.
- **Inheritance**: `Anggota` dan `Admin` mewarisi class `User`.
- **Abstraction**: `BaseModel` menjadi abstract class yang mewajibkan method `to_dict()` dan `from_dict()`.
- **Polymorphism**: method `dashboard_title()` dioverride oleh `Admin` dan `Anggota`.

## Cara Menjalankan

```bash
cd siperu_streamlit_app
pip install -r requirements.txt
streamlit run main.py
```

## Akun Demo

- Admin: `admin` / `admin123`
- Anggota: `anggota` / `anggota123`

## Struktur Folder

```text
siperu_streamlit_app/
├── main.py
├── config.py
├── requirements.txt
├── assets/
│   └── covers/
├── data/
│   ├── users.json
│   ├── books.json
│   ├── categories.json
│   ├── rooms.json
│   ├── loans.json
│   ├── queues.json
│   └── reservations.json
├── models/
│   ├── base.py
│   ├── user.py
│   ├── buku.py
│   ├── ruangan.py
│   └── transaksi.py
├── services/
│   ├── auth_service.py
│   ├── buku_service.py
│   ├── ruangan_service.py
│   ├── peminjaman_service.py
│   ├── reservasi_service.py
│   ├── report_service.py
│   └── helpers.py
├── storage/
│   ├── json_storage.py
│   └── export_import.py
└── views/
    ├── auth_view.py
    ├── anggota_view.py
    ├── admin_view.py
    └── components.py
```
