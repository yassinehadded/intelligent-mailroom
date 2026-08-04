from src.config import get_settings


def test_configuration():
    settings = get_settings()

    print(settings.app_name)
    print(settings.maarch_url)

    assert settings.app_name == "Intelligent Mailroom"
    assert settings.maarch_url is not None