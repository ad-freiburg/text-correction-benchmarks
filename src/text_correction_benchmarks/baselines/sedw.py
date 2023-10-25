from typing import Iterable, Any

from text_utils import dictionary as dct
from text_correction_benchmarks.baselines import Baseline


class Dummy(Baseline):
    def run(self, sequences: Iterable[str], **_: Any) -> Iterable[str]:
        for s in sequences:
            yield " ".join(["0"] * len(s.split(" ")))

    @property
    def name(self) -> str:
        return "Dummy"


class OutOfDictionary(Baseline):
    def __init__(self, dictionary: str):
        self.d = dct.Dictionary.load(dictionary)

    def run(self, sequences: Iterable[str], **_: Any) -> Iterable[str]:
        for s in sequences:
            predictions = []
            for w in s.split():
                if self.d.contains(w):
                    predictions.append("0")
                else:
                    predictions.append("1")
            yield " ".join(predictions)

    @property
    def name(self) -> str:
        return "OutOfDictionary"
