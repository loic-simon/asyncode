import sys
import unittest
from unittest import mock

sys.path.append("..")
import asyncode


class TestAsyncodeRerouting(unittest.IsolatedAsyncioTestCase):
    """Test reroute_stdout and reroute_stderr default and custom behaviors"""

    def setUp(self):
        self.console = asyncode.AsyncInteractiveConsole()
        patch = mock.patch('asyncode.input', create=True)
        self.addCleanup(patch.__exit__, None, None, None)
        self.infunc = patch.__enter__()

    async def test_reroute_stdout(self):
        """Check reroute_stdout argument is correctly handled"""
        # reroute_stdout default
        self.infunc.side_effect = ["'griz'", EOFError('Finished')]
        self.console.write = mock.AsyncMock(self.console.write)
        await self.console.interact()
        write_calls = ''.join(
            ''.join(call[0]) for call in self.console.write.call_args_list)
        self.assertIn('griz', write_calls)

        # reroute_stdout = True
        self.infunc.side_effect = ["'griz'", EOFError('Finished')]
        console = asyncode.AsyncInteractiveConsole(reroute_stdout=True)
        console.write = mock.AsyncMock(console.write)
        await console.interact()
        write_calls = ''.join(
            ''.join(call[0]) for call in console.write.call_args_list)
        self.assertIn('griz', write_calls)

        # reroute_stdout = False
        self.infunc.side_effect = ["'griz'", EOFError('Finished')]
        console = asyncode.AsyncInteractiveConsole(reroute_stdout=False)
        console.write = mock.AsyncMock(console.write)
        with mock.patch('sys.stdout'):
            await console.interact()
        write_calls = ''.join(
            ''.join(call[0]) for call in console.write.call_args_list)
        self.assertNotIn('griz', write_calls)

    async def test_reroute_stderr(self):
        """Check reroute_stderr argument is correctly handled"""
        # reroute_stderr default
        self.infunc.side_effect = ["import sys",
                                   "print('griz', file=sys.stderr)",
                                   EOFError('Finished')]
        self.console.write = mock.AsyncMock(self.console.write)
        await self.console.interact()
        write_calls = ''.join(
            ''.join(call[0]) for call in self.console.write.call_args_list)
        self.assertIn('griz', write_calls)

        # reroute_stderr = True
        self.infunc.side_effect = ["import sys",
                                   "print('griz', file=sys.stderr)",
                                   EOFError('Finished')]
        console = asyncode.AsyncInteractiveConsole(reroute_stderr=True)
        console.write = mock.AsyncMock(console.write)
        await console.interact()
        write_calls = ''.join(
            ''.join(call[0]) for call in console.write.call_args_list)
        self.assertIn('griz', write_calls)

        # reroute_stderr = False
        self.infunc.side_effect = ["import sys",
                                   "print('griz', file=sys.stderr)",
                                   EOFError('Finished')]
        console = asyncode.AsyncInteractiveConsole(reroute_stderr=False)
        console.write = mock.AsyncMock(console.write)
        with mock.patch('sys.stderr'):
            await console.interact()
        write_calls = ''.join(
            ''.join(call[0]) for call in console.write.call_args_list)
        self.assertNotIn('griz', write_calls)
