
import uuid
import os
import re
import csv
import ctypes
import subprocess
import pytest
from avic_core.licensing import HostIdentity, HostIdentityError


def test_host_id_stable_for_same_installation(tmp_path):
    first = HostIdentity(tmp_path, lambda: "machine-guid-12345678").get_host_id()
    second = HostIdentity(tmp_path, lambda: "machine-guid-12345678").get_host_id()
    assert first == second
    assert first.startswith("AVIC-")
    assert len(first.split("-")) == 5


def test_host_id_changes_for_other_machine(tmp_path):
    first = HostIdentity(tmp_path, lambda: "machine-guid-12345678").get_host_id()
    second = HostIdentity(tmp_path, lambda: "machine-guid-87654321").get_host_id()
    assert first != second


def test_host_id_changes_for_new_installation(tmp_path):
    a = HostIdentity(tmp_path / "a", lambda: "machine-guid-12345678").get_host_id()
    b = HostIdentity(tmp_path / "b", lambda: "machine-guid-12345678").get_host_id()
    assert a != b


def test_bad_machine_id_fails_closed(tmp_path):
    with pytest.raises(HostIdentityError):
        HostIdentity(tmp_path, lambda: "x").get_host_id()


def test_installation_identity_is_uuid_and_private(tmp_path):
    HostIdentity(tmp_path, lambda: "machine-guid-12345678").get_host_id()
    identity_file = tmp_path / "identity" / "installation_id"
    uuid.UUID(identity_file.read_text(encoding="ascii").strip())

    if os.name == "posix":
        assert identity_file.stat().st_mode & 0o077 == 0
    else:
        def read_sddl(path):
            from ctypes import wintypes

            advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            get_file_security = advapi32.GetFileSecurityW
            get_file_security.argtypes = [
                wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p,
                wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
            ]
            get_file_security.restype = wintypes.BOOL
            convert = advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW
            convert.argtypes = [
                ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                ctypes.POINTER(wintypes.LPWSTR), ctypes.POINTER(wintypes.DWORD),
            ]
            convert.restype = wintypes.BOOL
            local_free = kernel32.LocalFree
            local_free.argtypes = [ctypes.c_void_p]
            local_free.restype = ctypes.c_void_p

            needed = wintypes.DWORD()
            get_file_security(str(path), 0x00000004, None, 0, ctypes.byref(needed))
            if not needed.value:
                raise ctypes.WinError(ctypes.get_last_error())
            descriptor = ctypes.create_string_buffer(needed.value)
            if not get_file_security(str(path), 0x00000004, descriptor, needed.value, ctypes.byref(needed)):
                raise ctypes.WinError(ctypes.get_last_error())
            sddl_ptr = wintypes.LPWSTR()
            if not convert(ctypes.cast(descriptor, ctypes.c_void_p), 1, 0x00000004,
                           ctypes.byref(sddl_ptr), None):
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                return ctypes.wstring_at(sddl_ptr)
            finally:
                local_free(sddl_ptr)

        who = subprocess.run(
            ["whoami", "/user", "/fo", "csv", "/nh"],
            check=True, capture_output=True, text=True, timeout=10,
        )
        rows = list(csv.reader(line for line in who.stdout.splitlines() if line.strip()))
        current_sid = rows[0][-1].strip() if rows and rows[0] else ""
        assert current_sid.startswith("S-1-5-21-"), "Could not identify current Windows user SID"

        def assert_acl(path, directory):
            sddl = read_sddl(path)
            assert "D:P" in sddl, f"ACL is not protected from inheritance: {sddl}"
            aces = [part.split(";") for part in re.findall(r"\((A;[^)]*)\)", sddl)]
            sid_aliases = {"SY": "S-1-5-18", "BA": "S-1-5-32-544"}
            normalize_sid = lambda sid: sid_aliases.get(sid, sid)
            all_sids = {normalize_sid(parts[5]) for parts in aces if len(parts) == 6}
            allowed = {current_sid, "S-1-5-18", "S-1-5-32-544"}
            full_control = {
                normalize_sid(parts[5]) for parts in aces
                if len(parts) == 6 and parts[0] == "A" and parts[2] == "FA"
                and (not directory or "OICI" in parts[1])
            }
            assert {current_sid, "S-1-5-18", "S-1-5-32-544"}.issubset(full_control), (
                f"Required protected FullControl ACEs missing: {sddl}"
            )
            assert "S-1-5-113" not in all_sids, f"Broad Local Account access is not permitted: {sddl}"
            assert all_sids.issubset(allowed), f"Unexpected ACL principals: {sddl}"

        assert_acl(identity_file.parent, directory=True)
        assert_acl(identity_file, directory=False)
