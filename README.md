# asyncode
[![PyPI](https://img.shields.io/pypi/v/asyncode)](https://pypi.org/project/asyncode)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/asyncode)](https://pypi.org/project/asyncode)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/asyncode)](https://pypi.org/project/asyncode)
[![Read the Docs](https://img.shields.io/readthedocs/asyncode)](https://asyncode.readthedocs.io)
[![Travis CI](https://img.shields.io/travis/loic-simon/asyncode)](https://travis-ci.org/github/loic-simon/asyncode)

Python package for emulating Python's interactive interpreter in asynchronous contexts.


## Installation

Use the package manager [pip](https://pypi.org/project/pip) to install asyncode:
```bash
pip install asyncode
```

### Dependencies

* Python **≥ 3.5** *(no CI for Python < 3.8)*



## Usage

This package's external API consists in two classes, **`AsyncInteractiveInterpreter`** and **`AsyncInteractiveConsole`**, which subclass respectively [`code.InteractiveInterpreter`](https://docs.python.org/3/library/code.html#interactive-interpreter-objects) and [`code.InteractiveConsole`](https://docs.python.org/3/library/code.html#interactive-console-objects).

These classes are meant to be used in **already running asynchronous contexts**. Minimal useful code will need to subclass provided classes to implement specific functions:

```py
import asyncode

class MyAsyncConsole(asyncode.AsyncInteractiveConsole):
    """AsyncInteractiveConsole adapted to running environment"""

    async def write(self, data):
        """Use specific function"""
        await some_output_coroutine(data)

    async def raw_input(self, prompt=""):
        """Use specific functions"""
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
        # Do not exit the whole program when sending "exit()" or "quit()"
        await some_output_coroutine("Bye!")
```

Read [the docs](https://asyncode.readthedocs.io) for more informations.



## Contributing

Pull requests are welcome. Do not hesitate to get in touch with me (see below) for any question or suggestion about this project!



## License

This work is shared under [the MIT license](LICENSE).

© 2020 Loïc Simon ([loic.simon@espci.org](mailto:loic.simon@espci.org))
