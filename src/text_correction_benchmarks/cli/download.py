import argparse
import os
import pprint

from text_correction_utils import api, logging

_BENCHMARK_URL = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_dir", type=str,
        help="Output directory where benchmarks will be saved and extracted to"
    )
    parser.add_argument(
        "-f",
        "--force-download",
        type=str,
        action="store_true",
        help="Force download of benchmarks, even if they were already downloaded"
    )
    return parser.parse_args()


def download(args: argparse.Namespace):
    logger = logging.get_logger("TEXT_CORRECTION_BENCHMARKS")
    os.makedirs(args.output_dir, exist_ok=True)
    download_dir = os.path.join(args.output_dir, ".download")
    os.makedirs(download_dir, exist_ok=True)
    benchmark_dir = api.download_zip(
        "text correction benchmarks",
        _BENCHMARK_URL,
        download_dir,
        args.output_dir,
        ".",
        args.force_download,
        logger
    )
    logger.info(
        f"downloaded and extracted text correction benchmarks to {benchmark_dir}:\n\
        {pprint.pformat(os.listdir(benchmark_dir))}"
    )


def main():
    download(parse_args())


if __name__ == "__main__":
    main()
