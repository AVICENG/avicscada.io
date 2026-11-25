from pathlib import Path
import re
import shutil
import subprocess

HTML = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "logic.html"
SOURCE = HTML.read_text(encoding="utf-8")


def test_fbd_portable_package_has_manifest_and_sha256_verification():
    assert "schema:'avic.fbd.project-package'" in SOURCE
    assert "schemaVersion:1" in SOURCE
    assert "algorithm:'SHA-256'" in SOURCE
    assert "Контрольная сумма не совпадает" in SOURCE
    assert ".avicfbd.json" in SOURCE


def test_fbd_import_validates_before_replacing_and_supports_legacy_json():
    assert "function validateFbdImport(o)" in SOURCE
    assert "function readFbdPackage(text)" in SOURCE
    assert "validateFbdImport(candidate);if(!confirm(" in SOURCE
    assert "importData(candidate)" in SOURCE
    assert "повторяющийся ID страницы" in SOURCE
    assert "Связь ссылается на неизвестный блок" in SOURCE


def test_schedule_block_is_editable_and_included_in_fbd_simulation():
    assert "SCHEDULE:{label:'Schedule'" in SOURCE
    assert "if(type==='SCHEDULE')params.schedule=" in SOURCE
    assert "if(m.type==='SCHEDULE'){const result=AVICFBDLogic.evaluateSchedule" in SOURCE
    assert "function evaluateSchedule(config, instant=new Date())" in SOURCE
    assert "weeklyEvents" in SOURCE and "exceptions" in SOURCE
    assert "scheduleCopy" in SOURCE and "exceptionAdd" in SOURCE
    assert "schValueType" in SOURCE
    assert "часовой пояс IANA" in SOURCE


def test_schedule_logic_weekly_exception_override_timezone_and_overnight():
    node = shutil.which("node")
    if not node:
        return
    match = re.search(r"<script>(/\* AVIC FBD deterministic logic subset\..*?)</script>", SOURCE, re.S)
    assert match, "FBD deterministic logic script not found"
    js = match.group(1) + r"""
const assert=require('node:assert/strict');
const L=globalThis.AVICFBDLogic;
const monday=new Date('2026-11-23T08:30:00Z'); // Monday 09:30 Europe/Berlin
let r=L.evaluateSchedule({timezone:'Europe/Berlin',defaultValue:0,weeklyEvents:[{dayOfWeek:1,startMinute:540,endMinute:1020,value:1}]},monday);
assert.equal(r.value,1); assert.equal(r.source,'WEEKLY');
r=L.evaluateSchedule({timezone:'Europe/Berlin',defaultValue:0,weeklyEvents:[{dayOfWeek:1,startMinute:540,endMinute:1020,value:1}],exceptions:[{startDate:'2026-11-23',endDate:'2026-11-23',value:0,priority:10}]},monday);
assert.equal(r.value,0); assert.equal(r.source,'EXCEPTION');
r=L.evaluateSchedule({timezone:'Europe/Berlin',defaultValue:0,override:{value:1,expiresAt:'2026-11-23T09:00:00Z'}},monday);
assert.equal(r.value,1); assert.equal(r.source,'OVERRIDE');
const overnight=new Date('2026-11-24T00:30:00Z'); // Tue 01:30 Berlin
r=L.evaluateSchedule({timezone:'Europe/Berlin',defaultValue:0,weeklyEvents:[{dayOfWeek:1,startMinute:1320,endMinute:360,value:1}]},overnight);
assert.equal(r.value,1); assert.equal(r.source,'WEEKLY');
const dst=new Date('2026-03-29T01:30:00Z');
r=L.evaluateSchedule({timezone:'Europe/Berlin',defaultValue:7},dst);
assert.equal(r.localDate,'2026-03-29');
"""
    run = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=20)
    assert run.returncode == 0, run.stdout + run.stderr
