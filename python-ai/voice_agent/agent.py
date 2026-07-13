import core


def on_status(text):
    print(text)


def on_speak_start():
    pass


def on_speak_end():
    pass


if __name__ == "__main__":
    core.load_models(on_status=on_status)
    core.run_forever({
        "on_status": on_status,
        "on_speak_start": on_speak_start,
        "on_speak_end": on_speak_end,
    })
