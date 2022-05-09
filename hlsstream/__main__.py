# https://www.programmersought.com/article/54568977634/
# https://github.com/kkroening/ffmpeg-python/issues/154
# https://github.com/kkroening/ffmpeg-python/tree/master/examples

from subprocess import Popen
import sys
import time

if __name__ == "__main__":

    processes: list[Popen] = []
    try:
        processes.append(
            Popen([sys.executable, "-m", "hlsstream.sync"], start_new_session=True)
        )
        processes.append(
            Popen([sys.executable, "-m", "hlsstream.api"], start_new_session=True)
        )
        processes.append(
            Popen([sys.executable, "-m", "hlsstream.stream"], start_new_session=True)
        )
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Ctrl C")
    finally:
        for p in processes:
            p.terminate()
            p.wait()
