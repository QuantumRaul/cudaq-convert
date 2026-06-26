# cudaq-contrib

Interoperability helpers for [CUDA-Q](https://github.com/NVIDIA/cuda-quantum):
convert **OpenQASM 2.0 / 3.0** and **Qiskit** circuits into CUDA-Q kernels.

This package is developed and released **independently** of the core CUDA-Q
repository. It takes a dependency on `cuda-quantum` and installs on top of it,
so framework integrations can evolve on their own cadence without coupling to
CUDA-Q's release cycle.

## Installation

```bash
pip install cudaq-contrib            # OpenQASM support (no Qiskit needed)
pip install cudaq-contrib[qiskit]    # adds Qiskit conversion
```

## Usage

```python
import cudaq
from cudaq_contrib import from_qasm, from_qasm_str, from_qiskit

# OpenQASM 2.0 / 3.0 — native parser, no Qiskit dependency
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

## Testing

```bash
pip install -e .[test]
pytest
```

> **Note:** on CPU-only machines, export `CUDAQ_DEFAULT_SIMULATOR=qpp-cpu`
> before running the tests so `import cudaq` doesn't try to initialize a GPU
> context.

## License

Apache License 2.0.
