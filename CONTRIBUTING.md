# Contributing to cudaq-convert

Thanks for your interest in improving `cudaq-convert`! This project provides
OpenQASM 2.0/3.0 and Qiskit → CUDA-Q circuit translation. Contributions of bug
reports, tests, documentation, and new gate/feature/sdk coverage are all welcome.

By participating in this project you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting bugs and requesting features

Use [GitHub Issues](https://github.com/cudaq-community/cudaq-convert/issues).
For a bug, please include a minimal OpenQASM/Qiskit snippet that reproduces the
problem, the expected CUDA-Q behavior, and what you got instead. For security
issues, **do not** open a public issue — follow [SECURITY.md](SECURITY.md).

## Development setup

CUDA-Q ships Linux wheels only, so develop and test on **Linux or WSL** . Use Python **3.11–3.13** and
**`cudaq >= 0.14.2`**.

```bash
python3.12 -m venv ~/venvs/cudaq-convert   # keep the venv outside OneDrive/mnt
source ~/venvs/cudaq-convert/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt        # cudaq + numpy + qiskit + pytest
pip install -e . --no-deps                 # install cudaq-convert (editable)
```

`cudaq` is a meta-package that autodetects the host CUDA and resolves to a
concrete wheel. If that detection fails (no GPU, or an unsupported toolkit),
install the wheel directly instead — `pip install "cuda-quantum-cu12>=0.14.2"`
— which bundles the CPU simulator and needs no GPU. See
[requirements-dev.txt](requirements-dev.txt) for the rest of the environment
caveats.

## Running the tests

```bash
export CUDAQ_DEFAULT_SIMULATOR=qpp-cpu   # force the CPU simulator on no-GPU hosts
pytest -q                                # all tests
pytest tests/test_from_qasm.py -v        # a single module
pytest -k bell -v                        # a single scenario
pytest tests/test_cudaq_compat.py -v     # just the CUDA-Q compatibility check
```

> **After a CUDA-Q upgrade,** run `tests/test_cudaq_compat.py` first. It checks
> the installed version against what `pyproject.toml` declares and asserts every
> kernel-builder method the translators call still exists, so a broken CUDA-Q
> release reports itself there instead of as a pile of unrelated failures.

> **Endianness:** CUDA-Q counts are big-endian (q0 is the leftmost bit) while
> Qiskit is little-endian. All bitstring assertions in the tests follow CUDA-Q's
> big-endian convention — keep new tests consistent with that.

## Submitting changes

1. Fork the repository and create a topic branch off `main`.
2. Make your change, keeping the public API (`from_qasm`, `from_qasm_str`,
   `from_qiskit`) stable unless the change is intentional and documented.
3. Add or update tests covering your change. New gate handlers should have a
   sampling-based test asserting the expected computational-basis outcome.
4. Ensure the full test suite passes locally.
5. Open a pull request against `main` with a clear description of the change and
   its motivation. CI must pass before review.

### The only CUDA-Q dependency is the public API

The sole integration surface with CUDA-Q is `from cudaq import make_kernel`. Do
**not** reach into CUDA-Q internals — keeping to the public API is what lets this
package evolve independently of the core release cycle. New source-format
support should reuse the shared `_GATE_HANDLERS` table so the QASM and Qiskit
translators stay in lockstep on gate semantics.

## Code style

- **Formatting:** yapf with Google style, matching CUDA-Q conventions.
- **License header:** keep the Apache-2.0 header on every Python source file.
- **Unsupported features:** raise `NotImplementedError` with a clear message
  rather than silently no-op'ing (see the QASM3 gate modifiers). Do not silently
  drop instructions.

## License

By contributing, you agree that your contributions will be licensed under the
[Apache License 2.0](LICENSE).
