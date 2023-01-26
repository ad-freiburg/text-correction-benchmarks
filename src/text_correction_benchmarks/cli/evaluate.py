import argparse
import os
from typing import Set, Union, List, Tuple

from text_correction_utils import metrics
from text_correction_utils.io import load_text_file
from text_correction_utils.api import table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        "Evaluation script for most common text correction tasks."
    )
    parser.add_argument(
        "benchmark",
        type=str,
        help="Path to the benchmark directory containing input and groundtruth files."
    )
    prediction_group = parser.add_mutually_exclusive_group(required=False)
    prediction_group.add_argument(
        "-f",
        "--files",
        type=str,
        default=None,
        nargs="+",
        help="Paths to the prediction files as outputted by text correction models."
    )
    prediction_group.add_argument(
        "-d",
        "--dir",
        type=str,
        default=None,
        help="Path to a directory containing prediction files as outputted by text correction models."
    )
    parser.add_argument(
        "--sort",
        type=str,
        default=None,
        help="Sort evaluations by the given metric. If not specified, "
        "the order is equal to the order in which the predictions were given."
    )
    lowercase_group = parser.add_argument_group()
    lowercase_group.add_argument(
        "--lowercase",
        action="store_true",
        help="Whether to lowercase the model predictions before evaluation. Useful "
             "for spelling correction benchmarks that have lowercased inputs and groundtruths, "
             "such as bea322/bea4660."
    )
    lowercase_group.add_argument(
        "--lowercase-file",
        type=str,
        default=None,
        help="Path to a file containing a 0 or 1 for each line in the benchmark, indicating whether the corresponding "
             "predictions should be lowercased or not. Useful e.g. when evaluating on the neuspell "
             "benchmark because half of its sequences are from bea322/bea4660 and they have lowercased inputs "
             "and groundtruths."
    )
    return parser.parse_args()


def evaluate(
    corrupted_file: str,
    groundtruth_file: str,
    predicted_file: str,
    metric_names: Set[str],
    lowercase: Union[bool, str]
) -> List[Tuple[str, str, float, bool]]:
    groundtruths = load_text_file(groundtruth_file)
    predictions = load_text_file(predicted_file)
    corrupted = load_text_file(corrupted_file)
    if isinstance(lowercase, str):
        lowercase_lines = [
            bool(int(lower))
            for lower in load_text_file(lowercase)
        ]
    elif isinstance(lowercase, bool):
        lowercase_lines = [
            bool(int(lowercase))
            for _ in range(len(predictions))
        ]
    else:
        raise TypeError(
            f"expected lowercase to be a string or a bool, but got {type(lowercase)}")

    assert len(predictions) == len(groundtruths) == len(corrupted) == len(lowercase_lines), \
        "expected the same number of lines in the groundtruth, prediction, corrupted, and lowercase files"

    predictions = [
        p.lower() if lower else p
        for p, lower in zip(predictions, lowercase_lines)
    ]

    outputs = []

    for name in sorted(metric_names):
        if name == "bin_f1":
            binary_predictions = [
                bool(int(p))
                for prediction in predictions
                for p in prediction.split()
            ]
            binary_labels = [
                bool(int(lab))
                for label in groundtruths
                for lab in label.split()
            ]
            f1, _, _ = metrics.binary_f1(
                binary_predictions, binary_labels
            )
            outputs.append(("F1", f"{100 * f1:.2f}", f1, True))

        elif name == "word_acc":
            word_predictions = [
                p
                for prediction in predictions
                for p in prediction.split()
            ]
            word_groundtruths = [
                lab
                for label in groundtruths
                for lab in label.split()
            ]

            accuracy = metrics.accuracy(word_predictions, word_groundtruths)
            outputs.append(
                ("Word accuracy", f"{accuracy * 100:.2f}", accuracy, True)
            )

        elif name == "seq_acc":
            accuracy = metrics.accuracy(predictions, groundtruths)
            outputs.append(
                ("Sequence accuracy", f"{accuracy * 100:.2f}", accuracy, True)
            )

        elif name == "mned":
            mned = metrics.mean_normalized_sequence_edit_distance(
                predictions, groundtruths
            )
            outputs.append(("MNED", f"{mned:.4f}", mned, False))

        elif name == "sec_f1":
            for seq_avg in [False, True]:
                f1, _, _ = metrics.spelling_correction_f1(
                    corrupted,
                    predictions,
                    groundtruths,
                    sequence_averaged=seq_avg
                )
                prefix = "Sequence-averaged" if seq_avg else "Micro"
                outputs.append((f"{prefix} F1", f"{f1 * 100:.2f}", f1, True))

        elif name == "wsc_f1":
            for seq_avg in [False, True]:
                f1, _, _ = metrics.whitespace_correction_f1(
                    corrupted,
                    predictions,
                    groundtruths,
                    sequence_averaged=seq_avg
                )
                prefix = "Sequence-averaged" if seq_avg else "Micro"
                outputs.append((f"{prefix} F1", f"{f1 * 100:.2f}", f1, True))

        else:
            raise RuntimeError(f"unknown metric {name}")

    return outputs


