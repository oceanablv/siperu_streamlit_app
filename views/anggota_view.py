from datetime import date, datetime, timedelta
import streamlit as st
from models.user import User, Anggota
from views.components import (
    push_notification,
    render_book_cover,
    render_notifications,
    render_program_studi_input,
    room_records,
    rupiah,
    show_table,
)
from views.transaksi_buku_view import render_baca_buku, render_dashboard_transaksi_buku


def _reservation_datetimes(reservation):
    start = datetime.strptime(
        f"{reservation.tanggal_reservasi} {reservation.jam_mulai}",
        "%Y-%m-%d %H:%M",
    )
    end = datetime.strptime(
        f"{reservation.tanggal_reservasi} {reservation.jam_selesai}",
        "%Y-%m-%d %H:%M",
    )
    return start, end


def _reservation_state(reservation, now: datetime) -> str:
    start, end = _reservation_datetimes(reservation)

    if reservation.status_reservasi == "Dikonfirmasi":
        if start <= now < end:
            return "Sedang berlangsung"
        if now < start:
            return "Akan datang"
        return "Selesai"

    if reservation.status_reservasi == "Menunggu":
        return "Menunggu validasi"

    return reservation.status_reservasi


def _reservation_records(reservations, room_names: dict[str, str], now: datetime) -> list[dict]:
    return [
        {
            "ID Reservasi": reservation.id_reservasi,
            "Ruangan": room_names.get(reservation.id_ruangan, reservation.id_ruangan),
            "Tanggal": reservation.tanggal_reservasi,
            "Waktu": f"{reservation.jam_mulai}-{reservation.jam_selesai}",
            "Keperluan": reservation.keperluan,
            "Status": _reservation_state(reservation, now),
        }
        for reservation in reservations
    ]


def _room_status_records(rooms, reservations, user_names: dict[str, str], now: datetime) -> list[dict]:
    records = []

    for room in rooms:
        room_reservations = [
            reservation
            for reservation in reservations
            if reservation.id_ruangan == room.id_ruangan
        ]
        current_reservations = [
            reservation
            for reservation in room_reservations
            if reservation.status_reservasi == "Dikonfirmasi"
            and _reservation_datetimes(reservation)[0] <= now < _reservation_datetimes(reservation)[1]
        ]
        upcoming_reservations = [
            reservation
            for reservation in room_reservations
            if reservation.status_reservasi in ["Menunggu", "Dikonfirmasi"]
            and _reservation_datetimes(reservation)[0] > now
        ]

        current_reservation = min(
            current_reservations,
            key=lambda reservation: _reservation_datetimes(reservation)[0],
            default=None,
        )
        next_reservation = min(
            upcoming_reservations,
            key=lambda reservation: _reservation_datetimes(reservation)[0],
            default=None,
        )

        if not room.cek_ketersediaan():
            status = room.status_ruangan
        elif current_reservation:
            status = "Dipakai"
        else:
            status = "Kosong"

        records.append(
            {
                "ID Ruangan": room.id_ruangan,
                "Nama Ruangan": room.nama_ruangan,
                "Status Saat Ini": status,
                "Dipakai Oleh": (
                    user_names.get(current_reservation.id_anggota, current_reservation.id_anggota)
                    if current_reservation
                    else "-"
                ),
                "Jadwal Aktif": (
                    f"{current_reservation.jam_mulai}-{current_reservation.jam_selesai}"
                    if current_reservation
                    else "-"
                ),
                "Reservasi Berikutnya": (
                    f"{next_reservation.tanggal_reservasi} "
                    f"{next_reservation.jam_mulai}-{next_reservation.jam_selesai} "
                    f"({next_reservation.status_reservasi})"
                    if next_reservation
                    else "-"
                ),
            }
        )

    return records


