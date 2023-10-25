import argparse
import os
from typing import List, Tuple, Optional

from text_utils import metrics as M
from text_utils.io import load_text_file
from text_utils.api import table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        "Evaluation script for most common text correction tasks."
    )
    parser.add_argument(
        "-b",
        "--benchmarks",
        type=str,
        nargs="+",
        help="Paths to the benchmark directories containing input and groundtruth files."
    )
    parser.add_argument(
        "-m",
        "--metric",
        type=str,
        default=None,
        help="Name of the metric to evaluate. Only necessary if multiple benchmarks are specified. "
        "On a single benchmark, all M are evaluated."
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
    parser.add_argument(
        "--highlight",
        action="store_true",
        help="Highlights the best predictions per benchmark or per metric in yellow."
    )
    parser.add_argument(
        "--disallow-subset",
        action="store_true",
        help="Whether to allow the predictions to be a subset of the groundtruths (have fewer lines). Allowed by default."
    )
    return parser.parse_args()


def evaluate(
    corrupted_file: str,
    groundtruth_file: str,
    predicted_file: str,
    metrics: List[str],
    lowercase_file: Optional[str],
    disallow_subset: bool
) -> List[Tuple[str, str, float]]:
    groundtruths = load_text_file(groundtruth_file)
    corrupted = load_text_file(corrupted_file)
    assert len(groundtruths) == len(corrupted), \
        f"expected the same number of lines in the groundtruth and corrupted files, " \
        f"but got {len(groundtruths)} and {len(corrupted)}"

    predictions = load_text_file(predicted_file)
    if lowercase_file is not None:
        lowercase_lines = [
            bool(int(lower))
            for lower in load_text_file(lowercase_file)
        ]
    else:
        lowercase_lines = [False] * len(predictions)

    if disallow_subset:
        assert len(predictions) == len(groundtruths) and len(predictions) == len(lowercase_lines), \
            "expected the same number of lines in groundtruth, prediction, and lowercase files, " \
            f"but got {len(groundtruths)}, {len(predictions)}, and {len(lowercase_lines)}"
    else:
        groundtruths = groundtruths[:len(predictions)]
        corrupted = corrupted[:len(predictions)]
        lowercase_lines = lowercase_lines[:len(predictions)]

    predictions = [
        p.lower() if lower else p
        for p, lower in zip(predictions, lowercase_lines)
    ]

    outputs = []

    for metric in metrics:
        metric_name = _METRIC_TO_NAME[metric]
        if metric == "bin_f1":
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
            f1, _, _ = M.binary_f1(
                binary_predictions, binary_labels
            )
            outputs.append((metric_name, f"{100 * f1:.2f}", f1))

        elif metric == "word_acc":
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

            accuracy = M.accuracy(word_predictions, word_groundtruths)
            outputs.append(
                (metric_name, f"{accuracy * 100:.2f}", accuracy)
            )

        elif metric == "seq_acc":
            accuracy = M.accuracy(predictions, groundtruths)
            outputs.append(
                (metric_name, f"{accuracy * 100:.2f}", accuracy)
            )

        elif metric == "mned":
            mned = M.mean_normalized_edit_distance(
                predictions, groundtruths
            )
            outputs.append((mned, f"{mned:.4f}", mned))

        elif metric == "sec_f1_micro" or metric == "sec_f1_seq":
            (f1, _, _), _ = M.spelling_correction_f1(
                corrupted,
                predictions,
                groundtruths,
                sequence_averaged=metric == "sec_f1_seq"
            )
            outputs.append((metric_name, f"{f1 * 100:.2f}", f1))

        elif metric == "wsc_f1_micro" or metric == "wsc_f1_seq":
            (f1, _, _), _ = M.whitespace_correction_f1(
                corrupted,
                predictions,
                groundtruths,
                sequence_averaged=metric == "wsc_f1_seq"
            )
            outputs.append((metric_name, f"{f1 * 100:.2f}", f1))

        else:
            raise RuntimeError(f"unknown metric {metric}")

    return outputs


def parse_benchmark(benchmark: str) -> Optional[Tuple[str, str, str]]:
    if not os.path.exists(benchmark) or os.path.isfile(benchmark):
        return None
    split = os.path.abspath(benchmark).rstrip("/").split("/")
    if len(split) < 2:
        raise RuntimeError(
            f"expected the benchmark directory {benchmark} to have at least one "
            f"parent directory specifying the task, but got {split}"
        )
    task = split[-2]
    benchmark_name = split[-1]
    return benchmark, task, benchmark_name


_METRIC_TO_NAME = {
    "bin_f1": "F1",
    "seq_acc": "Sequence accuracy",
    "word_acc": "Word accuracy",
    "mned": "MNED",
    "sec_f1_micro": "Micro F1",
    "sec_f1_seq": "Sequence-averaged F1",
    "wsc_f1_micro": "Micro F1",
    "wsc_f1_seq": "Sequence-averaged F1",
}

_LARGER_IS_BETTER = {
    "bin_f1": True,
    "seq_acc": True,
    "word_acc": True,
    "mned": False,
    "sec_f1_micro": True,
    "sec_f1_seq": True,
    "wsc_f1_micro": True,
    "wsc_f1_seq": True,
}

_TASK_TO_NAME = {
    "seds": "Sequence-level spelling error detection",
    "sedw": "Word-level spelling error detection",
    "sec": "Spelling error correction",
    "wsc": "Whitespace correction",
}


def metrics_from_task(task: str) -> List[str]:
    if task == "seds":
        return ["bin_f1", "seq_acc"]
    elif task == "sedw":
        return ["bin_f1", "word_acc"]
    elif task == "sec":
        return ["sec_f1_micro", "sec_f1_seq", "mned"]
    elif task == "wsc":
        return ["wsc_f1_micro", "wsc_f1_seq", "seq_acc"]
    else:
        raise RuntimeError(f"unknown task {task}")


def list_dir(path: str) -> List[str]:
    return [
        os.path.join(path, file)
        for file in os.listdir(path)
        if os.path.isfile(os.path.join(path, file))
    ]


def run(args: argparse.Namespace) -> None:
    benchmarks = []
    for benchmark in args.benchmarks:
        parsed_benchmark = parse_benchmark(benchmark)
        if parsed_benchmark is not None:
            benchmarks.append(parsed_benchmark)

    if len(benchmarks) == 0:
        raise RuntimeError("no valid benchmarks specified")

    elif len(benchmarks) == 1:
        benchmark, task, benchmark_name = benchmarks[0]
        metrics = metrics_from_task(task)
        task_name = _TASK_TO_NAME[task]
        metric_names = [_METRIC_TO_NAME[metric] for metric in metrics]

        if args.files is not None:
            predictions = args.files
        elif args.dir is not None:
            predictions = [
                os.path.join(args.dir, file)
                for file in os.listdir(args.dir)
            ]
        else:
            prediction_dir = os.path.join(benchmark, "predictions")
            assert os.path.exists(prediction_dir) and os.path.isdir(prediction_dir), \
                f"expecting a subdirectory 'predictions' in {benchmark} if neither --files/-f nor --dir/-d is specified"
            predictions = list_dir(prediction_dir)

        benchmark_predictions = [predictions]

    else:
        assert all(task == benchmarks[0][1] for _, task, _ in benchmarks), \
            "all benchmarks must be for the same task if multiple benchmarks are specified"
        _, task, _ = benchmarks[0]
        metrics = metrics_from_task(task)
        task_name = _TASK_TO_NAME[task]
        assert args.metric is not None, \
            "need to specify --metric/-m if multiple benchmarks are specified"
        metric_names = [_METRIC_TO_NAME[metric] for metric in metrics]
        assert args.metric in metric_names, \
            f"metric {args.metric} not available for task {task_name}, must be one of {metric_names}"
        metric_idx = metric_names.index(args.metric)
        metrics = [metrics[metric_idx]]
        metric_names = [args.metric]

        benchmark_predictions = []
        for benchmark, *_ in benchmarks:
            prediction_dir = os.path.join(benchmark, "predictions")
            assert os.path.exists(prediction_dir) and os.path.isdir(prediction_dir), \
                f"expecting a subdirectory 'predictions' in each benchmark directory when " \
                f"evaluating on multiple benchmarks, but got none in {benchmark}"
            predictions = list_dir(prediction_dir)
            benchmark_predictions.append(predictions)

    if all(len(predictions) == 0 for predictions in benchmark_predictions):
        raise RuntimeError("no benchmark predictions")

    try:
        benchmark_evaluations = []
        for (benchmark, *_), predictions in zip(benchmarks, benchmark_predictions):
            in_file = os.path.join(benchmark, "corrupt.txt")
            gt_file = os.path.join(benchmark, "correct.txt")
            lc_file = os.path.join(benchmark, "lowercase.txt")
            evaluations = []
            for pred_file in predictions:
                evaluation = evaluate(
                    corrupted_file=in_file,
                    groundtruth_file=gt_file,
                    predicted_file=pred_file,
                    metrics=metrics,
                    # lowercase only respected for sec benchmarks
                    lowercase_file=lc_file if os.path.exists(
                        lc_file
                    ) and task == "sec" else None,
                    disallow_subset=args.disallow_subset
                )
                pred_name, _ = os.path.splitext(os.path.split(pred_file)[-1])
                evaluations.append((pred_name, evaluation))
            benchmark_evaluations.append(evaluations)

    except Exception as e:
        raise RuntimeError(
            f"encountered exception during evaluation: '{e}'.\n"
        )

    # generate nicely formatted output table for evaluations
    if len(benchmark_evaluations) == 1:
        evaluations = benchmark_evaluations[0]
        _, _, benchmark_name = benchmarks[0]
        if args.sort is not None:
            assert args.sort in metric_names, \
                f"sort must be a metric name in {metric_names}, but got '{args.sort}'"
            sort_idx = metric_names.index(args.sort)
            larger_is_better = _LARGER_IS_BETTER[metrics[sort_idx]]
            evaluations = sorted(
                evaluations, key=lambda e: e[1][sort_idx][2], reverse=larger_is_better
            )
        data = [
            [name] + [formatted_value for _, formatted_value, *_ in evaluation]
            for (name, evaluation) in evaluations
        ]
        if args.highlight:
            highlight = set()
            for i in range(len(metric_names)):
                larger_is_better = _LARGER_IS_BETTER[metrics[i]]
                indices_and_scores = [
                    (j, evaluation[i][2])
                    for j, (_, evaluation) in enumerate(evaluations)
                ]
                best_idx, _ = sorted(
                    indices_and_scores,
                    key=lambda e: e[1], reverse=larger_is_better
                )[0]
                highlight.add((best_idx, i + 1))
        else:
            highlight = None

        output_table = table.generate_table(
            headers=[
                [task_name] + [""] * len(metric_names),
                [benchmark_name] + metric_names
            ],
            data=data,
            highlight=highlight,
            highlight_type="terminal",
            highlight_color="yellow",
            alignments=["left"] + ["right"] * len(metric_names)
        )

    else:
        assert len(metric_names) == 1
        larger_is_better = _LARGER_IS_BETTER[metrics[0]]
        model_names = set()
        data_dict = {}
        for (*_, benchmark_name), evaluations in zip(benchmarks, benchmark_evaluations):
            if benchmark_name not in data_dict:
                data_dict[benchmark_name] = {}
            for (name, evaluation) in evaluations:
                assert len(evaluation) == 1
                data_dict[benchmark_name][name] = evaluation[0]
                model_names.add(name)
        model_names = sorted(model_names)
        data = [
            [name] + [
                "-" if name not in data_dict[benchmark_name]
                else data_dict[benchmark_name][name][1]
                for *_, benchmark_name in benchmarks
            ]
            for name in model_names
        ]
        if args.highlight:
            highlight = set()
            missing_score = float("-inf") if larger_is_better else float("inf")
            for i in range(len(benchmarks)):
                benchmark_name = benchmarks[i][2]
                indices_and_scores = [(
                    j,
                    data_dict[benchmark_name][model_name][2]
                    if model_name in data_dict[benchmark_name] else missing_score
                )
                    for j, model_name in enumerate(model_names)
                ]
                best_idx, _ = sorted(
                    indices_and_scores,
                    key=lambda e: e[1], reverse=larger_is_better
                )[0]
                highlight.add((best_idx, i + 1))
        else:
            highlight = None

        output_table = table.generate_table(
            headers=[
                [task_name] + [""] * len(benchmarks),
                metric_names + [
                    benchmark_name
                    for *_, benchmark_name in benchmarks
                ]
            ],
            data=data,
            highlight=highlight,
            highlight_type="terminal",
            highlight_color="yellow",
            alignments=["left"] + ["right"] * len(benchmark_evaluations)
        )

    print(output_table)


def main():
    run(parse_args())


if __name__ == "__main__":
    main()
