import sys
import unittest
from contextlib import ExitStack
from unittest import mock

sys.path.append("..")
import asyncode


class TestAsyncodeAsync(unittest.IsolatedAsyncioTestCase):
    """Do same tests as code standard module (but async)"""

    def setUp(self):
        self.console = asyncode.AsyncInteractiveConsole()
        self.mock_sys()

    def mock_sys(self):
        "Mock system environment for AsyncInteractiveConsole"
        # use exit stack to match patch context managers to addCleanup
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.infunc = stack.enter_context(mock.patch('asyncode.input',
                                          create=True))
        self.stdout = stack.enter_context(mock.patch('asyncode.sys.stdout'))
        self.stderr = stack.enter_context(mock.patch('asyncode.sys.stderr'))
        self.sysmod = stack.enter_context(mock.patch('asyncode.sys',
                                          wraps=asyncode.sys,
                                          spec=asyncode.sys))

    async def test_toplevel_await(self):
        """Check top-level await statements are not rejected"""
        self.infunc.side_effect = ["await lindbz",
                                   EOFError('Finished')]
        await self.console.interact()
        output = ''.join(''.join(call[1]) for call in self.stderr.method_calls)
        self.assertNotIn('SyntaxError', output)

    async def test_coroutine(self):
        """Check coroutines are awaited"""
        self.infunc.side_effect = ["import asyncio",
                                   "await asyncio.sleep(0, 'grizzz')",
                                   EOFError('Finished')]
        await self.console.interact()
        output = ''.join(''.join(call[1]) for call in self.stdout.method_calls)
        self.assertIn('grizzz', output)

    async def test_exc_in_coroutine(self):
        """Check exceptions occuring in coroutines are retrieved"""
        self.infunc.side_effect = ["import asyncio",
                                   "await asyncio.sleep(None)",
                                   EOFError('Finished')]
        await self.console.interact()
        output = ''.join(''.join(call[1]) for call in self.stderr.method_calls)
        self.assertIn('TypeError', output)
