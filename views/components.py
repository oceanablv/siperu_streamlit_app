from pathlib import Path
import inspect
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import hashlib
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parents[1]

PROGRAM_STUDI_OPTIONS = [
    "Akuntansi",
    "Ilmu Komunikasi",
    "Ilmu dan Teknologi Pangan",
    "Manajemen",
    "Ilmu Politik",
    "Sistem Informasi",
    "Informatika",
    "Teknik Industri",
    "Teknik Lingkungan",
    "Teknik Sipil",
]
PROGRAM_STUDI_PLACEHOLDER = "Pilih atau ketik Program Studi"
PROGRAM_STUDI_OTHER = "Lainnya"


def render_program_studi_input(label: str = "Program Studi", value: str = "", key: str = "program_studi") -> str:
    current_value = (value or "").strip()
    options = PROGRAM_STUDI_OPTIONS.copy()

    if current_value and current_value not in options:
        options.append(current_value)

    default_index = options.index(current_value) if current_value else None

    if "accept_new_options" in inspect.signature(st.selectbox).parameters:
        selected = st.selectbox(
            label,
            options,
            index=default_index,
            placeholder=PROGRAM_STUDI_PLACEHOLDER,
            accept_new_options=True,
            key=f"{key}_select",
        )
        return (selected or "").strip()

    fallback_options = [PROGRAM_STUDI_PLACEHOLDER, *PROGRAM_STUDI_OPTIONS, PROGRAM_STUDI_OTHER]
    if current_value in PROGRAM_STUDI_OPTIONS:
        fallback_index = fallback_options.index(current_value)
        custom_value = ""
    elif current_value:
        fallback_index = fallback_options.index(PROGRAM_STUDI_OTHER)
        custom_value = current_value
    else:
        fallback_index = 0
        custom_value = ""

    selected = st.selectbox(label, fallback_options, index=fallback_index, key=f"{key}_select")
    custom_value = st.text_input("Program Studi Lainnya", value=custom_value, key=f"{key}_custom")
    if selected == PROGRAM_STUDI_OTHER:
        return custom_value.strip()
    if selected == PROGRAM_STUDI_PLACEHOLDER:
        return ""
    return selected


def show_table(records: list[dict], empty_message: str = "Belum ada data.") -> None:
    if not records:
        st.info(empty_message)
        return
    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)


def rupiah(value: float) -> str:
    return f"Rp{value:,.0f}".replace(",", ".")


def push_notification(kind: str, message: str) -> None:
    st.session_state.setdefault("_notifications", []).append({"kind": kind, "message": message})


def render_notifications() -> None:
    notifications = st.session_state.pop("_notifications", [])
    for item in notifications:
        kind = item.get("kind", "info")
        message = item.get("message", "")
        if kind == "success":
            st.success(message)
        elif kind == "warning":
            st.warning(message)
        elif kind == "error":
            st.error(message)
        else:
            st.info(message)


def resolve_cover_source(cover_buku: str) -> str | None:
    """Mengembalikan URL/path cover buku yang aman dipakai oleh st.image."""
    if not cover_buku:
        return None
    cover_buku = str(cover_buku).strip()
    if cover_buku.startswith(("http://", "https://")):
        return cover_buku

    relative_cover = cover_buku.lstrip("/\\")
    path = Path(cover_buku)
    if path.exists():
        return str(path)

    relative_path = BASE_DIR / relative_cover
    if relative_path.exists():
        return str(relative_path)

    return cover_buku


def resolve_pdf_source(link_pdf: str):
    if not link_pdf:
        return None

    link_pdf = str(link_pdf).strip()
    parsed = urlparse(link_pdf)

    if parsed.scheme in ["http", "https"]:
        if "drive.google.com" in parsed.netloc and "/file/d/" in parsed.path:
            file_id = parsed.path.split("/file/d/", 1)[1].split("/", 1)[0]
            return f"https://drive.google.com/file/d/{file_id}/preview"
        if "drive.google.com" in parsed.netloc and parsed.path == "/open":
            file_id = parse_qs(parsed.query).get("id", [""])[0]
            if file_id:
                return f"https://drive.google.com/file/d/{file_id}/preview"
        return link_pdf

    relative_pdf = link_pdf.lstrip("/\\")
    path = Path(link_pdf)
    if not path.exists():
        path = BASE_DIR / relative_pdf

    if path.exists() and path.suffix.lower() == ".pdf":
        return path

    return None


