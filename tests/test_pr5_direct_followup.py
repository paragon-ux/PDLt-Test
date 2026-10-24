"""F4: a stateless direct worker receives only published history on referring follow-ups. Offline."""
import pytest

from pdl_taskmaster import api
from pdl_taskmaster.providers.base import WorkerResult

from test_api import ROOT
from test_l153_modes import DirectWorker, GatewaySys1


class FollowupSys1(GatewaySys1):
    follow_up = True

    def call(self, request):
        if next(iter(request.questions)) == "follow_up":
            choice = "FOLLOW_UP" if self.follow_up else "NEW_REQUEST"
            return {"answers": {"follow_up": {"choice": choice, "confidence": 0.99,
                                               "probabilities": {choice: 1.0}}}}, 1.0
        return super().call(request)


class StatelessWorker(DirectWorker):
    answer = "The generated identifier is violet-orbit-7392."

    def __init__(self):
        super().__init__()
        self.sys1_client = FollowupSys1()

    def call(self, request):
        if request.operation == "DIRECT_ANSWER":
            self.prompts.append(request.prompt)
            return WorkerResult(self.answer)
        return super().call(request)


@pytest.mark.parametrize("mode", ["direct", "saver"])
@pytest.mark.parametrize("reopen", [False, True])
def test_referring_followup_receives_published_answer_without_rewriting_user_source(tmp_path, mode, reopen):
    worker, folder = StatelessWorker(), tmp_path / "s"
    session = api.Session.open(worker, folder, repo_root=ROOT, mode=mode)
    try:
        first = session.send("Invent a fresh identifier and return it.")
        assert worker.prompts == ["Invent a fresh identifier and return it."]
        if reopen:
            session.close()
            session = api.Session.open(worker, folder, repo_root=ROOT)
        second = session.send("Repeat the identifier from your last answer.")
        assert first.text in worker.prompts[-1]
        assert "reference" in worker.prompts[-1].lower()
        assert "violet-orbit-7392" not in session.host.engine.workspace.turn_source()
        assert second.provenance["verification"]["reproduced_by_host"] is False
        assert second.provenance["verification"]["witness_form"] == "none"
    finally:
        session.close()


@pytest.mark.parametrize("mode", ["direct", "saver"])
def test_unrelated_direct_turn_receives_its_own_request_only(tmp_path, mode):
    worker = StatelessWorker()
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode=mode) as session:
        session.send("Invent a fresh identifier and return it.")
        worker.sys1_client.follow_up = False
        session.send("Explain why the sky is blue.")
    assert worker.prompts[-1] == "Explain why the sky is blue."


def test_cancelled_turn_has_no_published_answer_to_carry(tmp_path):
    worker = StatelessWorker()
    worker.answer = ""
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        assert session.send("Invent a fresh identifier.").stage == "CLOSED_CANCELLED"
        worker.answer = "Another answer."
        session.send("Try again.")
        assert "Previous published answer" not in worker.prompts[-1]
