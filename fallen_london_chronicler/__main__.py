from fallen_london_chronicler.config import config
from fallen_london_chronicler.log import LOGGING_CONFIG


def main():
    import uvicorn

    uvicorn.run(
        "fallen_london_chronicler.app:app",
        host="0.0.0.0",
        port=config.app_port,
        debug=config.debug,
        log_config=LOGGING_CONFIG,
    )


if __name__ == '__main__':
    main()
