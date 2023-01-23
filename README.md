# Text correction benchmarks

Benchmarks and baselines for various text correction tasks. Light-weight and 
easy to use.

### Installation

```
git clone https://github.com/bastiscode/text-correction-benchmarks
cd text-correction-benchmarks && pip install .
```

After installation you will have two command available to you:
- `tcb.evaluate` for evaluating model predictions on benchmarks
- `tcb.baseline` for running baselines on benchmarks

## Usage

This repository contains [benchmarks](benchmarks) for text correction tasks such as
- Whitespace correction (**wc**)
- Spelling error correction (**sec**)
- Word-level spelling error detection (**sedw**)
- Sequence-level spelling error detection (**seds**)

in the following simple text file format:
- Whitespace correction
  - *corrupt.txt*: Input text with whitespace errors (can also contains spelling errors, but they remain uncorrected in the groundtruth)
  - *correct.txt*: Groundtruth text without whitespace errors
  > "Th isis a tset." > "This is a tset."
- Spelling error correction
  - *corrupt.txt*: Input text with spelling errors (can also contain whitespace errors to make the task harder)
  - *correct.txt*: Groundtruth text without whitespace and spelling errors
  > "Th isis a tset." > "This is a test." 
- Word-level spelling error detection:
  - *corrupt.txt*: Input text with spelling errors (should not contain whitespace errors, since we assume they are already fixed)
  - *correct.txt*: Groundtruth label for each word in the input (split by whitespace), indicating whether a word contains a spelling error (1)
  or not (0)
  > "This is a tset." > "0 0 0 1"
- Sequence-level spelling error detection:
  - *corrupt.txt*: Input text with spelling errors (can also contain whitespace errors)
  - *correct.txt*: Groundtruth label for each sequence in the input, indicating whether the sequence contains a spelling error (1) or not (0)
  > "this is a tset." > "1"

For each format one line corresponds to one benchmark sample.

Note that for some benchmarks we also provide versions other than [*test*](benchmarks/test), e.g. 
[*dev*](benchmarks/dev) or [*tuning*](benchmarks/tuning), which can be used to assess performance 
of your method during developement. Final evaluations should always be done on the *test* split.

To evaluate predictions on a benchmark using `tcb.evaluate`,
the following procedure is recommended:
1. Run your model on `benchmarks/<split>/<task>/<benchmark>/corrupt.txt` 
2. Save your predictions in the expected format for the benchmark as `<model_name>.txt`
3. Evaluate your predictions on a benchmark using `tcb.evaluate`:
   ```bash
   # evaluate your predictions on the benchmark
   tcb.evaluate benchmarks/<split>/<task>/<benchmark> <model_name>.txt
   
   # You can also pass in as additional model predictions you want to compare to, 
   # the output is formatted as a markdown table:
   tcb.evaluate /benchmarks/<split>/<task>/<benchmark> <model_name>.txt <other_model>.txt ...
   ```

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

### Baselines

We also provide baselines for each task:
- Whitespace correction:
    - Dummy
- Spelling error correction:
    - Dummy
    - Close to dictionary (dictionaries can be found [here](dictionaries))
    - [Norvig](https://norvig.com/spell-correct.html)
    - [Aspell](http://aspell.net)
    - [Hunspell](https://hunspell.github.io)
    - [Jamspell](https://github.com/bakwc/JamSpell)
    - [Neuspell (BERT)](https://github.com/neuspell/neuspell)
- Word-level spelling error detection:
    - Dummy
    - Out of dictionary (dictionaries can be found [here](dictionaries))
    - From spelling error correction<sup>1</sup>
- Sequence-level spelling error detection:
    - Dummy
    - Out of dictionary (dictionaries can be found [here](dictionaries))
    - From spelling error correction<sup>1</sup>

The dummy baselines produce the predictions one gets by leaving the inputs unchanged.

<sup>1</sup> We can reuse spelling error correction baselines to detect spelling errors both on
a word and sequence level. For the word level we simply predict that all words changed
by a spelling corrector contain a spelling error. For the sequence level we
predict that a sequence contains a spelling error if it is changed by a spelling corrector.
All spelling error correction baselines can be used as underlying spelling correctors for this purpose.

You can run a baseline using `tcb.baseline`:
```bash
# run baseline on stdin and output to stdout
tcb.baseline <baseline>

# run baseline on file and output to stdout
tcb.baseline <baseline> -f <input_file>

# run baseline on file and write predictions to file
tcb.baseline <baseline> -f <input_file> -o <output_file>
```

We provide predictions for all of the baselines in [baselines](baselines).

---

This repository is backed by the [text-correction-utils](https://github.com/bastiscode/text-correction-utils) package.
