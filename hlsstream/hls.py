from typing import Callable, Any
from pathlib import Path
import ffmpeg
import enum
import numpy as np
import time


class HLSPresets(enum.Enum):
    DEFAULT_CPU = {
        "vcodec": "libx264",
        "preset": "veryfast",
        "video_bitrate": "2M",
        "maxrate": "2M",
        "bufsize": "2M",
    }
    DEFAULT_GPU = {
        "vcodec": "h264_nvenc",
        "preset": "p3",  # https://gist.github.com/nico-lab/e1ba48c33bf2c7e1d9ffdd9c1b8d0493
        "tune": "ll",
        "video_bitrate": "2M",
        "maxrate": "2M",
        "bufsize": "2M",
    }


# For preset settings
# https://obsproject.com/blog/streaming-with-x264#:~:text=x264%20has%20several%20CPU%20presets,%2C%20slower%2C%20veryslow%2C%20placebo.


class HLSEncoder:
    def __init__(
        self,
        out_path: Path,
        shape: tuple[int, int] = (1080, 1920),
        input_fps: int = 30,
        use_wallclock_pts: bool = False,
        preset: HLSPresets = HLSPresets.DEFAULT_CPU,
        **hls_kwargs,
    ) -> None:
        self.out_path = out_path
        self.shape = shape

        self.inp_settings = {
            "format": "rawvideo",
            "pix_fmt": "rgb24",
            "s": "{}x{}".format(shape[1], shape[0]),
            "framerate": input_fps,
            "use_wallclock_as_timestamps": use_wallclock_pts,
        }
        self.enc_settings = {
            "format": "hls",
            "pix_fmt": "yuv420p",
            "hls_time": 5,
            "hls_list_size": 12,
            "hls_flags": "delete_segments",  # otherwise only m3u8 is updated correctly
            "start_number": 0,
            **preset.value,
            **hls_kwargs,
        }
        # Compute keyframe interval for most precise segment duration
        # Note, -g (GOP) and keyint_min is necessary to get exact duration segments.
        # https://sites.google.com/site/linuxencoding/x264-ffmpeg-mapping#:~:text=%2Dg%20(FFmpeg,Recommended%20default%3A%20250
        nkey = self.enc_settings["hls_time"] * self.inp_settings["framerate"]
        self.enc_settings["g"] = nkey
        self.enc_settings["keyint_min"] = nkey

        self.proc: Callable[[np.ndarray[np.uint8, Any]]] = None
        self.time: float = 0.0

    def __enter__(self) -> "HLSEncoder":
        self.time = 0.0
        self.proc = (
            ffmpeg.input("pipe:", **self.inp_settings)
            .output(str(self.out_path), **self.enc_settings)
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )
        return self

    def __exit__(self, type, value, traceback):
        self.proc.stdin.close()
        self.proc = None

    def __call__(self, rgb24: np.ndarray[np.uint8, Any]) -> float:
        if self.inp_settings["use_wallclock_as_timestamps"]:
            start_time = time.time()  # not very precise
        else:
            start_time = self.time
            self.time += 1 / self.inp_settings["framerate"]
        self.proc.stdin.write(rgb24.tobytes())
        return start_time


if __name__ == "__main__":

    from .input import chessboard_generator

    shape = (1080, 1920)
    fps = 30
    roll = int(np.ceil(shape[1] / (5 * fps)))
    gen = chessboard_generator(shape, roll, 100, fps=fps)
    enc = HLSEncoder(
        "static/video/chessboard.m3u8",
        shape=shape,
        input_fps=fps,
        use_wallclock_pts=False,
        preset=HLSPresets.DEFAULT_CPU,
    )

    with enc:
        while True:
            enc(next(gen))
