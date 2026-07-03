__all__ = ["build_parser", "main"]


def __getattr__(name: str):
    if name in __all__:
        from kiwoom_cli.main import build_parser, main

        return {"build_parser": build_parser, "main": main}[name]
    raise AttributeError(name)
