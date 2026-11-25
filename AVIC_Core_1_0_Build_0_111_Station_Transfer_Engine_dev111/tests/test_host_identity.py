
import uuid
import os
import re
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
        identity_dir = str(identity_file.parent).replace("'", "''")
        command = (
            f"$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value; "
            f"$acl = Get-Acl -LiteralPath '{identity_dir}'; "
            "Write-Output $sid; Write-Output $acl.Sddl"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            check=True,
            capture_output=True,
            encoding="mbcs",
            errors="replace",
            timeout=10,
        )

        lines = result.stdout.splitlines()
        assert len(lines) >= 2, "Windows did not return the expected ACL information"

        current_sid = lines[0].strip()
        sddl = lines[1].strip()

        assert current_sid.startswith("S-1-5-21-"), "Could not identify current Windows user SID"
        assert "D:PAI" in sddl, "Identity directory ACL is not protected from inheritance"

        aces = re.findall(r"\(A;OICI;FA;;;([^)]+)\)", sddl)
        # Owner Rights (OW) may exist on hosted Windows runners.
        assert {"SY", "BA", current_sid}.issubset(set(aces)), f"Required ACL principals missing: {aces}"
        assert "LA" not in aces, f"Broad Local Account access is not permitted: {aces}"
        assert set(aces).issubset({"OW", "SY", "BA", current_sid}), f"Unexpected ACL principals: {aces}"
