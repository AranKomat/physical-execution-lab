from pathlib import Path
import pytest
from prl.contracts import Case
from prl.util import digest
from prl.journal import Journal
from prl.registry import Registry
from prl.budget import Budget
from prl.governor import Governor,GovernorConfig
from prl.backends.toy import ToyBackend

@pytest.fixture
def case():
    return Case('test.0','synthetic_contract',0,0,0,'dev',digest('test'),'normal')

@pytest.fixture
def runtime(tmp_path,case):
    journal=Journal(tmp_path/'events.jsonl');b=ToyBackend(case,tmp_path)
    g=Governor(b,Registry(),Budget(max_steps=300),journal,GovernorConfig(stall_checks=2))
    yield b,g,journal
    journal.close()
