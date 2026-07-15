import streamlit as st

from views.components import pdf_fullscreen_key, render_pdf_reader, show_table


def loan_records(active_loans, books_by_id: dict) -> list[dict]:
    records = []
    for loan in active_loans:
        book = books_by_id.get(loan.id_buku)
        records.append(
            {
                "ID Peminjaman": loan.id_peminjaman_buku,
                "Judul Buku": book.judul if book else loan.id_buku,
                "Tanggal Pinjam": loan.tanggal_pinjam,
                "Batas Akses": loan.tanggal_kembali,
                "Status": loan.status_peminjaman,
                "PDF": "Tersedia" if book and book.link_pdf else "Belum tersedia",
            }
        )
    return records


def _active_loan_context(user, buku_service, peminjaman_service):
    active_loans = peminjaman_service.active_loans_by_user(user.id_user)
    books_by_id = {book.id_buku: book for book in buku_service.list_books()}
    return active_loans, books_by_id


def _selected_loan(active_loans):
    selected_loan_id = st.session_state.get("selected_pdf_loan_id")
    return next((loan for loan in active_loans if loan.id_peminjaman_buku == selected_loan_id), None)


def render_dashboard_transaksi_buku(user, buku_service, peminjaman_service) -> None:
    st.header("Transaksi Buku Sedang Dipinjam")
    active_loans, books_by_id = _active_loan_context(user, buku_service, peminjaman_service)

    show_table(
        loan_records(active_loans, books_by_id),
        "Tidak ada buku yang sedang dipinjam.",
    )

    if not active_loans:
        st.session_state.pop("selected_pdf_loan_id", None)
        return

    for loan in active_loans:
        book = books_by_id.get(loan.id_buku)
        title = book.judul if book else loan.id_buku

        with st.container(border=True):
            col_title, col_date, col_action = st.columns([3, 2, 1])
            col_title.write(f"**{title}**")
            col_title.caption(loan.ringkasan_transaksi())
            col_date.write(f"Batas akses: **{loan.tanggal_kembali}**")

            if col_action.button(
                "Baca PDF",
                key=f"dashboard_read_{loan.id_peminjaman_buku}",
                use_container_width=True,
                disabled=not (book and book.link_pdf),
            ):
                st.session_state["selected_pdf_loan_id"] = loan.id_peminjaman_buku
                st.session_state["target_anggota_page"] = "Baca Buku"
                st.rerun()


def render_baca_buku(user, buku_service, peminjaman_service) -> None:
    active_loans, books_by_id = _active_loan_context(user, buku_service, peminjaman_service)

    if not active_loans:
        st.header("Baca Buku")
        st.session_state.pop("selected_pdf_loan_id", None)
        st.info("Tidak ada buku yang sedang dipinjam.")
        return

    selected_loan = _selected_loan(active_loans) or active_loans[0]
    selected_index = active_loans.index(selected_loan)
    selected_book = books_by_id.get(selected_loan.id_buku)
    fullscreen_active = bool(
        selected_book
        and st.session_state.get(pdf_fullscreen_key(selected_book.judul, selected_book.link_pdf), False)
    )

    if fullscreen_active:
        _apply_reader_fullscreen_layout()
    else:
        st.header("Baca Buku")
        option = st.selectbox(
            "Pilih buku",
            [
                f"{loan.id_peminjaman_buku} - {books_by_id.get(loan.id_buku).judul if books_by_id.get(loan.id_buku) else loan.id_buku}"
                for loan in active_loans
            ],
            index=selected_index,
        )
        selected_id = option.split(" - ")[0]
        selected_loan = next((loan for loan in active_loans if loan.id_peminjaman_buku == selected_id), None)
        st.session_state["selected_pdf_loan_id"] = selected_id

    if selected_loan is None:
        return

    selected_book = books_by_id.get(selected_loan.id_buku)
    if selected_book is None:
        st.warning("Data buku untuk transaksi ini tidak ditemukan.")
        return

    if not fullscreen_active:
        st.divider()
    render_pdf_reader(selected_book.link_pdf, selected_book.judul)


def _apply_reader_fullscreen_layout() -> None:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }
            [data-testid="collapsedControl"] {
                display: block !important;
            }
            [data-testid="stAppViewContainer"] > .main {
                margin-left: 0 !important;
            }
            .block-container {
                max-width: 100% !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
                padding-top: 1.25rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
