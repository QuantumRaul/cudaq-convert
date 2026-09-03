# cudaq-convert

Interoperability helpers for [CUDA-Q](https://github.com/NVIDIA/cuda-quantum):
convert **OpenQASM 2.0 / 3.0** and **Qiskit** circuits into CUDA-Q kernels.

This package is developed and released **independently** of the core CUDA-Q
repository. It takes a dependency on `cudaq` and installs on top of it.

## Who is this for

Researchers and developers who already have quantum circuits expressed in
**OpenQASM 2.0/3.0** or built with **Qiskit** and want to run, simulate, or
extend them on **CUDA-Q** — without hand-rewriting each circuit as a CUDA-Q
kernel.

> **Platform:** CUDA-Q ships Linux wheels only, so this package runs on **Linux
> or WSL** with **Python 3.11–3.13**. It is not importable on bare Windows.

## Installation

```bash
pip install cudaq-convert
```

This installs everything both conversion paths need, so `from_qasm`,
`from_qasm_str`, and `from_qiskit` all work straight away.

### Compatibility

| | Supported |
| --- | --- |
| CUDA-Q | `cudaq >= 0.14.2` |
| Python | 3.11 – 3.13 |
| Qiskit | `>= 1.0` |
| OpenQASM | 2.0, 3.0 |

## Usage

```python
import cudaq
from cudaq_convert import from_qasm, from_qasm_str, from_qiskit

# From a OpenQASM 2.0 / 3.0 string
kernel = from_qasm_str("""
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0], q[1];
""")
print(cudaq.sample(kernel))

# From a file
kernel = from_qasm("circuit.qasm")

# From a Qiskit QuantumCircuit
from qiskit import QuantumCircuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
kernel = from_qiskit(qc)
```

## Public API

| Function | Description |
| --- | --- |
| `from_qasm(path)` | Parse an OpenQASM 2.0/3.0 file into a CUDA-Q kernel. |
| `from_qasm_str(source)` | Parse OpenQASM 2.0/3.0 source text. Dispatches on the `OPENQASM <version>;` header. |
| `from_qiskit(circuit)` | Convert a Qiskit `QuantumCircuit` into a CUDA-Q kernel. |

## Feature coverage

- **OpenQASM 2.0:** full `qelib1.inc` gate set, user-defined `gate` blocks with
  recursive expansion, register broadcasting, `measure`/`reset`/`barrier`/`opaque`.
- **OpenQASM 3.0:** `qubit[N]`/`bit[N]` declarations, `c = measure q;`
  assignment, built-in `U(...)`/`gphase`, legacy uppercase `CX`/`I`,
  `include "stdgates.inc";`.
- **Qiskit:** full standard gate library, with recursive `definition` fallback
  for custom/composite gates.

## Known limitations

- **Not yet implemented** (these raise `NotImplementedError`):
  - QASM3 gate modifiers: `ctrl @`, `negctrl @`, `inv @`, `pow(n) @`.
  - Classical control and typed declarations / subroutines (`if`, `for`,
    `while`, `def`, `input`/`output`, `int`/`float`/`angle`, …). This includes
    OpenQASM 2.0's `if (c==N) gate q;`, which is legal 2.0 syntax.
- **Endianness:** CUDA-Q counts are big-endian (q0 is the leftmost bit) while
  Qiskit is little-endian; reverse the bitstring when comparing across the two.
- **Phase-only gates** (`rz`, `cz`, `cp`, `s`, `t`, global phase, `gphase`,
  `u0`) are unobservable in Z-basis sampling.
- **Platform:** Linux/WSL only, Python 3.11–3.13 (inherited from CUDA-Q).

## Testing

```bash
pip install -e .[test]
pytest
```

> **Note:** on CPU-only machines, export `CUDAQ_DEFAULT_SIMULATOR=qpp-cpu`
> before running the tests so `import cudaq` doesn't try to initialize a GPU
> context.

## Contributing

Contributions are welcome — see
[CONTRIBUTING.md](https://github.com/QuantumRaul/cudaq-convert/blob/main/CONTRIBUTING.md)
for the
development setup, test instructions, and coding conventions. By participating
you agree to the
[Code of Conduct](https://github.com/QuantumRaul/cudaq-convert/blob/main/CODE_OF_CONDUCT.md).

## Security

To report a security vulnerability, follow
[SECURITY.md](https://github.com/QuantumRaul/cudaq-convert/blob/main/SECURITY.md). **Do not**
open a public GitHub issue for security reports.

## License

Apache License 2.0 — see
[LICENSE](https://github.com/QuantumRaul/cudaq-convert/blob/main/LICENSE).