def render_dashboard_ruangan(user, auth_service, ruangan_service, reservasi_service) -> None:
    st.header("Status & Reservasi Ruangan")
    now = datetime.now()
    rooms = ruangan_service.list_rooms()
    room_names = {room.id_ruangan: room.nama_ruangan for room in rooms}
    user_names = {member.id_user: member.nama for member in auth_service.list_users()}
    reservations = reservasi_service.list_reservations()
    dashboard_reservations = reservasi_service.active_or_upcoming_reservations_by_user(user.id_user, now)
    current_user_reservations = [
        reservation
        for reservation in dashboard_reservations
        if reservasi_service.is_current_reservation(reservation, now)
    ]

    if current_user_reservations:
        active_room_names = [
            room_names.get(reservation.id_ruangan, reservation.id_ruangan)
            for reservation in current_user_reservations
        ]
        active_until = max(reservation.jam_selesai for reservation in current_user_reservations)
        st.success(
            f"Saat ini Anda sedang menggunakan {', '.join(active_room_names)} sampai pukul {active_until}."
        )
    else:
        st.info("Saat ini Anda tidak sedang menggunakan ruangan.")

    show_table(
        _room_status_records(rooms, reservations, user_names, now),
        "Belum ada data ruangan.",
    )

    st.subheader("Reservasi Ruangan Saya")
    show_table(
        _reservation_records(dashboard_reservations, room_names, now),
        "Tidak ada reservasi ruangan aktif atau mendatang.",
    )

    for reservation in dashboard_reservations:
        is_current = reservasi_service.is_current_reservation(reservation, now)
        room_name = room_names.get(reservation.id_ruangan, reservation.id_ruangan)

        with st.container(border=True):
            col_info, col_time, col_action = st.columns([3, 2, 2])
            col_info.write(f"**{reservation.id_reservasi} - {room_name}**")
            col_info.caption(reservation.keperluan)
            col_time.write(f"**{reservation.tanggal_reservasi}**")
            col_time.caption(
                f"{reservation.jam_mulai}-{reservation.jam_selesai} | {_reservation_state(reservation, now)}"
            )

            if reservation.status_reservasi == "Menunggu":
                if col_action.button(
                    "Batalkan Reservasi",
                    key=f"dashboard_cancel_reservation_{reservation.id_reservasi}",
                    use_container_width=True,
                ):
                    try:
                        reservasi_service.cancel_by_user(reservation.id_reservasi, user.id_user)
                        push_notification("success", "Reservasi berhasil dibatalkan.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

            elif reservation.status_reservasi == "Dikonfirmasi" and is_current:
                extend_col, finish_col = col_action.columns(2)

                if extend_col.button(
                    "Perpanjang 1 Jam",
                    key=f"dashboard_extend_reservation_{reservation.id_reservasi}",
                    use_container_width=True,
                ):
                    try:
                        updated_reservation = reservasi_service.perpanjang_reservasi(
                            reservation.id_reservasi,
                            user.id_user,
                        )
                        push_notification(
                            "success",
                            f"Reservasi berhasil diperpanjang sampai pukul {updated_reservation.jam_selesai}.",
                        )
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

                if finish_col.button(
                    "Akhiri Sekarang",
                    key=f"dashboard_finish_reservation_{reservation.id_reservasi}",
                    use_container_width=True,
                ):
                    try:
                        reservasi_service.akhiri_reservasi_sekarang(
                            reservation.id_reservasi,
                            user.id_user,
                        )
                        push_notification("success", "Reservasi berhasil diakhiri.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))


def render_anggota(user_dict: dict, services: dict):
    user = User.from_dict(user_dict)
    render_notifications()
    auth_service = services["auth"]
    buku_service = services["buku"]
    peminjaman_service = services["peminjaman"]
    ruangan_service = services["ruangan"]
    reservasi_service = services["reservasi"]
    report_service = services["report"]

    st.sidebar.success(f"{user.nama}")
    menu_options = ["Dashboard", "Baca Buku", "Cari & Pinjam Buku", "Pengembalian Buku", "Reservasi Ruangan", "Riwayat", "Profil"]
    target_page = st.session_state.pop("target_anggota_page", None)
    if target_page in menu_options:
        st.session_state["anggota_page_radio"] = target_page
    elif st.session_state.get("anggota_page_radio") not in menu_options:
        st.session_state["anggota_page_radio"] = "Dashboard"

    page = st.sidebar.radio(
        "Menu Anggota",
        menu_options,
        key="anggota_page_radio",
    )

    if st.sidebar.button("Logout", use_container_width=True):
        push_notification("success", "Logout berhasil.")
        st.session_state.pop("user", None)
        st.rerun()

    if page == "Dashboard":
        st.header(user.dashboard_title())
        active_loans = peminjaman_service.active_loans_by_user(user.id_user)
        reservations = reservasi_service.active_or_upcoming_reservations_by_user(user.id_user)
        current_reservations = [
            reservation
            for reservation in reservations
            if reservasi_service.is_current_reservation(reservation)
        ]
        pending_reservations = [
            reservation
            for reservation in reservations
            if reservation.status_reservasi == "Menunggu"
        ]
        queues = peminjaman_service.queues_by_user(user.id_user)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Peminjaman Aktif", len(active_loans))
        col2.metric("Ruangan Dipakai", len(current_reservations))
        col3.metric("Reservasi Menunggu", len(pending_reservations))
        col4.metric("Antrian Buku", len([q for q in queues if q.status_antrian == "Menunggu"]))
        st.info("Dashboard menampilkan status ruangan saat ini, reservasi aktif, dan peminjaman buku Anda.")
        st.divider()
        render_dashboard_ruangan(user, auth_service, ruangan_service, reservasi_service)
        st.divider()
        render_dashboard_transaksi_buku(user, buku_service, peminjaman_service)

    elif page == "Baca Buku":
        render_baca_buku(user, buku_service, peminjaman_service)

    elif page == "Cari & Pinjam Buku":
        st.header("Cari & Pinjam Buku")
        st.caption("Pilih buku dari kartu di bawah. Lama peminjaman otomatis 14 hari dan tidak dapat diubah oleh anggota.")

        if st.session_state.pop("clear_book_search", False):
            st.session_state["book_search_keyword"] = ""

        categories = buku_service.list_categories()
        category_options = {"Semua": "Semua Kategori"}
        category_options.update({c.id_kategori: c.nama_kategori for c in categories})
        col1, col2 = st.columns([2, 1])
        keyword = col1.text_input("Cari judul/penulis/penerbit", key="book_search_keyword")
        selected_category_label = col2.selectbox("Kategori", list(category_options.values()))
        selected_category_id = next(k for k, v in category_options.items() if v == selected_category_label)
        books = buku_service.search_books(keyword, selected_category_id)

        if not books:
            st.info("Buku tidak ditemukan.")
        else:
            category_map = buku_service.category_map()
            for index in range(0, len(books), 3):
                cols = st.columns(3)
                for col, book in zip(cols, books[index:index + 3]):
                    with col.container(border=True):
                        render_book_cover(book)
                        st.subheader(book.judul)
                        st.caption(f"{book.penulis} • {book.penerbit} • {book.tahun_terbit}")
                        st.write(f"Kategori: **{category_map.get(book.kategori_id, book.kategori_id)}**")
                        st.metric("Sisa Stok", book.stok)
                        st.caption("Lama pinjam: 14 hari")
                        st.caption("PDF reader tersedia" if book.bisa_dibaca_pdf() else "PDF reader belum tersedia")

                        if not book.bisa_dibaca_pdf():
                            button_label = "PDF Belum Tersedia"
                        else:
                            button_label = "Pinjam Buku" if book.stok > 0 else "Masuk Antrian"

                        if st.button(
                            button_label,
                            key=f"borrow_{book.id_buku}",
                            use_container_width=True,
                            disabled=not book.bisa_dibaca_pdf(),
                        ):
                            try:
                                status, message = peminjaman_service.pinjam_buku(user.id_user, book.id_buku)
                                if status == "success":
                                    push_notification("success", message)
                                    st.session_state["selected_pdf_loan_id"] = ""
                                else:
                                    push_notification("warning", message)
                                st.session_state["clear_book_search"] = True
                                st.rerun()
                            except ValueError as error:
                                st.error(str(error))

    elif page == "Pengembalian Buku":
        st.header("Pengembalian Buku")
        active_loans = peminjaman_service.active_loans_by_user(user.id_user)
        books_by_id = {b.id_buku: b for b in buku_service.list_books()}
        records = []
        for loan in active_loans:
            book = books_by_id.get(loan.id_buku)
            records.append(
                {
                    "ID Peminjaman": loan.id_peminjaman_buku,
                    "Judul Buku": book.judul if book else loan.id_buku,
                    "Tanggal Pinjam": loan.tanggal_pinjam,
                    "Batas Kembali": loan.tanggal_kembali,
                    "Status": loan.status_peminjaman,
                }
            )
        show_table(records, "Tidak ada peminjaman aktif.")
        if active_loans:
            with st.form("return_form"):
                option = st.selectbox(
                    "Pilih peminjaman",
                    [
                        f"{l.id_peminjaman_buku} - {books_by_id.get(l.id_buku).judul if books_by_id.get(l.id_buku) else l.id_buku}"
                        for l in active_loans
                    ],
                )
                submitted = st.form_submit_button("Kembalikan Buku", use_container_width=True)
            if submitted:
                try:
                    id_pinjam = option.split(" - ")[0]
                    denda = peminjaman_service.kembalikan_buku(id_pinjam)
                    st.session_state.pop("selected_pdf_loan_id", None)
                    push_notification("success", f"Buku berhasil dikembalikan. Denda: {rupiah(denda)}")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

    elif page == "Reservasi Ruangan":
        st.header("Reservasi Ruangan")

        if st.session_state.pop("clear_reservation_form", False):
            st.session_state["reservation_need"] = ""

        rooms = ruangan_service.list_rooms()
        show_table(room_records(rooms), "Belum ada data ruangan.")

        available_rooms = [r for r in rooms if r.cek_ketersediaan()]

        if available_rooms:
            st.info(
                "Reservasi ruangan hanya dapat dilakukan mulai pukul 08:00 sampai 19:00. "
                "Jam selesai maksimal pukul 21:00 dengan durasi awal maksimal 2 jam."
            )

            # Membuat pilihan jam mulai dari 08:00 sampai 19:00
            jam_mulai_options = []
            cursor = datetime.strptime("08:00", "%H:%M")
            batas_jam_mulai = datetime.strptime("19:00", "%H:%M")

            while cursor <= batas_jam_mulai:
                jam_mulai_options.append(cursor.strftime("%H:%M"))
                cursor += timedelta(minutes=30)

            with st.container(border=True):
                room_option = st.selectbox(
                    "Pilih Ruangan",
                    [
                        f"{r.id_ruangan} - {r.nama_ruangan} (kapasitas {r.kapasitas})"
                        for r in available_rooms
                    ],
                )

                tanggal = st.date_input(
                    "Tanggal Reservasi",
                    min_value=date.today()
                )

                jam_mulai_str = st.selectbox(
                    "Jam Mulai",
                    jam_mulai_options,
                    index=2
                )

                # Membuat pilihan jam selesai berdasarkan jam mulai
                # Maksimal 2 jam setelah jam mulai dan tidak boleh melewati jam 21:00
                mulai_dt = datetime.strptime(jam_mulai_str, "%H:%M")
                tutup_dt = datetime.strptime("21:00", "%H:%M")
                maksimal_selesai_dt = min(
                    mulai_dt + timedelta(hours=2),
                    tutup_dt
                )

                jam_selesai_options = []
                cursor_selesai = mulai_dt + timedelta(minutes=30)

                while cursor_selesai <= maksimal_selesai_dt:
                    jam_selesai_options.append(cursor_selesai.strftime("%H:%M"))
                    cursor_selesai += timedelta(minutes=30)

                jam_selesai_str = st.selectbox(
                    "Jam Selesai",
                    jam_selesai_options,
                    index=len(jam_selesai_options) - 1
                )

                selesai_dt = datetime.strptime(jam_selesai_str, "%H:%M")
                durasi_jam = (selesai_dt - mulai_dt).total_seconds() / 3600

                st.info(
                    f"Durasi reservasi: {durasi_jam:g} jam. "
                    "Durasi awal maksimal 2 jam. Jika ingin lebih lama, gunakan fitur perpanjangan."
                )

                keperluan = st.text_area("Keperluan", key="reservation_need")

                submitted = st.button(
                    "Ajukan Reservasi",
                    use_container_width=True
                )

            if submitted:
                try:
                    id_ruangan = room_option.split(" - ")[0]

                    reservasi = reservasi_service.buat_reservasi(
                        user.id_user,
                        id_ruangan,
                        tanggal.isoformat(),
                        jam_mulai_str,
                        jam_selesai_str,
                        keperluan,
                    )

                    st.session_state["reservation_success"] = (
                        f"✅ Reservasi berhasil diajukan.\n\n"
                        f"ID Reservasi: {reservasi.id_reservasi}\n"
                        f"Status: Menunggu validasi admin."
                    )
                    push_notification(
                        "success",
                        (
                            f"Reservasi berhasil diajukan. "
                            f"ID Reservasi: {reservasi.id_reservasi}. "
                            "Status: Menunggu validasi admin."
                        ),
                    )
                    st.session_state["clear_reservation_form"] = True
                    st.rerun()

                except ValueError as error:
                    st.error(str(error))

        else:
            st.warning("Tidak ada ruangan yang tersedia untuk reservasi.")

    elif page == "Riwayat":
        st.header("Riwayat Anggota")
        tab1, tab2, tab3 = st.tabs(["Peminjaman Buku", "Reservasi Ruangan", "Antrian Buku"])
        books = {b.id_buku: b.judul for b in buku_service.list_books()}
        rooms = {r.id_ruangan: r.nama_ruangan for r in ruangan_service.list_rooms()}

        with tab1:
            records = []
            for loan in peminjaman_service.loans_by_user(user.id_user):
                if loan.sedang_dipinjam():
                    continue
                item = loan.to_dict()
                item["judul_buku"] = books.get(loan.id_buku, loan.id_buku)
                records.append(item)
            show_table(records, "Belum ada riwayat peminjaman lampau.")

        with tab2:
            reservations = reservasi_service.history_reservations_by_user(user.id_user)
            records = []
            for reservation in reservations:
                item = reservation.to_dict()
                item["nama_ruangan"] = rooms.get(reservation.id_ruangan, reservation.id_ruangan)
                records.append(item)
            show_table(records, "Belum ada riwayat reservasi lampau.")

        with tab3:
            queues = peminjaman_service.queues_by_user(user.id_user)
            records = []
            for queue in queues:
                item = queue.to_dict()
                item["judul_buku"] = books.get(queue.id_buku, queue.id_buku)
                records.append(item)
            show_table(records, "Belum ada data antrian.")

    elif page == "Profil":
        st.header("Profil Saya")
        with st.form("profile_form"):
            nama = st.text_input("Nama", value=user.nama)
            email = st.text_input("Email", value=user.email)
            prodi = render_program_studi_input(
                value=user.prodi if isinstance(user, Anggota) else "",
                key="profile_program_studi",
            )
            no_telp = st.text_input("No. Telepon", value=user.no_telp if isinstance(user, Anggota) else "")
            submitted = st.form_submit_button("Simpan Profil", use_container_width=True)
        if submitted:
            try:
                updated = auth_service.update_profile(user.id_user, nama, email, prodi, no_telp)
                st.session_state["user"] = updated.to_dict()
                push_notification("success", "Profil berhasil diperbarui.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

        with st.expander("Ubah Password"):
            with st.form("password_form", clear_on_submit=True):
                old_password = st.text_input("Password Lama", type="password")
                new_password = st.text_input("Password Baru", type="password")
                submitted = st.form_submit_button("Ubah Password")
            if submitted:
                try:
                    auth_service.change_password(user.id_user, old_password, new_password)
                    push_notification("success", "Password berhasil diubah.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
