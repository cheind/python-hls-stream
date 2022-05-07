from typing import Iterator, Optional
import numpy as np
import time


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
    last_time = time.perf_counter()
    while True:
        rolled = np.roll(img, total_roll, 1)
        sleep_for = last_time + 1 / fps - time.perf_counter()
        if sleep_for > 0:
            time.sleep(sleep_for)
        yield rolled
        last_time = time.perf_counter()
        total_roll += roll


def test_chessboard_gen():
    import matplotlib.pyplot as plt

    shape = (1080, 1920)
    fps = 30
    roll_over = 5  # roll over in 5 secs
    roll = int(np.ceil(shape[1] / (roll_over * fps)))
    gen = chessboard_generator(shape, roll=roll, block_size=120)

    fig, ax = plt.subplots()
    img_ = ax.imshow(next(gen))
    while True:
        plt.pause(1 / fps)
        img_.set_data(next(gen))


if __name__ == "__main__":
    test_chessboard_gen()
