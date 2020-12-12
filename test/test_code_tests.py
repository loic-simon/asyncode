import sys
import unittest
from textwrap import dedent
from contextlib import ExitStack
from unittest import mock

sys.path.append("..")
import asyncode


class TestAsyncodeLikeCode(unittest.IsolatedAsyncioTestCase):
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
        if sys.excepthook is sys.__excepthook__:
            self.sysmod.excepthook = self.sysmod.__excepthook__
        del self.sysmod.ps1
        del self.sysmod.ps2

    async def test_ps1(self):
        """Check default / custom sys.ps1 are correctly set"""
        # default
        self.infunc.side_effect = EOFError('Finished')
        await self.console.interact()
        self.assertEqual(self.sysmod.ps1, '>>> ')
        # custom
        self.sysmod.ps1 = 'custom1> '
        await self.console.interact()
        self.assertEqual(self.sysmod.ps1, 'custom1> ')

    async def test_ps2(self):
        """Check default / custom sys.ps2 are correctly set"""
        # default
        self.infunc.side_effect = EOFError('Finished')
        await self.console.interact()
        self.assertEqual(self.sysmod.ps2, '... ')
        # custom
        self.sysmod.ps1 = 'custom2> '
        await self.console.interact()
        self.assertEqual(self.sysmod.ps1, 'custom2> ')

    async def test_console_stderr(self):
        """Check stdout is correctly printed"""
        self.infunc.side_effect = ["'antioch'", "", EOFError('Finished')]
        await self.console.interact()
        for call in list(self.stdout.method_calls):
            if 'antioch' in ''.join(call[1]):
                break
        else:
            raise AssertionError("no console stdout")

    async def test_syntax_error(self):
        """Check compiler exceptions are retrieved"""
        self.infunc.side_effect = ["undefined", EOFError('Finished')]
        await self.console.interact()
        for call in self.stderr.method_calls:
            if 'NameError' in ''.join(call[1]):
                break
        else:
            raise AssertionError("No syntax error from console")

    async def test_sysexcepthook(self):
        """Check custom excepthooks are called"""
        self.infunc.side_effect = ["raise ValueError('')",
                                    EOFError('Finished')]
        hook = mock.Mock()
        self.sysmod.excepthook = hook
        await self.console.interact()
        self.assertTrue(hook.called)

    async def test_banner(self):
        """Check default/custom banner is correctly printed"""
        # with banner ==> stderr called 3 times, custom banner in 1st call
        self.infunc.side_effect = EOFError('Finished')
        await self.console.interact(banner='Foo')
        self.assertEqual(len(self.stderr.method_calls), 3)
        banner_call = self.stderr.method_calls[0]
        self.assertEqual(banner_call, ['write', ('Foo\n',), {}])

        # no banner ==> stderr called 2 times
        self.stderr.reset_mock()
        self.infunc.side_effect = EOFError('Finished')
        await self.console.interact(banner='')
        self.assertEqual(len(self.stderr.method_calls), 2)

    async def test_exit_msg(self):
        """Check default/custom exit message is correctly printed"""
        # default exit message ==> stderr called 2 times and good msg
        self.infunc.side_effect = EOFError('Finished')
        await self.console.interact(banner='')
        self.assertEqual(len(self.stderr.method_calls), 2)
        err_msg = self.stderr.method_calls[1]
        expected = 'now exiting AsyncInteractiveConsole...\n'
        self.assertEqual(err_msg, ['write', (expected,), {}])

        # no exit message ==> stderr called 1 time
        self.stderr.reset_mock()
        self.infunc.side_effect = EOFError('Finished')
        await self.console.interact(banner='', exitmsg='')
        self.assertEqual(len(self.stderr.method_calls), 1)

        # custom exit message ==> stderr called 2 times and custom msg
        self.stderr.reset_mock()
        message = (
            'bye! \N{GREEK SMALL LETTER ZETA}\N{CYRILLIC SMALL LETTER ZHE}'
            )
        self.infunc.side_effect = EOFError('Finished')
        await self.console.interact(banner='', exitmsg=message)
        self.assertEqual(len(self.stderr.method_calls), 2)
        err_msg = self.stderr.method_calls[1]
        expected = message + '\n'
        self.assertEqual(err_msg, ['write', (expected,), {}])

    async def test_cause_tb(self):
        """Check exceptions chaining is correctly printed"""
        self.infunc.side_effect = ["raise ValueError('') from AttributeError",
                                    EOFError('Finished')]
        await self.console.interact()
        output = ''.join(''.join(call[1]) for call in self.stderr.method_calls)
        expected = dedent("""
        AttributeError

        The above exception was the direct cause of the following exception:

        Traceback (most recent call last):
          File "<console>", line 1, in <module>
        ValueError
        """)
        self.assertIn(expected, output)

    async def test_context_tb(self):
        """Check exceptions inception is correctly printed"""
        self.infunc.side_effect = ["try: ham\nexcept: eggs\n",
                                   EOFError('Finished')]
        await self.console.interact()
        output = ''.join(''.join(call[1]) for call in self.stderr.method_calls)
        expected = dedent("""
        Traceback (most recent call last):
          File "<console>", line 1, in <module>
        NameError: name 'ham' is not defined

        During handling of the above exception, another exception occurred:

        Traceback (most recent call last):
          File "<console>", line 2, in <module>
        NameError: name 'eggs' is not defined
        """)
        self.assertIn(expected, output)
