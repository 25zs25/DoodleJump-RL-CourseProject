"""Read native runtime geometry; reject stale or independently resized game views."""
from pathlib import Path
import json, math

COMMIT='d4b6071813a9c1353267d53dcfa9d8abc3e5b2f4'

def load_viewport(path):
    value=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if value.get('upstream_commit')!=COMMIT:
        raise ValueError('Window config must come from this original-game preview.')
    for key in ('windowWidth','windowHeight','width','height','stepSize','jump','gravity'):
        if not isinstance(value.get(key),(int,float)) or not math.isfinite(value[key]) or value[key]<=0:
            raise ValueError(f'Invalid native geometry: {key}')
    h,w=value['windowHeight'],value['windowWidth']
    expected_width=w if w<=768 else h*9/16
    expected={'width':expected_width,'height':h,'stepSize':math.floor(h/9),
              'jump':8.15*h/1289,'gravity':.16*h/1289}
    for key,target in expected.items():
        if abs(value[key]-target)>1e-7:
            raise ValueError(f'Native {key} differs from fresh upstream initialization; refresh game then export again.')
    if h<18:
        raise ValueError('Viewport too small for training.')
    return value
