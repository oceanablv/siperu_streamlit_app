import pandas as pd
import streamlit as st
from models.user import User, Anggota
from storage.export_import import ExportImport
from views.components import book_records, push_notification, render_notifications, room_records, rupiah, show_table


def render_admin(user_dict: dict, services: dict):
    user = User.from_dict(user_dict)
    render_notifications()
    auth_service = services["auth"]
    buku_service = services["buku"]
    peminjaman_service = services["peminjaman"]
    ruangan_service = services["ruangan"]
    reservasi_service = services["reservasi"]
    report_service = services["report"]

    st.sidebar.success(f"{user.nama}")
    page = st.sidebar.radio(
        "Menu Admin",
        [
            "Dashboard",
            "Kelola Buku",
            "Kelola Ruangan",
            "Kelola Anggota",
            "Monitoring Peminjaman",
            "Validasi Reservasi",
            "Import/Export & Laporan",
        ],
    )

    if st.sidebar.button("Logout", use_container_width=True):
        push_notification("success", "Logout berhasil.")
        st.session_state.pop("user", None)
        st.rerun()

    if page == "Dashboard":
        st.header(user.dashboard_title())
        summary = report_service.summary()
        cols = st.columns(len(summary))
        for col, (label, value) in zip(cols, summary.items()):
            col.metric(label, value)
        st.info("Admin dapat mengelola buku, ruangan, anggota, memonitor peminjaman, memvalidasi reservasi, export laporan CSV/PDF, serta import data CSV/Excel.")

    elif page == "Kelola Buku":
        st.header("Kelola Data Buku")
        categories = buku_service.list_categories()
        category_map = buku_service.category_map()
        books = buku_service.list_books()
        show_table(book_records(books, category_map), "Belum ada data buku.")

        tab_add, tab_edit, tab_category = st.tabs(["Tambah Buku", "Ubah/Hapus Buku", "Kategori Buku"])
        with tab_add:
            with st.form("add_book_form", clear_on_submit=True):
                judul = st.text_input("Judul Buku")
                penulis = st.text_input("Penulis")
                penerbit = st.text_input("Penerbit")
                col1, col2 = st.columns(2)
                tahun = col1.number_input("Tahun Terbit", min_value=1900, max_value=2100, value=2024)
                stok = col2.number_input("Stok", min_value=0, value=1)
                kategori_label = st.selectbox("Kategori", [f"{c.id_kategori} - {c.nama_kategori}" for c in categories]) if categories else ""
                cover = st.text_input("URL/Path Cover Buku (opsional)")
                pdf_upload = st.file_uploader("Upload PDF ke assets/pdfs", type=["pdf"])
                link_pdf = st.text_input("Path/URL PDF Buku", placeholder="assets/pdfs/nama_buku.pdf")
                submitted = st.form_submit_button("Tambah Buku", use_container_width=True)
            if submitted:
                try:
                    kategori_id = kategori_label.split(" - ")[0]
                    saved_pdf_path = buku_service.save_pdf_upload(pdf_upload) if pdf_upload else ""
                    buku = buku_service.add_book(
                        judul,
                        penulis,
                        penerbit,
                        int(tahun),
                        int(stok),
                        kategori_id,
                        cover,
                        saved_pdf_path or link_pdf,
                    )
                    push_notification("success", f"Buku {buku.judul} berhasil ditambahkan.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

        with tab_edit:
            if books:
                selected = st.selectbox("Pilih Buku", [f"{b.id_buku} - {b.judul}" for b in books])
                selected_id = selected.split(" - ")[0]
                book = buku_service.get_book(selected_id)
                with st.form("edit_book_form"):
                    judul = st.text_input("Judul Buku", value=book.judul)
                    penulis = st.text_input("Penulis", value=book.penulis)
                    penerbit = st.text_input("Penerbit", value=book.penerbit)
                    col1, col2 = st.columns(2)
                    tahun = col1.number_input("Tahun Terbit", min_value=1900, max_value=2100, value=int(book.tahun_terbit))
                    stok = col2.number_input("Stok", min_value=0, value=int(book.stok))
                    category_labels = [f"{c.id_kategori} - {c.nama_kategori}" for c in categories]
                    default_index = next((i for i, label in enumerate(category_labels) if label.startswith(book.kategori_id)), 0)
                    kategori_label = st.selectbox("Kategori", category_labels, index=default_index)
                    cover = st.text_input("URL/Path Cover Buku", value=book.cover_buku)
                    pdf_upload = st.file_uploader("Upload PDF Baru ke assets/pdfs", type=["pdf"])
                    link_pdf = st.text_input("Path/URL PDF Buku", value=book.link_pdf)
                    col_save, col_delete = st.columns(2)
                    save_clicked = col_save.form_submit_button("Simpan Perubahan", use_container_width=True)
                    delete_clicked = col_delete.form_submit_button("Hapus Buku", use_container_width=True)
                try:
                    if save_clicked:
                        saved_pdf_path = buku_service.save_pdf_upload(pdf_upload) if pdf_upload else ""
                        buku_service.update_book(
                            selected_id,
                            judul,
                            penulis,
                            penerbit,
                            int(tahun),
                            int(stok),
                            kategori_label.split(" - ")[0],
                            cover,
                            saved_pdf_path or link_pdf,
                        )
                        push_notification("success", "Buku berhasil diperbarui.")
                        st.rerun()
                    if delete_clicked:
                        buku_service.delete_book(selected_id)
                        push_notification("success", "Buku berhasil dihapus.")
                        st.rerun()
                except ValueError as error:
                    st.error(str(error))
            else:
                st.info("Belum ada buku untuk diubah.")

        with tab_category:
            show_table([c.to_dict() for c in categories], "Belum ada kategori.")
            with st.form("add_category_form"):
                nama_kategori = st.text_input("Nama Kategori Baru")
                submitted = st.form_submit_button("Tambah Kategori")
            if submitted:
                try:
                    kategori = buku_service.add_category(nama_kategori)
                    push_notification("success", f"Kategori {kategori.nama_kategori} berhasil ditambahkan.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    elif page == "Kelola Ruangan":
        st.header("Kelola Data Ruangan")
        rooms = ruangan_service.list_rooms()
        show_table(room_records(rooms), "Belum ada data ruangan.")
        tab_add, tab_edit = st.tabs(["Tambah Ruangan", "Ubah/Hapus Ruangan"])

        with tab_add:
            with st.form("add_room_form", clear_on_submit=True):
                nama = st.text_input("Nama Ruangan")
                kapasitas = st.number_input("Kapasitas", min_value=1, value=4)
                lokasi = st.text_input("Lokasi")
                fasilitas = st.text_area("Fasilitas")
                status = st.selectbox("Status", ["Tersedia", "Tidak Tersedia", "Maintenance"])
                submitted = st.form_submit_button("Tambah Ruangan", use_container_width=True)
            if submitted:
                try:
                    room = ruangan_service.add_room(nama, int(kapasitas), lokasi, fasilitas, status)
                    push_notification("success", f"Ruangan {room.nama_ruangan} berhasil ditambahkan.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

        with tab_edit:
            if rooms:
                selected = st.selectbox("Pilih Ruangan", [f"{r.id_ruangan} - {r.nama_ruangan}" for r in rooms])
                selected_id = selected.split(" - ")[0]
                room = ruangan_service.get_room(selected_id)
                with st.form("edit_room_form"):
                    nama = st.text_input("Nama Ruangan", value=room.nama_ruangan)
                    kapasitas = st.number_input("Kapasitas", min_value=1, value=int(room.kapasitas))
                    lokasi = st.text_input("Lokasi", value=room.lokasi)
                    fasilitas = st.text_area("Fasilitas", value=room.fasilitas)
                    statuses = ["Tersedia", "Tidak Tersedia", "Maintenance"]
                    status = st.selectbox("Status", statuses, index=statuses.index(room.status_ruangan) if room.status_ruangan in statuses else 0)
                    col_save, col_delete = st.columns(2)
                    save_clicked = col_save.form_submit_button("Simpan Perubahan", use_container_width=True)
                    delete_clicked = col_delete.form_submit_button("Hapus Ruangan", use_container_width=True)
                try:
                    if save_clicked:
                        ruangan_service.update_room(selected_id, nama, int(kapasitas), lokasi, fasilitas, status)
                        push_notification("success", "Ruangan berhasil diperbarui.")
                        st.rerun()
                    if delete_clicked:
                        ruangan_service.delete_room(selected_id)
                        push_notification("success", "Ruangan berhasil dihapus.")
                        st.rerun()
                except ValueError as error:
                    st.error(str(error))
            else:
                st.info("Belum ada ruangan untuk diubah.")

    elif page == "Kelola Anggota":
        st.header("Kelola Data Anggota")
        members = auth_service.list_members()
        records = [
            {
                "ID": m.id_user,
                "Nama": m.nama,
                "Username": m.username,
                "Email": m.email,
                "NIM/NIDN": m.nim_nidn,
                "Prodi": m.prodi,
                "No Telp": m.no_telp,
                "Status Aktif": m.status_aktif,
                "Kuota Pinjam": m.kuota_pinjam,
            }
            for m in members
        ]
        show_table(records, "Belum ada anggota.")
        if members:
            with st.form("member_form"):
                selected = st.selectbox("Pilih Anggota", [f"{m.id_user} - {m.nama}" for m in members])
                member = next(m for m in members if m.id_user == selected.split(" - ")[0])
                status = st.checkbox("Status Aktif", value=member.status_aktif)
                kuota = st.number_input("Kuota Pinjam", min_value=0, max_value=10, value=int(member.kuota_pinjam))
                col_save, col_delete = st.columns(2)
                save_clicked = col_save.form_submit_button("Simpan Data Anggota", use_container_width=True)
                delete_clicked = col_delete.form_submit_button("Hapus Akun Anggota", use_container_width=True)

            if save_clicked:
                try:
                    auth_service.update_member(member.id_user, status, int(kuota))
                    push_notification("success", "Data anggota berhasil diperbarui.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

            if delete_clicked:
                try:
                    active_loans = peminjaman_service.active_loans_by_user(member.id_user)
                    active_reservations = [
                        reservation
                        for reservation in reservasi_service.reservations_by_user(member.id_user)
                        if reservation.status_reservasi in ["Menunggu", "Dikonfirmasi"]
                    ]
                    if active_loans or active_reservations:
                        raise ValueError("Akun anggota tidak dapat dihapus karena masih memiliki peminjaman atau reservasi aktif.")
                    auth_service.delete_member(member.id_user)
                    push_notification("success", "Akun anggota berhasil dihapus.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    elif page == "Monitoring Peminjaman":
        st.header("Monitoring Peminjaman Buku")
        records = report_service.joined_loans()
        show_table(records, "Belum ada transaksi peminjaman.")

        st.divider()
        with st.container(border=True):
            st.subheader("Proses Pengembalian Manual")
            active = [loan for loan in peminjaman_service.list_loans() if loan.status_peminjaman == "Dipinjam"]

            if active:
                books = {b.id_buku: b.judul for b in buku_service.list_books()}
                with st.form("admin_return_form"):
                    selected = st.selectbox(
                        "Pilih peminjaman aktif",
                        [f"{l.id_peminjaman_buku} - {books.get(l.id_buku, l.id_buku)}" for l in active],
                    )
                    submitted = st.form_submit_button("Kembalikan", use_container_width=True)
                if submitted:
                    try:
                        denda = peminjaman_service.kembalikan_buku(selected.split(" - ")[0])
                        push_notification("success", f"Pengembalian berhasil diproses. Denda: {rupiah(denda)}")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
            else:
                st.info("Tidak ada peminjaman aktif yang perlu diproses.")

    elif page == "Validasi Reservasi":
        st.header("Validasi Reservasi Ruangan")
        records = report_service.joined_reservations()
        show_table(records, "Belum ada data reservasi.")
        pending = [r for r in reservasi_service.list_reservations() if r.status_reservasi == "Menunggu"]
        if pending:
            rooms = {r.id_ruangan: r.nama_ruangan for r in ruangan_service.list_rooms()}
            with st.form("validate_reservation_form"):
                selected = st.selectbox("Pilih Reservasi", [f"{r.id_reservasi} - {rooms.get(r.id_ruangan, r.id_ruangan)} - {r.tanggal_reservasi} {r.jam_mulai}-{r.jam_selesai}" for r in pending])
                action = st.selectbox("Aksi", ["Dikonfirmasi", "Ditolak", "Dibatalkan"])
                submitted = st.form_submit_button("Simpan Status", use_container_width=True)
            if submitted:
                try:
                    reservasi_service.update_status(selected.split(" - ")[0], action)
                    push_notification("success", "Status reservasi berhasil diperbarui.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    elif page == "Import/Export & Laporan":
        st.header("Import CSV/Excel & Export Laporan CSV/PDF")
        table_options = {
            "Users": "users",
            "Books": "books",
            "Rooms": "rooms",
            "Loans": "loans",
            "Reservations": "reservations",
            "Queues": "queues",
        }
        selected_table_label = st.selectbox("Pilih Data", list(table_options.keys()))
        table_name = table_options[selected_table_label]
        records = report_service.table_records(table_name)
        show_table(records, "Belum ada data pada tabel ini.")

        col1, col2 = st.columns(2)
        col1.download_button(
            "Download CSV",
            data=ExportImport.to_csv_bytes(records),
            file_name=f"siperu_{table_name}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        col2.download_button(
            "Download PDF",
            data=ExportImport.to_pdf_bytes(records, f"Laporan {selected_table_label} SIPERU"),
            file_name=f"siperu_{table_name}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.divider()
        st.subheader("Import Data Master")
        st.caption("Import tersedia untuk Books dan Rooms. Gunakan kolom sesuai hasil export agar data terbaca dengan benar.")
        import_target = st.selectbox("Target Import", ["Books", "Rooms"])
        replace = st.checkbox("Replace data lama", value=False)
        uploaded = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx", "xls"])
        if st.button("Import Data", use_container_width=True):
            try:
                imported_records = ExportImport.read_uploaded_file(uploaded)
                if import_target == "Books":
                    total = buku_service.import_books(imported_records, replace)
                else:
                    total = ruangan_service.import_rooms(imported_records, replace)
                push_notification("success", f"Import berhasil. {total} data baru masuk.")
                st.rerun()
            except Exception as error:
                st.error(str(error))
