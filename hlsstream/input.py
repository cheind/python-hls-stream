from distutils.log import warn
from typing import Iterator, Optional
import numpy as np
import time
import logging

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


def chessboard_generator(
    shape: tuple[int, int],
    roll: int,
    block_size: int = 100,
    fps: Optional[int] = 10000,
    noise_std: float = 0.0,
) -> Iterator[np.ndarray]:
    """Generates rolling chessboard images."""

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

    img[:, :block_size] = (0, 255, 255)
    img = img[: shape[0], : shape[1]]

    total_roll = 0
    for ts in rate_limited_loop(fps=fps):
        rolled = np.roll(img, total_roll, 1)
        yield ts, rolled
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
    while True:
        plt.pause(1e-5)
        img_.set_data(next(gen)[1])


if __name__ == "__main__":
    test_chessboard_gen()
