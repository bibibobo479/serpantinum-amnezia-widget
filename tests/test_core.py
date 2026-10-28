# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import tempfile
from pathlib import Path
import unittest
import install

spec = importlib.util.spec_from_file_location('amnezia', Path(__file__).resolve().parents[1]/'widget/amnezia.py')
amnezia = importlib.util.module_from_spec(spec)
spec.loader.exec_module(amnezia)


def menu(connect=True, disconnect=False, labels=('Connect', 'Disconnect')):
    return (0, {}, [(12, {'label': labels[0], 'enabled': connect}, []),
                    (34, {'label': labels[1], 'enabled': disconnect}, [])])


class BackendTests(unittest.TestCase):
    def test_native_state_is_not_a_handshake_claim(self):
        self.assertEqual(amnezia.state_from(amnezia.menu_actions(menu())), 'offline')
        self.assertEqual(amnezia.state_from(amnezia.menu_actions(menu(False, True))), 'active')
        for a,b in ((True,True),(False,False)):
            self.assertEqual(amnezia.state_from(amnezia.menu_actions(menu(a,b))), 'unknown')

    def test_localization_and_mnemonics(self):
        for names in (('&Connect', '&Disconnect'), ('Подключиться', 'Отключиться'), ('Verbinden','Trennen'), ('连接','断开连接')):
            self.assertEqual(amnezia.menu_actions(menu(labels=names))['connect'], (12, True))

    def test_unknown_labels_are_never_guessed(self):
        self.assertEqual(amnezia.state_from(amnezia.menu_actions(menu(labels=('Action 1','Action 2')))), 'unknown')
        node=menu(); node[2].append((99, {'label':'Connect'}, []))
        with self.assertRaises(ValueError): amnezia.menu_actions(node)

    def test_traffic_excludes_other_vpns_and_resets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def write(name,rx,tx):
                p=root/name/'statistics';p.mkdir(parents=True,exist_ok=True)
                (p/'rx_bytes').write_text(str(rx));(p/'tx_bytes').write_text(str(tx))
            write('amn0',100,200);write('tun0',900000,900000);write('wlp2s0',900000,900000)
            t=amnezia.Traffic(root)
            self.assertEqual(t.read(True,1)['rx_rate'],0)
            write('amn0',300,600)
            result=t.read(True,3)
            self.assertEqual(result['interfaces'],['amn0']);self.assertEqual(result['rx_rate'],100);self.assertEqual(result['tx_rate'],200)
            write('amn0',0,0)
            self.assertEqual(t.read(True,5)['rx_rate'],0)
            self.assertEqual(t.read(False,7)['interfaces'],[])
            self.assertEqual(t.read(True,9)['rx_rate'],0)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'shell с пробелами'
        self.registry=self.root/'widgets/WidgetRegistry.qml';self.registry.parent.mkdir(parents=True)
        self.original='pragma Singleton\nQtObject {\n    property var types: ({\n        "clock": {}\n    })\n}\n'
        self.registry.write_text(self.original)
        self.payload={name:b'test' for name in install.FILES}

    def tearDown(self): self.tmp.cleanup()

    def test_install_idempotence_and_non_destructive_remove(self):
        install.install(self.root,self.payload);install.install(self.root,self.payload)
        text=self.registry.read_text()
        self.assertEqual(text.count(install.START),1)
        self.registry.write_text(text.replace('"clock": {}','"clock": {}, "other": {}'))
        install.install(self.root,remove=True)
        self.assertNotIn('amnezia',self.registry.read_text())
        self.assertIn('"other": {}',self.registry.read_text())
        self.assertEqual(self.registry.with_name('WidgetRegistry.qml.before-amnezia').read_text(),self.original)

    def test_unsupported_format_has_no_side_effects(self):
        self.registry.write_text('unsupported')
        with self.assertRaises(ValueError):install.install(self.root,self.payload)
        self.assertFalse((self.root/'widgets/faces').exists())

    def test_unrelated_directory_is_preserved(self):
        target=self.root/'widgets/faces/amnezia';target.mkdir(parents=True)
        (target/'mine').write_text('keep')
        with self.assertRaises(ValueError):install.install(self.root,self.payload)
        self.assertEqual(self.registry.read_text(),self.original)
        self.assertEqual((target/'mine').read_text(),'keep')

    def test_broken_markers_and_conflicting_registration(self):
        for text in (self.original+install.START,self.original.replace('"clock"','"amnezia"')):
            with self.assertRaises(ValueError):install.registry_update(text)


if __name__=='__main__': unittest.main()