def run(args: argparse.Namespace) -> None:
    split = os.path.abspath(args.benchmark).rstrip("/").split("/")
    if len(split) < 2:
        raise RuntimeError(
            f"expected the benchmark directory to have at least one parent directory specifying "
            f"the task, but got {split}"
        )
    benchmark_type = split[-2]
    benchmark_name = split[-1]

    if benchmark_type == "seds":
        task_name = "Sequence-level spelling error detection"
        metric_names = {"bin_f1", "seq_acc"}
    elif benchmark_type == "sedw":
        task_name = "Word-level spelling error detection"
        metric_names = {"bin_f1", "word_acc"}
    elif benchmark_type == "sec":
        task_name = "Spelling error correction"
        metric_names = {"sec_f1", "mned"}
    elif benchmark_type == "wsc":
        task_name = "Whitespace correction"
        metric_names = {"wsc_f1", "seq_acc"}
    else:
        raise RuntimeError(
            f"unknonw benchmark type {benchmark_type}, make sure your directory "
            f"structure has the correct format"
        )

    if args.files is not None:
        predictions = args.files
    elif args.dir is not None:
        predictions = [
            os.path.join(args.dir, file)
            for file in os.listdir(args.dir)
        ]
    else:
        prediction_dir = os.path.join(args.benchmark, "predictions")
        assert os.path.exists(prediction_dir) and os.path.isdir(prediction_dir), \
            f"expecting a subdirectory 'predictions' in {args.benchmark} if neither --files/-f nor --dir/-d is specified"
        predictions = [
            os.path.join(prediction_dir, file)
            for file in os.listdir(prediction_dir)
        ]

    assert len(predictions) > 0, "need to have at least one prediction file"

    in_file = os.path.join(args.benchmark, "corrupt.txt")
    gt_file = os.path.join(args.benchmark, "correct.txt")
    try:
        evaluations = []
        for pred_file in predictions:
            evaluation = evaluate(
                corrupted_file=in_file,
                groundtruth_file=gt_file,
                predicted_file=pred_file,
                metric_names=metric_names,
                # lowercase only respected for sec benchmarks
                lowercase=args.lowercase and args.benchmark_type == "sec"
            )
            pred_name, _ = os.path.splitext(os.path.split(pred_file)[-1])
            evaluations.append((pred_name, evaluation))
    except Exception as e:
        raise RuntimeError(
            f"encountered exception during evaluation: '{e}'.\n"
        )

    # generate nicely formatted output table for evaluations
    metric_headers = [name for name, *_ in evaluations[0][1]]
    if args.sort is not None:
        assert args.sort in metric_headers, \
            f"sort must be a metric name in {metric_headers}, but got '{args.sort}'"
        sort_idx = metric_headers.index(args.sort)
        larger_is_better = [larger for *_, larger in evaluations[0][1]]
        evaluations = sorted(
            evaluations, key=lambda e: e[1][sort_idx][2], reverse=larger_is_better[sort_idx]
        )
    data = [
        [name] + [formatted_value for _, formatted_value, _, _ in evaluation]
        for (name, evaluation) in evaluations
    ]
    output_table = table.generate_table(
        headers=[
            [task_name] + [""] * len(metric_headers),
            [benchmark_name] + metric_headers
        ],
        data=data,
        alignments=["left"] + ["right"] * len(metric_headers)
    )
    print(output_table)


def main():
    run(parse_args())


if __name__ == "__main__":
    main()
