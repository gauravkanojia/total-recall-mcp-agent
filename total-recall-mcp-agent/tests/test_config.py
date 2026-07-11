from app.core.config import settings


def test_settings():
    print(settings.APP_NAME)
    print(settings.PORT)
    print(settings.ENVIRONMENT)
    assert settings.APP_NAME == "Total-Recall MCP Agent"
    assert settings.PORT == 4646
    assert settings.ENVIRONMENT == "development"
