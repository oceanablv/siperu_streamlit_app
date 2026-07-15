import streamlit as st
from views.components import push_notification, render_notifications, render_program_studi_input


def render_auth(auth_service):
    render_notifications()
    st.title("SIPERU")
    st.caption("Sistem Peminjaman Buku dan Reservasi Ruangan Perpustakaan")

    tab_login, tab_register = st.tabs(["Login", "Register Anggota"])

    with tab_login:
        with st.form("login_form", clear_on_submit=True):
            identifier = st.text_input("Username atau Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            try:
                user = auth_service.login(identifier, password)
                st.session_state["user"] = user.to_dict()
                push_notification("success", f"Login berhasil. Selamat datang, {user.nama}.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

        with st.expander("Akun demo"):
            st.write("Admin: `admin` / `admin123`")
            st.write("Anggota: `anggota` / `anggota123`")

    with tab_register:
        with st.form("register_form", clear_on_submit=True):
            nama = st.text_input("Nama Lengkap")
            username = st.text_input("Username Baru")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            nim_nidn = st.text_input("NIM/NIDN")
            prodi = render_program_studi_input(key="register_program_studi")
            no_telp = st.text_input("No. Telepon")
            submitted = st.form_submit_button("Daftar", use_container_width=True)
        if submitted:
            try:
                auth_service.register_anggota(nama, username, email, password, nim_nidn, prodi, no_telp)
                push_notification("success", "Register berhasil. Silakan login menggunakan akun baru.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
