from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


class CredentialLookupError(RuntimeError):
    pass


if sys.platform == "win32":
    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


    class CREDENTIAL_ATTRIBUTEW(ctypes.Structure):
        _fields_ = [
            ("Keyword", wintypes.LPWSTR),
            ("Flags", wintypes.DWORD),
            ("ValueSize", wintypes.DWORD),
            ("Value", ctypes.POINTER(ctypes.c_ubyte)),
        ]


    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.POINTER(CREDENTIAL_ATTRIBUTEW)),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]


    PCREDENTIALW = ctypes.POINTER(CREDENTIALW)
    _advapi32 = ctypes.WinDLL("Advapi32.dll")
    _cred_read = _advapi32.CredReadW
    _cred_read.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(PCREDENTIALW)]
    _cred_read.restype = wintypes.BOOL
    _cred_free = _advapi32.CredFree
    _cred_free.argtypes = [ctypes.c_void_p]
    _cred_free.restype = None
    _CRED_TYPE_GENERIC = 1


def _decode_credential_blob(raw_bytes: bytes) -> str:
    for encoding in ("utf-16-le", "utf-8"):
        try:
            return raw_bytes.decode(encoding).rstrip("\x00")
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("latin-1", errors="ignore").rstrip("\x00")


def read_windows_generic_credential(target_name: str) -> str:
    if sys.platform != "win32":
        raise CredentialLookupError("Windows Credential Manager lookup is only available on Windows.")

    credential = PCREDENTIALW()
    ok = _cred_read(target_name, _CRED_TYPE_GENERIC, 0, ctypes.byref(credential))
    if not ok:
        error_code = ctypes.GetLastError()
        raise CredentialLookupError(
            f"Credential Manager entry '{target_name}' could not be read (WinError {error_code})."
        )

    try:
        record = credential.contents
        blob_size = int(record.CredentialBlobSize)
        if blob_size <= 0 or not record.CredentialBlob:
            raise CredentialLookupError(f"Credential Manager entry '{target_name}' does not contain a secret.")

        raw_bytes = ctypes.string_at(record.CredentialBlob, blob_size)
        token = _decode_credential_blob(raw_bytes).strip()
        if not token:
            raise CredentialLookupError(f"Credential Manager entry '{target_name}' is empty.")
        return token
    finally:
        _cred_free(credential)