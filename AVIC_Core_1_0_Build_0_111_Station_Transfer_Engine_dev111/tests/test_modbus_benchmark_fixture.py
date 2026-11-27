from tools.modbus_load_compare import build_fc03_response


def test_fc03_response_has_valid_modbus_tcp_mbap_and_register_payload():
    response = build_fc03_response(tid=0x1234, unit=7, address=0x0100, count=3)

    assert len(response) == 15
    assert response[0:2] == b"\\x12\\x34"
    assert response[2:4] == b"\\x00\\x00"
    assert int.from_bytes(response[4:6], "big") == len(response) - 6
    assert response[6] == 7
    assert response[7] == 3
    assert response[8] == 6
    assert [int.from_bytes(response[i:i + 2], "big") for i in (9, 11, 13)] == [
        0x0100, 0x0101, 0x0102
    ]


def test_fc03_response_rejects_invalid_register_count():
    import pytest

    with pytest.raises(ValueError):
        build_fc03_response(tid=1, unit=1, address=0, count=0)
    with pytest.raises(ValueError):
        build_fc03_response(tid=1, unit=1, address=65535, count=2)
