# DevelNote: need to pass in localtz now
def WindowsTime(low, high, localtz):
    "Convert the Windows time in 100 nanosecond intervals since Jan 1, 1601 to time in seconds since Jan 1, 1970"
    # Windows NT time is specified as the number of 100 nanosecond intervals since January 1, 1601.
    # UNIX time is specified as the number of seconds since January 1, 1970.
    # There are 134,774 days (or 11,644,473,600 seconds) between these dates.

    if (low == 0) and (high == 0):
        return 0

    # t = float(high) * 2 ** 32 + low

    # The '//' does a floor on the float value, where *1e-7 does not, resulting in an off by one second error
    # However, doing the floor loses the usecs....
    # return (t * 1e-7 - 11644473600)
    return ((high) * 429.4967296 + low * 1e-7 - 11644473600)
    # return((t//10000000)-11644473600)


def hexdump(chars, sep, width):
    while chars:
        line = chars[:width]
        chars = chars[width:]
        line = line.ljust(width, '\000')
        print "%s%s%s" % (sep.join("%02x" % ord(c) for c in line),
                          sep, quotechars(line))


def quotechars(chars):
    return ''.join(['.', c][c.isalnum()] for c in chars)
