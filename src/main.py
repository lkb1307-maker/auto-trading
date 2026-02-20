from __future__ import annotations

from src.app.bot import Bot
from src.config.logging_setup import configure_logging
from src.config.settings import load_settings
from src.notify.telegram import TelegramNotifier


def main() -> None:
    settings = load_settings()
    logger = configure_logging(settings.log_level)

    notifier = TelegramNotifier(
        token=settings.telegram_token,
        chat_id=settings.telegram_chat_id,
        logger=logger,
    )

    bot = Bot(settings=settings, notifier=notifier, logger=logger)
    bot.run_once()


if __name__ == "__main__":
    main()
