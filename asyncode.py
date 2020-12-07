"""Emulating Python's interactive interpreter in asynchronous contexts.

"""

# Based on code standard module by Guido van Rossum and co-othors,
# and on asyncio.__main__ code by Yury Selivanov (differs from it in
# that these classes operate in already running asynchronous contexts)


import sys
import traceback
import code
import asyncio
import ast
import io
import types

__all__ = ["AsyncInteractiveInterpreter", "AsyncInteractiveConsole"]


class AsyncInteractiveInterpreter(code.InteractiveInterpreter):
    """Base class for AsyncInteractiveConsole.

    This class inherits from :class:`code.InteractiveInterpreter`. It
      - makes ``runsource``, ``runcode``, ``showsyntaxerror``,
        ``showtraceback`` and ``write`` methods asynchronous
        (they return coroutines, that have to be awaited);
      - tell the compiler to allow top-level ``await`` statements;
      - awaits coroutines returned by such statements execution;
      - catches :data:`sys.stdout` and :data:`sys.stderr` during code
        execution, then send gathered content using :meth:`write`.

    This class deals with parsing and interpreter state (the user's
    namespace); it doesn't deal with input buffering or prompting or
    input file naming (the filename is always passed in explicitly).

    """

    def __init__(self, locals, *, reroute_stdout=True, reroute_stderr=True):
        """Constructor.

        The optional ``locals`` argument specifies the dictionary in
        which code will be executed; it defaults to a newly created
        dictionary with key ``"__name__"`` set to ``"__console__"`` and
        key ``"__doc__"`` set to ``None``.

        The optional ``reroute_stdout`` and ``reroute_stderr`` keyword
        arguments, if set to ``False``, disable catching
        :data:`sys.stdout` and :data:`sys.stderr`, respectively.

        """
        super().__init__(locals)
        if "__builtins__" not in self.locals:
            # Why should __builtins__ be specified here and not in
            # code.InteractiveInterpreter? No idea, but necessary!
            self.locals["__builtins__"] = __builtins__

        self.compile.compiler.flags |= ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
        self.reroute_stdout = reroute_stdout
        self.reroute_stderr = reroute_stderr

    async def runsource(self, source, filename="<input>", symbol="single"):
        """Compile and run some source in the interpreter.

        Arguments and behavior are as for :class:`code.InteractiveInterpreter`,
        except that this is an asynchronous method.

        Unless explicitly disabled, this method catches :data:`sys.stdout`
        and :data:`sys.stderr` during code execution.  If some data has
        been written, it is send using :meth:`write` before returning.

        """
        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            await self.showsyntaxerror(filename)
            return False

        if code is None:
            # Case 2
            return True

        # Case 3a
        if self.reroute_stdout or self.reroute_stderr:
            # Cache current stdout and stderr
            _stdout = sys.stdout
            _stderr = sys.stderr
            # Create temporary IO buffer
            buffer = io.StringIO()
            try:
                if self.reroute_stdout:
                    # Catch standard output
                    sys.stdout = buffer
                if self.reroute_stderr:
                    # Catch error output
                    sys.stderr = buffer
                await self.runcode(code)
                return False
            finally:
                # Restore sys.stdout and sys.stderr
                sys.stdout = _stdout
                sys.stderr = _stderr
                data = buffer.getvalue()
                if data:
                    # Write gathered output (from print, repr...)
                    await self.write(data)
                buffer.close()

        # Case 3b
        else:
            await self.runcode(code)
            return False

    async def runcode(self, code):
        """Execute a code object.

        Arguments and behavior are as for :class:`code.InteractiveInterpreter`,
        except that this is an asynchronous method and that 'code' is
        wrapped in a function object which is called instead of being
        directly executed.

        If the result is a coroutine, it is then awaited before this
        method returns. Exceptions are processed in the same way as
        during code execution.

        """
        func = types.FunctionType(code, self.locals)
        coro = None
        try:
            # Same as exec(code, self.locals) but return result
            coro = func()
        except SystemExit:
            raise
        except BaseException:
            await self.showtraceback()

        if asyncio.iscoroutine(coro):
            # func() returned a coroutine
            try:
                # We await it
                await coro
            except SystemExit:
                raise
            except BaseException:
                await self.showtraceback()

    async def showsyntaxerror(self, filename=None):
        """Display the syntax error that just occurred.

        Arguments and behavior are as for :class:`code.InteractiveInterpreter`,
        except that this is an asynchronous method.

        """
        type, value, tb = sys.exc_info()
        sys.last_type = type
        sys.last_value = value
        sys.last_traceback = tb
        if filename and type is SyntaxError:
            # Work hard to stuff the correct filename in the exception
            try:
                msg, (dummy_filename, lineno, offset, line) = value.args
            except ValueError:
                # Not the format we expect; leave it alone
                pass
            else:
                # Stuff in the right filename
                value = SyntaxError(msg, (filename, lineno, offset, line))
                sys.last_value = value
        if sys.excepthook is sys.__excepthook__:
            lines = traceback.format_exception_only(type, value)
            await self.write(''.join(lines))
        else:
            # If someone has set sys.excepthook, we let that take precedence
            # over self.write
            sys.excepthook(type, value, tb)

    async def showtraceback(self):
        """Display the exception that just occurred.

        Arguments and behavior are as for :class:`code.InteractiveInterpreter`,
        except that this is an asynchronous method.

        """
        sys.last_type, sys.last_value, last_tb = ei = sys.exc_info()
        sys.last_traceback = last_tb
        try:
            lines = traceback.format_exception(ei[0], ei[1], last_tb.tb_next)
            if sys.excepthook is sys.__excepthook__:
                await self.write(''.join(lines))
            else:
                # If someone has set sys.excepthook, we let that take precedence
                # over self.write
                sys.excepthook(ei[0], ei[1], last_tb)
        finally:
            last_tb = ei = None

    async def write(self, data):
        """Write a string.

        Arguments are as for :class:`code.InteractiveInterpreter`.
        While that this is an async method, the base implementation
        still writes to :data:`sys.stderr`; a subclass should replace
        this with a different (asynchronous) implementation.

        """
        sys.stderr.write(data)


