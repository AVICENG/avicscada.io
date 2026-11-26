import re
from pathlib import Path

from avic_core.logic_fbd import FBDService
from avic_core.logic_fbd_studio import FBDStudioService


def test_all_editor_blocks_have_matching_core_and_compiler_contracts():
    expected = {
        "BOOL_INPUT", "FLOAT_INPUT", "POINT_INPUT", "ANALOG_INPUT", "EXTERNAL_SENSOR",
        "BOOL_OUTPUT", "FLOAT_OUTPUT", "COMBINATION", "PID_LOOP", "AND", "OR", "NOT",
        "ADD", "SUB", "MUL", "DIV", "COMPARE_GT", "COMPARE_LT", "LIMIT", "SCALE",
        "SELECT", "HYSTERESIS", "DELAY", "LATCH", "SWITCH", "KNOB", "TIME",
        "SCHEDULE", "CONSTANT",
    }
    assert set(FBDService.BLOCKS) == expected
    assert set(FBDStudioService._COMPILER_BLOCKS) == expected

    html_path = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "logic.html"
    html = html_path.read_text(encoding="utf-8")
    definitions = {}
    pattern = re.compile(
        r"([A-Z_]+):\{label:'[^']*',ins:\[([^\]]*)\],outs:\[([^\]]*)\]"
    )
    for match in pattern.finditer(html):
        block_type, inputs, outputs = match.groups()
        if block_type in expected:
            definitions[block_type] = {
                "inputs": re.findall(r"'([^']+)'", inputs),
                "outputs": re.findall(r"'([^']+)'", outputs),
            }
    assert set(definitions) == expected
    for block_type in sorted(expected):
        assert set(definitions[block_type]["inputs"]) == set(FBDService.BLOCKS[block_type]["inputs"]), block_type
        assert set(definitions[block_type]["outputs"]) == set(FBDService.BLOCKS[block_type]["outputs"]), block_type
