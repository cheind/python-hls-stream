import dataclasses
from typing import Iterator, Optional
import numpy as np
import time
import logging
import datetime

_logger = logging.getLogger("input")


def rate_limited_loop(fps: float) -> Iterator[float]:
    """Rate limited loop."""

    def _busy_wait_until(tend: float):
        while tend - time.perf_counter() > 0.0:
            pass

    td = 1 / fps
    t_start = time.perf_counter()
    t_next = t_start + td
    rate_failed_emitted = False
    while True:
        t_cur = time.perf_counter() - t_start
        yield t_cur
        remain = max(t_next - time.perf_counter(), 0)
        if remain > 0.1:
            time.sleep(remain)
        elif remain > 0.0:
            _busy_wait_until(t_next)
        elif remain < 0.0 and not rate_failed_emitted:
            rate_failed_emitted = True
            _logger.warning(f"Too slow at {t_cur}")
        t_next += td


@dataclasses.dataclass
class Event:
    at: float
    until: float
    name: str

    @staticmethod
    def create_random(lambd: float = 20.0, dur: float = 2.0):
        event_at = time.time() + np.random.exponential(scale=20)
        event_name = datetime.datetime.fromtimestamp(event_at).strftime("%H:%M:%S")
        event_until = event_at + 2.0
        return Event(event_at, event_until, f"Event at {event_name}")


def chessboard_generator(
    shape: tuple[int, int],
    roll: int,
    block_size: int = 100,
    fps: Optional[int] = 10000,
    noise_std: float = 0.0,
) -> Iterator[tuple[float, np.ndarray, bool]]:
    """Generates rolling chessboard images.

    Returns:
        timestamp: timestamp relative to start of generator [sec]
        image: rgb24 image
        ev: true if an event is currently active, false otherwise
    """

    num_blocks = (
        int(np.ceil(shape[0] / block_size)),
        int(np.ceil(shape[1] / block_size)),
    )
    check = np.zeros(num_blocks)
    check[1::2, ::2] = 1
    check[::2, 1::2] = 1

    img = np.expand_dims(np.kron(check, np.ones((block_size, block_size))), -1)
    img = np.tile(img, (1, 1, 3))
    img += np.random.randn(*img.shape) * noise_std
    img = np.clip(img, 0.0, 1.0).astype(np.uint8) * 255
    img = img[: shape[0], : shape[1]]

    ev = Event.create_random(lambd=10, dur=2)
    ev_active = False

    total_roll = 0
    for ts in rate_limited_loop(fps=fps):
        t_cur = time.time()
        if t_cur > ev.until:
            ev = Event.create_random(lambd=10, dur=2)
            img[:block_size, :block_size] = (0, 0, 0)
            ev_active = False
        elif t_cur > ev.at:
            img[:block_size, :block_size] = (0, 255, 255)
            ev_active = True
        rolled = np.roll(img, total_roll, 1)
        yield ts, rolled, ev_active
        total_roll += roll


def test_chessboard_gen():
    import matplotlib.pyplot as plt

    shape = (200, 320)
    fps = 30
    roll_over = 5  # roll over in 5 secs
    roll = int(np.ceil(shape[1] / (roll_over * fps)))
    gen = chessboard_generator(shape, roll=roll, block_size=20, fps=fps)

    fig, ax = plt.subplots()
    img_ = ax.imshow(next(gen)[1])
    prev_ev = False
    while True:
        plt.pause(1e-5)
        ts, img, ev = next(gen)
        img_.set_data(img)
        if not prev_ev and ev:
            print("now")
        prev_ev = ev


if __name__ == "__main__":
    test_chessboard_gen()
