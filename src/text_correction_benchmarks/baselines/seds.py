from typing import Iterable, Dict, Any
from text_correction_benchmarks.baselines import Baseline


class Dummy(Baseline):
    def run(self, sequences: Iterable[str], **_: Dict[str, Any]) -> Iterable[str]:
        for _s in sequences:
            yield "0"

    @property
    def name(self) -> str:
        return "Dummy"
