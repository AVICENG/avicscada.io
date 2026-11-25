from avic_core.ui.engineering_tree import EngineeringTreeService


def test_fbd_point_provenance_resolves_exact_owner_and_one_based_output():
    page = {"id": "page-a", "code": "P2", "name": "Page 2"}
    module = {"id": "module-a", "no": 7, "tag": "COMB_007", "type": "COMBINATION",
              "outs": [{"id": "o0", "name": "JK"}, {"id": "o1", "name": "Q"}]}
    point = {"source": {"pageId": "page-a", "moduleId": "module-a", "moduleNo": 7,
                        "moduleType": "COMBINATION", "portIndex": 1, "portName": "Q"}}
    result = EngineeringTreeService._fbd_point_provenance(
        point, {"page-a": page}, {"module-a": (page, module)})
    assert result["resolved"] is True
    assert result["page_code"] == "P2"
    assert result["module_tag"] == "COMB_007"
    assert result["output_index"] == 1
    assert result["output_number"] == 2
    assert result["output_name"] == "Q"
    assert result["label"] == "P2 · COMB_007 · OUT2 (Q)"


def test_fbd_point_provenance_does_not_invent_missing_source():
    result = EngineeringTreeService._fbd_point_provenance({"source": {}}, {}, {})
    assert result["resolved"] is False
    assert result["page_id"] is None
    assert result["module_id"] is None
    assert result["output_number"] is None
    assert "OUT?" in result["label"]
