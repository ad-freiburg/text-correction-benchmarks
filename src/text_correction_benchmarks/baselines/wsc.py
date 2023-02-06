from typing import Iterable, Any, Optional
from text_correction_benchmarks.baselines import Baseline


class Dummy(Baseline):
    def run(
        self,
        sequences: Iterable[str],
        **_: Any
    ) -> Iterable[str]:
        yield from sequences

    @property
    def name(self) -> str:
        return "Dummy"


class Wordsegment(Baseline):
    def __init__(self, seed: Optional[int] = None):
        super().__init__(seed)
        from wordsegment import load
        load()

    def run(
        self,
        sequences: Iterable[str],
        **_: Any
    ) -> Iterable[str]:
        from wordsegment import segment
        for sequence in sequences:
            yield " ".join(segment("".join(sequence.split())))

    @property
    def name(self) -> str:
        return "Wordsegment"
