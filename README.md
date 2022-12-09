## Text correction benchmarks

This repository contains benchmarks for text correction tasks such as
- Whitespace correction
- Spelling error correction
- Word-level spelling error detection
- Sequence-level spelling error detection
in the following simple text file format:
- Whitespace correction
  - corrupt.txt: Input text with whitespace errors (can also contains spelling errors, but they remain uncorrected in the groundtruth)
  - correct.txt: Groundtruth text without whitespace errors
  > Example: "Th isis a tset." > "This is a tset."
- Spelling error correction
  - corrupt.txt: Input text with spelling errors (can also contain whitespace errors to make the task harder)
  - correct.txt: Groundtruth text without whitespace and spelling errors
  > Example: "Th isis a tset." > "This is a test." 
- Word-level spelling error detection:
  - corrupt.txt: Input text with spelling errors (should not contain whitespace errors, since we assume they are already fixed)
  - correct.txt: Groundtruth label for each word in the input (split by whitespace), indicating whether a word contains a spelling error (1)
  or not (0)
  > Example: "This is a tset." > "0 0 0 1"
- Sequence-level spelling error detection:
  - corrupt.txt: Input text with spelling errors (can also contain whitespace errors)
  - correct.txt: Groundtruth label for each sequence in the input, indicating whether the sequence contains a spelling error (1) or not (0)
  > Example: "this is a tset." > "1"

For each format one line corresponds to one benchmark sample.

This repository also contains scripts for evaluating predictions on the benchmarks.
The following procedure is recommended:
1. Run your model on corrupt.txt 
2. Save your predictions in the expected format for the benchmark as <model_name>.txt
3. Evaluate your predictions against a groundtruth using [evaluate.py](evaluate.py):
   > python evaluate.py corrupt.txt correct.txt <model_name>.txt --task <task> <--additional-args>

Depending on the task the following metrics are calculated:
- Whitespace correction
  - F1 (micro-averaged)
  - F1 (sequence-averaged)
  - Sequence accuracy
- Spelling error correction
  - F1 (micro-averaged)
  - F1 (sequence-averaged)
  - Sequence accuracy
- Word-level spelling error detection
  - Word accuracy
  - Binary F1 (micro-averaged)
- Sequence-level spelling error detection
  - Binary F1
  - Sequence accuracy

We already provide predictions for some baselines (see [baselines](baselines)).

This repository is backed by the [text-correction-utils](https://github.com/bastiscode/text-correction-utils) package.
