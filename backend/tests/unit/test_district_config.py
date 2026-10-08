from backend.app.core.district_config import DistrictConfig, load_district_config


def test_load_wayanad_config():
    config = load_district_config("wayanad")
    assert config.id == "wayanad"
    assert config.name == "Wayanad"
    assert config.state == "Kerala"
    assert len(config.bbox) == 4
    assert config.projected_crs == "EPSG:32643"
    assert config.weights.landslide["slope"] == 0.30
    assert len(config.historical_events) >= 1
    assert config.historical_events[0].name == "Meppadi Chooralmala Debris Flow"


def test_load_idukki_config():
    config = load_district_config("idukki")
    assert config.id == "idukki"
    assert config.name == "Idukki"
    assert config.state == "Kerala"
