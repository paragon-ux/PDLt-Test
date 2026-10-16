"""L124 D3: the core invariants hold whatever an extension does (run from the b2 worktree root)."""
from pathlib import Path


def edit(path, pairs, count=1):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        assert s.count(old) == count, (path, old[:90], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")


ENGINE = "src/pdl_taskmaster/runtime/session_engine.py"
edit(ENGINE, [
    # The session's verifier registry is built from the registered verifiers (verifier profile v1).
    ("        from pdl_taskmaster.verification.output_verifier import OutputVerifier\n\n"
     "        self.output_verifier = OutputVerifier()\n",
     "        from pdl_taskmaster.extensions import verifiers\n\n"
     "        self.output_verifier = verifiers.output_verifier()\n"),
    ("                verdict = verifier.check(sandbox_witness, constraints, domain=self._problem_domain, body=body)\n",
     "                verdict = self._check_witness(verifier, sandbox_witness, constraints, body)\n"),
    ("                verdict = verifier.check(model_witness, constraints, domain=self._problem_domain, body=body)\n",
     "                verdict = self._check_witness(verifier, model_witness, constraints, body)\n"),
    ("    def _verify_result(\n",
     '''    def _check_witness(self, verifier: Any, witness: Any, constraints: dict[str, Any], body: str) -> Any:
        """A checker judges a copy of the witness and of its constraints (L124): it cannot change what the host
        records. A checker that raises, or answers with anything but a VerificationVerdict, stops the turn: no result
        is published on it (fail-closed)."""
        import copy

        from pdl_taskmaster.extensions.profiles import ExtensionFailure
        from pdl_taskmaster.verification.checkers.base import VerificationVerdict

        try:
            verdict = verifier.check(copy.deepcopy(witness), copy.deepcopy(constraints), domain=self._problem_domain,
                                     body=body)
        except Exception as exc:
            raise ExtensionFailure(f"the checker for this witness failed ({type(exc).__name__}: {exc}); "
                                   "no result is published") from exc
        if not isinstance(verdict, VerificationVerdict):
            raise ExtensionFailure(f"the checker for this witness answered {type(verdict).__name__}, not a "
                                   "VerificationVerdict; no result is published")
        return verdict

    def _verify_result(\n'''),
])
edit("src/pdl_taskmaster/extensions/profiles.py", [
    ('''class Registry(Generic[T]):''',
     '''class ExtensionFailure(RuntimeError):
    """An extension failed while the core used it. The core stops what it was doing; it never passes on a failure."""


class Registry(Generic[T]):'''),
])
print("ok")
