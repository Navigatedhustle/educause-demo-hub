"""Isolated failure-path checks. These do not start or stop real demos."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import controller as module


class Failures(unittest.TestCase):
    def test_health_requires_real_readiness_not_just_http_200(self):
        for data in ({'ok':False},{'status':'loading'},[],{'models':[]}):
            response=Mock()
            response.__enter__=Mock(return_value=response)
            response.__exit__=Mock(return_value=False)
            response.read.return_value=json.dumps(data).encode()
            with patch.object(module.urllib.request,'urlopen',return_value=response):
                self.assertFalse(module.healthy('http://127.0.0.1:8130/health'))

    def controller(self):
        manager = module.Controller()
        manager.generation = 1
        manager.state.update(phase='starting',demo='atlas',generation=1)
        manager.stop_resources = Mock()
        return manager

    def test_low_memory_is_reported_before_spawning(self):
        manager = self.controller()
        with patch.object(module,'atlas_health',return_value={'UI':False}), patch.object(module,'available_gib',return_value=49.25), patch.object(module.time,'monotonic',side_effect=[0,61]), patch.object(module.subprocess,'Popen') as spawn:
            manager.run('atlas',threading.Event(),1)
        self.assertEqual(manager.state['phase'],'error')
        self.assertIn('49.2 GiB',manager.state['message'])
        spawn.assert_not_called()

    def test_180_second_timeout_keeps_exact_last_20_log_lines(self):
        manager = self.controller()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            def spawn(*args,**kwargs):
                kwargs['stdout'].write('\n'.join(f'line {i}' for i in range(30)))
                kwargs['stdout'].flush()
                return Mock(poll=Mock(return_value=None))
            with patch.object(module,'CACHE',path),patch.object(module,'atlas_health',return_value={'UI':False}),patch.object(module,'available_gib',return_value=100),patch.object(module.time,'monotonic',side_effect=[0,0,0,181]),patch.object(module.subprocess,'Popen',side_effect=spawn):
                manager.run('atlas',threading.Event(),1)
        self.assertEqual(manager.state['phase'],'error')
        self.assertIn('180 seconds',manager.state['message'])
        self.assertEqual(manager.state['log_tail'].splitlines(),[f'line {i}' for i in range(10,30)])
        self.assertEqual(manager.stop_resources.call_count,2)

    def test_stale_transition_cannot_overwrite_stop_state(self):
        manager = self.controller()
        manager.generation=2
        manager.state.update(phase='stopping',demo=None,generation=2)
        with patch.object(module,'atlas_health',return_value={'UI':True}):
            manager.run('atlas',threading.Event(),1)
        self.assertEqual(manager.state['phase'],'stopping')
        self.assertIsNone(manager.state['demo'])


if __name__=='__main__':
    unittest.main()