def render_pdf_reader(link_pdf: str, title: str, height: int = 720) -> None:
    source = resolve_pdf_source(link_pdf)
    if not source:
        st.warning("PDF belum tersedia untuk buku ini.")
        return

    st.subheader(f"PDF Reader - {title}")
    fullscreen_mode = st.toggle("Mode Layar Penuh", key=pdf_fullscreen_key(title, link_pdf))
    reader_height = 1050 if fullscreen_mode else height

    try:
        if isinstance(source, Path):
            st.pdf(source, height=reader_height)
            return

        if isinstance(source, str) and "drive.google.com" in source:
            components.iframe(source, height=reader_height, scrolling=True)
            st.link_button("Buka PDF di Tab Baru", source, use_container_width=True)
            return

        if isinstance(source, str) and source.startswith(("http://", "https://")):
            st.pdf(source, height=reader_height)
            return

        st.pdf(source, height=reader_height)
    except Exception as error:
        if isinstance(source, str) and source.startswith(("http://", "https://")):
            components.iframe(source, height=reader_height, scrolling=True)
        else:
            st.error(f"PDF tidak dapat ditampilkan: {error}")

    if isinstance(source, str) and source.startswith(("http://", "https://")):
        st.link_button("Buka PDF di Tab Baru", source, use_container_width=True)


def pdf_fullscreen_key(title: str, link_pdf: str) -> str:
    reader_key = hashlib.sha1(f"{title}-{link_pdf}".encode("utf-8")).hexdigest()[:12]
    return f"pdf_fullscreen_{reader_key}"


def render_book_cover(book, width: int = 170, height: int = 200) -> None:
    """Menampilkan cover buku dengan ukuran lebih kecil."""
    cover_source = resolve_cover_source(getattr(book, "cover_buku", ""))
    if cover_source:
        try:
            # Supaya cover tidak terlalu besar
            left, center, right = st.columns([1, 2, 1])
            with center:
                st.image(cover_source, width=width)
            return
        except Exception:
            pass

    safe_title = str(getattr(book, "judul", "Buku")).replace("<", "&lt;").replace(">", "&gt;")
    st.markdown(
        f"""
        <div style="
            height:{height}px;
            max-width:{width}px;
            margin:0 auto;
            border:1px solid rgba(255,255,255,0.18);
            border-radius:12px;
            display:flex;
            align-items:center;
            justify-content:center;
            text-align:center;
            padding:14px;
            background:linear-gradient(135deg, rgba(132,91,255,0.20), rgba(255,255,255,0.05));
        ">
            <div>
                <div style="font-size:36px; margin-bottom:8px;">📚</div>
                <b>{safe_title}</b><br>
                <span style="opacity:0.75; font-size:13px;">Cover belum tersedia</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def book_records(books, category_map: dict[str, str]) -> list[dict]:
    return [
        {
            "ID Buku": b.id_buku,
            "Judul": b.judul,
            "Penulis": b.penulis,
            "Penerbit": b.penerbit,
            "Tahun": b.tahun_terbit,
            "Kategori": category_map.get(b.kategori_id, b.kategori_id),
            "Stok": b.stok,
            "PDF": "Tersedia" if getattr(b, "link_pdf", "") else "Belum tersedia",
        }
        for b in books
    ]


def room_records(rooms) -> list[dict]:
    return [
        {
            "ID Ruangan": r.id_ruangan,
            "Nama Ruangan": r.nama_ruangan,
            "Kapasitas": r.kapasitas,
            "Lokasi": r.lokasi,
            "Fasilitas": r.fasilitas,
            "Status": r.status_ruangan,
        }
        for r in rooms
    ]
