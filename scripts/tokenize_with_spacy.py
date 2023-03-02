import argparse
import spacy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        type=str
    )
    parser.add_argument(
        "-o",
        "--out",
        required=True,
        type=str
    )
    return parser.parse_args()


def tokenize(args: argparse.Namespace):
    nlp = spacy.load("en_core_web_sm")
    with open(args.file, "r", encoding="utf8") as inf, \
            open(args.out, "w", encoding="utf8") as of:
        for line in inf:
            line = line.strip()
            split = " ".join(token.text for token in nlp(line))
            of.write(f"{split}\n")

    pass


if __name__ == "__main__":
    tokenize(parse_args())
