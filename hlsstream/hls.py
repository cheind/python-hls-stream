from typing import Iterator
from pathlib import Path
import ffmpeg
import numpy as np


def chessboard_generator(
    shape: tuple[int, int], roll: int, block_size: int
) -> Iterator[np.ndarray]:

    num_blocks = (
        int(np.ceil(shape[0] / block_size)),
        int(np.ceil(shape[1] / block_size)),
    )
    check = np.zeros(num_blocks)
    check[1::2, ::2] = 1
    check[::2, 1::2] = 1

    img = np.expand_dims(np.kron(check, np.ones((block_size, block_size))), -1)
    img = np.tile(img, (1, 1, 3))
    # img += np.random.randn(*img.shape) * 1e-2
    img = np.clip(img, 0.0, 1.0).astype(np.uint8) * 255

    img[:, :block_size] = (0, 255, 255)
    img = img[: shape[0], : shape[1]]
    print(img.shape)

    while True:
        yield img
        img = np.roll(img, roll, 1)


def hls_stream(
    outdir: Path,
    prefix: str,
    shape: tuple[int, int] = (1080, 1920),
    fps: int = 20,
    hls_segment_duration=5,
):
    height, width = shape

    proc = (
        ffmpeg.input(
            "pipe:",
            format="rawvideo",
            pix_fmt="rgb24",
            s="{}x{}".format(width, height),
            framerate=fps,
        )
        .output(
            str(Path(outdir) / f"{prefix}.m3u8"),
            format="hls",
            start_number=0,
            hls_time=hls_segment_duration,
            hls_list_size=100,
            pix_fmt="yuv420p",
            vcodec="libx264",  # no gpu support? libx264, else h264_nvenc
            preset="veryfast",  # ll for h264_nvenc https://gist.github.com/nico-lab/e1ba48c33bf2c7e1d9ffdd9c1b8d0493
            g=hls_segment_duration * fps,
            keyint_min=hls_segment_duration * fps,
            # video_bitrate="4M",  # 1Mbit/s, CBR, see below
            # maxrate="4M",
            # bufsize="5M",
        )
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )

    # Note, -g (GOP) and keyint_min is necessary to get exact duration segments.
    # https://sites.google.com/site/linuxencoding/x264-ffmpeg-mapping#:~:text=%2Dg%20(FFmpeg,Recommended%20default%3A%20250
    # For preset settings
    # https://obsproject.com/blog/streaming-with-x264#:~:text=x264%20has%20several%20CPU%20presets,%2C%20slower%2C%20veryslow%2C%20placebo.
    # See CBR
    # https://trac.ffmpeg.org/wiki/Encode/H.264

    roll = int(np.ceil(width / (5 * fps)))
    gen = chessboard_generator(shape, roll, 100)

    while True:
        proc.stdin.write(next(gen).tobytes())
    proc.stdin.close()


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
    hls_stream(
        "static/video", "chessboard", shape=(1080, 1920), fps=30, hls_segment_duration=5
    )
