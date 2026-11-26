
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
            f"$acl = Get-Acl -LiteralPath '{identity_dir}'; "
            "$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value; "
            "Write-Output ('CURRENT|' + $sid); "
            "Write-Output ('PROTECTED|' + $acl.AreAccessRulesProtected); "
            "foreach ($rule in $acl.Access) { "
            "$resolved = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value; "
            "Write-Output ('ACE|' + $resolved + '|' + $rule.AccessControlType + '|' + "
            "$rule.FileSystemRights + '|' + $rule.InheritanceFlags + '|' + $rule.IsInherited) }"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            check=True,
            capture_output=True,
            encoding="mbcs",
            errors="replace",
            timeout=10,
        )

        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        current_line = next((line for line in lines if line.startswith("CURRENT|")), "")
        protected_line = next((line for line in lines if line.startswith("PROTECTED|")), "")
        assert current_line and protected_line, "Windows did not return the expected ACL information"
        current_sid = current_line.split("|", 1)[1]
        assert current_sid.startswith("S-1-5-21-"), "Could not identify current Windows user SID"
        assert protected_line == "PROTECTED|True", "Identity directory ACL is not protected from inheritance"

        # Resolve SDDL aliases to numeric SIDs before asserting policy.
        # LA is the local built-in Administrator alias (RID 500), not
        # the broad Local Account principal S-1-5-113.
        aces = [line.split("|") for line in lines if line.startswith("ACE|")]
        all_sids = {parts[1] for parts in aces if len(parts) > 1}
        allowed = {current_sid, "S-1-5-18", "S-1-5-32-544", "S-1-3-4"}
        allow_full_control = {
            parts[1] for parts in aces
            if len(parts) == 6 and parts[2] == "Allow"
            and "FullControl" in parts[3]
            and "ContainerInherit" in parts[4] and "ObjectInherit" in parts[4]
            and parts[5] == "False"
        }
        assert {current_sid, "S-1-5-18", "S-1-5-32-544"}.issubset(allow_full_control), (
            f"Required protected FullControl ACEs missing: {aces}"
        )
        assert "S-1-5-113" not in all_sids, f"Broad Local Account access is not permitted: {aces}"
        assert all_sids.issubset(allowed), f"Unexpected ACL principals: {aces}"
