from src.config import get_settings


settings = get_settings()

print("Application:", settings.app_name)
print("Environment:", settings.app_env)
print("Maarch URL:", settings.maarch_url)
print("Email port:", settings.email_port)