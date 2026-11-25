from avic_core.trend_tsite import parse_tsite, TrendTSiteError


def test_tsite_parser_reads_lans_devices_modules_and_raw_parameters():
    xml = b"""<?xml version='1.0'?>
    <TrendProject><Site CncAddress='4' TuaString='T/Site/TCP,,,192.0.2.10,10004'>
      <Internetwork><Lan IsLocal='True' LanNumber='21'><Device DeviceNumber='1001' VersionString='IQ4NC Iss3.4'>
        <DeviceOverview DeviceType='q' MajorVersion='3' MinorVersion='4' HexEncoded='711B' Revision='0'/>
        <Module Name='R1' SubTypeNumber='-1'><Param Name='D' Type='2' Value='AHU-1'/></Module>
      </Device></Lan></Internetwork></Site></TrendProject>"""
    result = parse_tsite(xml)
    assert result["device_count"] == 1
    assert result["module_count"] == 1
    assert result["parameter_count"] == 1
    device = result["sites"][0]["lans"][0]["devices"][0]
    assert device["device_number"] == 1001
    assert device["modules"][0]["parameters"][0]["raw_value"] == "AHU-1"
    assert result["import_policy"]["physical_points_created"] is False


def test_tsite_parser_rejects_non_trend_root():
    try:
        parse_tsite(b"<Other/>")
        assert False, "root must be TrendProject"
    except TrendTSiteError as exc:
        assert "TrendProject" in str(exc)


def test_tsite_parser_rejects_bad_integer():
    try:
        parse_tsite(b"<TrendProject><Site><Internetwork><Lan LanNumber='bad'/></Internetwork></Site></TrendProject>")
        assert False, "bad LAN number must be rejected"
    except TrendTSiteError as exc:
        assert "LanNumber" in str(exc)
