import argparse
import os
import tempfile

from text_correction_utils import api, logging

_BASE_URL = "https://ad-publications.informatik.uni-freiburg.de/" \
    "EMNLP_whitespace_correction_transformer_BHW_2022.materials"
_BENCHMARK_WITH_PREDICTIONS_URL = f"{_BASE_URL}/benchmarks_with_predictions.zip"
_BENCHMARK_URL = f"{_BASE_URL}/benchmarks.zip"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        "Benchmark downloader",
        "Downloads and extracts text correction benchmarks"
    )
    parser.add_argument(
        "-o",
        "--out",
        type=str,
        required=True,
        help="Output directory where benchmarks will be saved and extracted to"
    )
    parser.add_argument(
        "--no-predictions",
        action="store_true",
        help="Do not download predictions, but just the benchmarks"
    )
    return parser.parse_args()


def download(args: argparse.Namespace):
    logger = logging.get_logger("TEXT_CORRECTION_BENCHMARKS")
    if os.path.exists(args.out):
        logger.error(f"output directory {args.out} already exists")
        return

    if args.no_predictions:
        url = _BENCHMARK_URL
    else:
        url = _BENCHMARK_WITH_PREDICTIONS_URL

    with tempfile.TemporaryDirectory() as tmpdir:
        benchmark_dir = api.download_zip(
            "text correction benchmarks",
            url,
            tmpdir,
            args.out,
            ".",
            False,
            logger
        )

    logger.info(
        f"downloaded and extracted text correction benchmarks to {benchmark_dir}"
    )


def main():
    download(parse_args())


if __name__ == "__main__":
    main()
