from backend.app.core.settings import Settings, get_settings


def test_settings_initialization():
    settings = get_settings()
    assert settings.APP_NAME == "Surakshit Basti API"
    assert settings.DB_NAME == "surakshit_basti"
    assert isinstance(settings.cors_origins_list, list)
    assert len(settings.cors_origins_list) >= 1


def test_settings_database_url():
    settings = get_settings()
    url = settings.database_url
    assert url.drivername == "postgresql+psycopg2"
    assert url.database == "surakshit_basti"
