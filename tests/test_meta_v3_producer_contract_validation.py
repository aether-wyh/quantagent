"""No candidate generation during outside-job metadata admission or status."""
import pytest
from quanta_agents.meta_v3 import generator_controls as gc,registered_producer as rp
from quanta_agents.meta_v3.ledger import AdmissionBlocked

@pytest.mark.parametrize('arm',['fixed','random'])
def test_contract_validation_never_computes_candidate_order(monkeypatch,arm):
    space={'program_template':{'factors':[],'target_weight_expression':'{{weight}}'},'parameters':{'weight':[.2,.4]},'axis_order':['weight']}
    contract={'kind':rp.VERSION,'arm':arm,'space':space,'count':2,'seed':'0123456789abcdef'*4}
    monkeypatch.setattr(gc,'indices',lambda *a,**kw:pytest.fail('candidate order computed outside job'))
    rp.validate_contract(contract)
    with pytest.raises(AdmissionBlocked,match='256bit seed'):rp.validate_contract({**contract,'seed':'not-a-seed'})
    with pytest.raises(AdmissionBlocked,match='count exceeds domain'):rp.validate_contract({**contract,'count':3})
