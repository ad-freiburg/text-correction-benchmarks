from typing import Iterable, Any

from text_correction_utils import dictionary as dct
from text_correction_benchmarks.baselines import Baseline


class Dummy(Baseline):
    def run(self, sequences: Iterable[str], **_: Any) -> Iterable[str]:
        for _s in sequences:
            yield "0"

    @property
    def name(self) -> str:
        return "Dummy"


class OutOfDictionary(Baseline):
    def __init__(self, dictionary: str):
        self.d = dct.Dictionary.load(dictionary)

    def run(self, sequences: Iterable[str], **_: Any) -> Iterable[str]:
        for s in sequences:
            yield "0" if all(self.d.contains(w) for w in s.split()) else "1"

    @property
    def name(self) -> str:
        return "OutOfDictionary"
