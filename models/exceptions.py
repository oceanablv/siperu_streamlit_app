class SiperuError(ValueError):
    """Exception dasar SIPERU.

    Exception handling:
    class ini tetap mewarisi ValueError agar seluruh try/except ValueError
    yang sudah ada di view tetap berjalan tanpa perubahan fitur.
    """


class DomainValidationError(SiperuError):
    """Exception untuk validasi domain, misalnya stok negatif atau input kosong."""


class ResourceUnavailableError(SiperuError):
    """Exception untuk resource yang tidak tersedia, misalnya stok tidak cukup."""