class AsyncInteractiveConsole(AsyncInteractiveInterpreter,
                              code.InteractiveConsole):
    """Emulate interactive Python interpreter in asynchronous contexts.

    This class builds on :class:`AsyncInteractiveInterpreter` and adds
    prompting using the familiar :data:`sys.ps1` and :data:`sys.ps2`,
    and input buffering.

    It does exactly the same job as :class:`code.InteractiveConsole`,
    except that ``interact``, ``push`` and ``raw_input`` methods are
    asynchronous (they return coroutines, that have to be awaited).

    """

    def __init__(self, locals=None, filename="<console>", *,
                 reroute_stdout=True, reroute_stderr=True):
        """Constructor.

        The optional ``locals``, ``reroute_stdout`` and
        ``reroute_stderr`` arguments will be passed to the
        :class:`AsyncInteractiveInterpreter` base class.
        The optional ``filename`` argument should specify the
        (file)name of the input stream; it will show up in tracebacks.

        """
        super().__init__(locals, reroute_stdout=reroute_stdout,
                         reroute_stderr=reroute_stderr)
        self.filename = filename
        self.resetbuffer()

    async def interact(self, banner=None, exitmsg=None):
        """Closely emulate the interactive Python console.

        Arguments and behavior are as for :class:`code.InteractiveConsole`,
        except that this is an asynchronous method that awaits inputs.

        """
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        aw = 'async REPL: use "await" directly instead of "asyncio.run()".'
        cprt = 'Type "help", "copyright", "credits" or "license" for more information.'
        if banner is None:
            await self.write("Python {} on {}\n{}\n{}\n({})\n".format(
                             sys.version, sys.platform, aw, cprt,
                             self.__class__.__name__))
        elif banner:
            await self.write("{}\n".format(banner))
        more = 0
        while 1:
            try:
                if more:
                    prompt = sys.ps2
                else:
                    prompt = sys.ps1
                try:
                    line = await self.raw_input(prompt)
                except EOFError:
                    await self.write("\n")
                    break
                else:
                    more = await self.push(line)
            except KeyboardInterrupt:
                await self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0
        if exitmsg is None:
            await self.write('now exiting {}...\n'.format(
                             self.__class__.__name__))
        elif exitmsg != '':
            await self.write('{}\n'.format(exitmsg))

    async def push(self, line):
        """Push a line to the interpreter.

        Arguments and behavior are as for :class:`code.InteractiveConsole`,
        except that this is an asynchronous method.

        """
        self.buffer.append(line)
        source = "\n".join(self.buffer)
        more = await self.runsource(source, self.filename)
        if not more:
            self.resetbuffer()
        return more

    async def raw_input(self, prompt=""):
        """Write a prompt and read a line.

        Arguments and behavior are as for :class:`code.InteractiveConsole`.
        While that this is an async method, the base implementation
        still uses the built-in function :func:`input`; a subclass should
        replace this with a different (asynchronous) implementation.

        """
        return input(prompt)
