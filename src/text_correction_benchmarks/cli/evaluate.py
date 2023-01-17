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
        "benchmark_type",
        choices=[
            "seds",
            "sedw",
            "sec",
            "wc"
        ],
        help="The benchmark type determines the metrics that will be used to evaluate the given files."
    )
    parser.add_argument(
        "benchmark",
        type=str,
        help="Path to the benchmark directory containing input and groundtruth files."
    )
    parser.add_argument(
        "predictions",
        type=str,
        nargs="+",
        help="Paths to the prediction files as outputted by text correction models."
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
) -> List[Tuple[str, str]]:
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
            f1, prec, rec = metrics.binary_f1(
                binary_predictions, binary_labels
            )
            outputs.append(("F1", f"{100 * f1:.2f}"))

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
            outputs.append(("Word accuracy", f"{accuracy * 100:.2f}"))

        elif name == "seq_acc":
            accuracy = metrics.accuracy(predictions, groundtruths)
            outputs.append(("Sequence accuracy", f"{accuracy * 100:.2f}"))

        elif name == "mned":
            mned = metrics.mean_normalized_sequence_edit_distance(
                predictions, groundtruths
            )
            outputs.append(("MNED", f"{mned:.4f}"))

        elif name == "sec_f1":
            for seq_avg in [False, True]:
                (f1, prec, rec) = metrics.spelling_correction_f1(
                    corrupted,
                    predictions,
                    groundtruths,
                    sequence_averaged=seq_avg
                )
                prefix = "Sequence-averaged" if seq_avg else "Micro"
                outputs.append((f"{prefix} F1", f"{f1 * 100:.2f}"))

        elif name == "wc_f1":
            for seq_avg in [False, True]:
                (f1, prec, rec) = metrics.whitespace_correction_f1(
                    corrupted,
                    predictions,
                    groundtruths,
                    sequence_averaged=seq_avg
                )
                prefix = "Sequence-averaged" if seq_avg else "Micro"
                outputs.append((f"{prefix} F1", f"{f1 * 100:.2f}"))

        else:
            raise RuntimeError(f"unknown metric {name}")

    return outputs


def run(args: argparse.Namespace) -> None:
    if args.benchmark_type == "seds":
        benchmark_name = "Sequence-level spelling error detection"
        metric_names = {"bin_f1", "seq_acc"}
    elif args.benchmark_type == "sedw":
        benchmark_name = "Word-level spelling error detection"
        metric_names = {"bin_f1", "word_acc"}
    elif args.benchmark_type == "sec":
        benchmark_name = "Spelling error correction"
        metric_names = {"sec_f1", "mned"}
    elif args.benchmark_type == "wc":
        benchmark_name = "Whitespace correction"
        metric_names = {"wc_f1", "seq_acc"}
    else:
        raise RuntimeError("should not happen")
    assert len(args.predictions) > 0, "need to have at least one prediction file"

    in_file = os.path.join(args.benchmark, "corrupt.txt")
    gt_file = os.path.join(args.benchmark, "correct.txt")
    try:
        evaluations = []
        pred_names = []
        for pred_file in args.predictions:
            evaluations.append(evaluate(
                corrupted_file=in_file,
                groundtruth_file=gt_file,
                predicted_file=pred_file,
                metric_names=metric_names,
                # lowercase only respected for sec benchmarks
                lowercase=args.lowercase and args.benchmark_type == "sec"
            ))
            pred_name, _ = os.path.splitext(os.path.split(pred_file)[-1])
            pred_names.append(pred_name)
    except Exception as e:
        raise RuntimeError(
            f"encountered exception during evaluation: '{e}'.\n"
        )

    # generate nicely formatted output table for evaluations
    metric_headers = [name for name, _ in evaluations[0]]
    output_table = table.generate_table(
        headers=[[benchmark_name] + metric_headers],
        data=[
            [name] + [value for _, value in evaluation]
            for (name, evaluation) in zip(pred_names, evaluations)
        ],
        alignments=["left"] + ["right"] * len(metric_headers)
    )
    print(output_table)


def main():
    run(parse_args())


if __name__ == "__main__":
    main()
