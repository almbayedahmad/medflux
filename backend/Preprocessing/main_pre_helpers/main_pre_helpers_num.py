def as_int(x, default=0):
    try: return int(x)
    except: return default


def as_float(x, default=0.0):
    try: return float(x)
    except: return default
