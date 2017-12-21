def backoff(attempts):
    """
    Delay increases very rapidly with the number of attemps:
    1, 2, 4, 8, 16, 32, ...

    """
    return 2 ** attempts
