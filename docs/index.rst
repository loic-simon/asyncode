.. asyncode documentation master file, created by
   sphinx-quickstart on Sun Dec  6 01:23:44 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to asyncode's documentation!
====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


..
.. Emulating Python's interactive interpreter in asynchronous contexts.
..
..
.. Abstract
.. -------------------------------

The goal of this module is to allow to emulate Python's interactive interpreter
in already running asnychronous contexts.

For example, it allows to debug a Discord bot (built with `Discord.py`_, that
uses async mechanisms) directly inside Discord client, by processing
messages sent in a channel as interpreter commands.


*This module source code is based on* :mod:`code` *standard module by Guido van
Rossum and co-othors, and on* `asyncio.__main__`_ *code by Yury Selivanov.*

*It differs from the latter in that its classes operate in already running
asynchronous contexts, while running* ``python -m asyncio`` *create and run a
new asyncio loop.*

.. _Discord.py: https://discordpy.readthedocs.io/
.. _asyncio.__main__: https://github.com/python/cpython/blob/master/Lib/asyncio/__main__.py



Rationale
-------------------------------


Several issues prevent directly using Python's :mod:`code` standard module :

- :class:`code.InteractiveConsole` and :class:`code.InteractiveInterpreter`
  methods are not asynchronous, so the interpreter will be blocking the loop
  between two inputs: one solution would be to run it in a specific thread,
  but this adds a lot of complexity and potential error sources;

- the code compiler (:class:`codeop.CommandCompiler` instance) disallow using
  ``await`` statements outside of functions, so it would be very unpleasant
  to await coroutines inside the interpreter (declare a asynchronous
  function and use :func:`asyncio.get_running_loop`);

- information printed by functions and by :func:`repr` (writing only an
  object name) to :data:`sys.stdout` and :data:`sys.stderr` would be lost, as
  an we need an asynchronous function to send content to the interpreter.


Implementation
-------------------------------

This module provides two classes, :class:`AsyncInteractiveInterpreter` and
:class:`AsyncInteractiveConsole`, who do the exact same job as standard
:class:`code.InteractiveInterpreter` and :class:`code.InteractiveConsole`,
except that:

- :meth:`~AsyncInteractiveInterpreter.write``,
  :meth:`~AsyncInteractiveConsole.raw_input`` and other higher-level methods
  are asynchronous (they return coroutines, that have to be awaited).

    .. warning::
    	Only text input/output is asnychronous: in particular, **code executed
        in the interpreter will still be blocking**.

        For example, sending ``time.sleep(10)`` in a running ``AsyncInteractiveConsole`` will block
        every other concurrent tasks for 10 seconds.

- the compiler allows top-level ``await`` statements;

- instead of being directly executed, compiled code is wrapped in a function
  object (:class:`types.FunctionType`) which is called (): if the result is a
  coroutine, it is then awaited; otherwise, this is strictly identical to
  direct code execution.

- :data:`sys.stdout` and :data:`sys.stderr` are catch during code execution,
  then gathered content is written in the interpreter. This behavior can be
  turned off with ``reroute_stdout`` and ``reroute_stderr`` arguments.


Usage
-------------------------------

``asyncode`` is meant to be used in existing asynchronous environments.
Minimal working code will need to subclass provided classes to implement
appropriate functions:

.. code-block:: py

    import asyncode

    class MyAsyncConsole(asyncode.AsyncInteractiveConsole):
        """AsyncInteractiveConsole adapted to running environment"""

        async def write(self, data):
            """Use appropriate method"""
            await some_output_coroutine(data)

        async def raw_input(self, prompt=""):
            """Use appropriate method"""
            if prompt:
                await some_output_coroutine(prompt)

            data = await some_input_coroutine()
            return data


    async def run_interpreter():
        """Run an interactive Python interpreter"""
        console = MyAsyncConsole()
        try:
            await console.interact()
        except SystemExit:
            # Do not exit the whole program!
            await some_output_coroutine("Bye!")



.. warning::

    As for :mod:`code` classes, :exc:`SystemExit` exceptions are **not**
    catched by provided methods. This mean that ``quit()``/``exit()`` commands
    run inside the console will **quit your whole program** if not explicitly
    catched (as in this example), which may not be what you want.



.. note::

    High-level async environments may not provide a way to send EOF or
    KeyboardInterrupt signals to the console. Custom implementations should
    not forget a exit mechanism (like recognize some custom message), or just
    catch SystemExit (as in this example).


API Reference
-------------------------------


.. automodule:: asyncode
   :members:
   :special-members:
   :member-order: bysource









Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
