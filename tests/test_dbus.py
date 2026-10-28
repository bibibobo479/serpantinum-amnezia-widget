#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Integration test. Run under dbus-run-session; never talks to the real VPN."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from gi.repository import Gio, GLib

ROOT=Path(__file__).resolve().parents[1]
SNI='org.kde.StatusNotifierItem'
MENU='com.canonical.dbusmenu'
WATCHER='org.kde.StatusNotifierWatcher'


def server():
    bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
    bus.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','RequestName',GLib.Variant('(su)',(WATCHER,0)),None,Gio.DBusCallFlags.NONE,1000,None)
    xml=f'''<node>
    <interface name="{WATCHER}"><property name="RegisteredStatusNotifierItems" type="as" access="read"/></interface>
    <interface name="{SNI}"><property name="Id" type="s" access="read"/><property name="Title" type="s" access="read"/><property name="Menu" type="o" access="read"/><method name="Activate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method></interface>
    <interface name="{MENU}"><method name="GetLayout"><arg type="i" direction="in"/><arg type="i" direction="in"/><arg type="as" direction="in"/><arg type="u" direction="out"/><arg type="(ia{{sv}}av)" direction="out"/></method><method name="Event"><arg type="i" direction="in"/><arg type="s" direction="in"/><arg type="v" direction="in"/><arg type="u" direction="in"/></method></interface>
    </node>'''
    interfaces=Gio.DBusNodeInfo.new_for_xml(xml).interfaces
    state={'active':False}
    def get_prop(conn,sender,path,interface,prop):
        if prop=='RegisteredStatusNotifierItems':return GLib.Variant('as',[bus.get_unique_name()+'/StatusNotifierItem'])
        return GLib.Variant('o' if prop=='Menu' else 's','/MenuBar' if prop=='Menu' else 'AmneziaVPN')
    def method(conn,sender,path,interface,name,args,invocation):
        if name=='GetLayout':
            def item(ident,label,enabled):return GLib.Variant('(ia{sv}av)',(ident,{'label':GLib.Variant('s',label),'enabled':GLib.Variant('b',enabled)},[]))
            tree=(0,{},[item(91,'&Connect',not state['active']),item(27,'Disconnect',state['active']),item(55,'Quit AmneziaVPN',True)])
            invocation.return_value(GLib.Variant('(u(ia{sv}av))',(1,tree)))
        elif name=='Event':
            ident,event,data,stamp=args.unpack()
            if event!='clicked' or ident not in (91,27):
                invocation.return_dbus_error('org.test.InvalidAction','Not an allowed native action');return
            state['active']=ident==91
            invocation.return_value(GLib.Variant('()',()))
        else:invocation.return_value(GLib.Variant('()',()))
    for path,info in zip(('/StatusNotifierWatcher','/StatusNotifierItem','/MenuBar'),interfaces):
        bus.register_object(path,info,method,get_prop,None)
    print('READY',flush=True)
    GLib.MainLoop().run()


class DBusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=subprocess.Popen([sys.executable,__file__,'--server'],stdout=subprocess.PIPE,text=True)
        assert cls.server.stdout.readline().strip()=='READY'
    @classmethod
    def tearDownClass(cls):cls.server.terminate();cls.server.wait(timeout=3);cls.server.stdout.close()
    def command(self,name):
        output=subprocess.check_output([sys.executable,str(ROOT/'widget/amnezia.py'),name],text=True,timeout=5)
        return json.loads(output)
    def test_native_menu_actions_and_stale_state_rejection(self):
        self.assertEqual(self.command('status')['state'],'offline')
        self.assertEqual(self.command('disconnect'),{'ok':False,'error':'action_unavailable'})
        self.assertTrue(self.command('connect')['ok'])
        self.assertEqual(self.command('status')['state'],'active')
        self.assertFalse(self.command('connect')['ok'])
        self.assertTrue(self.command('open')['ok'])
        self.assertTrue(self.command('disconnect')['ok'])
        self.assertEqual(self.command('status')['state'],'offline')
    def test_watch_stream(self):
        p=subprocess.Popen([sys.executable,str(ROOT/'widget/amnezia.py'),'watch'],stdout=subprocess.PIPE,text=True)
        try:
            self.assertEqual(json.loads(p.stdout.readline())['state'],'offline')
        finally:p.terminate();p.wait(timeout=3);p.stdout.close()


if __name__=='__main__':
    if '--server' in sys.argv:server()
    elif os.environ.get('AMNEZIA_TEST_PRIVATE_BUS')=='1':unittest.main()
    else:raise SystemExit('Run: AMNEZIA_TEST_PRIVATE_BUS=1 dbus-run-session -- python3 tests/test_dbus.py')
