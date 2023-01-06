from typing import Iterable, Dict, Any
from text_correction_benchmarks.baselines import Baseline


class Dummy(Baseline):
    def run(self, sequences: Iterable[str], **_: Dict[str, Any]) -> Iterable[str]:
        yield from sequences

    @property
    def name(self) -> str:
        return "Dummy"
