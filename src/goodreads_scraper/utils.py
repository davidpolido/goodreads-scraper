def progress(current, total, msg):
    print(f"\r{msg}[ {current} / {total} ]", end="")
    if current == total:
        print(" - Done!")
