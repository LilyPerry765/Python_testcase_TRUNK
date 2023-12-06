def timer_hangup(raw_channel):
    """
    Hang up a raw channel after max duration of a call
    Use this method with threading.Timer
    Timer(
        settings.MAX_CALL_DURATION_SECONDS,
        timer_hangup,
        [self.machine.channel.raw_channel],
    ).start()
    :return:
    """
    try:
        raw_channel.hangup()
        print("HANG UP MAX DURATION")
    except Exception:
        pass
