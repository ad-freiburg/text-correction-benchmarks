from typing import Iterable, Any
from text_correction_benchmarks.baselines import Baseline


class Dummy(Baseline):
    def run(self, sequences: Iterable[str], **_: Any) -> Iterable[str]:
        yield from sequences

    @property
    def name(self) -> str:
        return "Dummy"
