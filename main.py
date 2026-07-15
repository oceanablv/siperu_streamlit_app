import streamlit as st
import base64

from config import (
    ensure_data_dir,
    USERS_FILE,
    BOOKS_FILE,
    CATEGORIES_FILE,
    ROOMS_FILE,
    LOANS_FILE,
    QUEUES_FILE,
    RESERVATIONS_FILE,
)
from models.buku import Buku, KategoriBuku
from models.ruangan import Ruangan
from models.transaksi import PeminjamanBuku, AntrianBuku, ReservasiRuangan
from models.user import User
from services.auth_service import AuthService
from services.buku_service import BukuService
from services.peminjaman_service import PeminjamanService
from services.reservasi_service import ReservasiService
from services.ruangan_service import RuanganService
from services.report_service import ReportService
from storage.json_storage import JsonStorage
from views.auth_view import render_auth
from views.anggota_view import render_anggota
from views.admin_view import render_admin


st.set_page_config(page_title="SIPERU", page_icon="📒", layout="wide")


def set_background(image_file):
    with open(image_file, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""
        <style>

        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: rgba(20, 20, 20, 0.85);
        }}

        /* Header transparan */
        [data-testid="stHeader"] {{
            background: rgba(0,0,0,0);
        }}

        /* Konten utama */
        .block-container {{
            background: rgba(20,20,20,0.55);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 18px;
            padding: 2rem;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

def build_services() -> dict:
    ensure_data_dir()

    user_storage = JsonStorage(USERS_FILE, User)
    book_storage = JsonStorage(BOOKS_FILE, Buku)
    category_storage = JsonStorage(CATEGORIES_FILE, KategoriBuku)
    room_storage = JsonStorage(ROOMS_FILE, Ruangan)
    loan_storage = JsonStorage(LOANS_FILE, PeminjamanBuku)
    queue_storage = JsonStorage(QUEUES_FILE, AntrianBuku)
    reservation_storage = JsonStorage(RESERVATIONS_FILE, ReservasiRuangan)

    auth_service = AuthService(user_storage)
    buku_service = BukuService(book_storage, category_storage)
    ruangan_service = RuanganService(room_storage)
    peminjaman_service = PeminjamanService(book_storage, loan_storage, queue_storage, user_storage)
    reservasi_service = ReservasiService(room_storage, reservation_storage)
    report_service = ReportService(user_storage, book_storage, room_storage, loan_storage, reservation_storage, queue_storage)

    auth_service.seed_default_users()
    buku_service.seed_default_data()
    ruangan_service.seed_default_data()

    return {
        "auth": auth_service,
        "buku": buku_service,
        "ruangan": ruangan_service,
        "peminjaman": peminjaman_service,
        "reservasi": reservasi_service,
        "report": report_service,
    }


def main() -> None:
    services = build_services()

    # Pasang wallpaper untuk seluruh aplikasi
    set_background(
        "assets/abcdefghij.jpg"
    )

    st.sidebar.title("SIPERU")
    st.sidebar.caption("Perpustakaan Universitas Bakrie")

    # Jika belum login tampilkan halaman login
    if "user" not in st.session_state:
        render_auth(services["auth"])
        return

    user = User.from_dict(st.session_state["user"])

    if user.role == "admin":
        render_admin(st.session_state["user"], services)
    else:
        render_anggota(st.session_state["user"], services)

if __name__ == "__main__":
    main()
