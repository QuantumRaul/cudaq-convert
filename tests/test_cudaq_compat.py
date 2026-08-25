# ============================================================================ #
# Copyright (c) 2022 - 2026 NVIDIA Corporation & Affiliates.                   #
# All rights reserved.                                                         #
#                                                                              #
# This source code and the accompanying materials are made available under     #
# the terms of the Apache License 2.0 which accompanies this distribution.     #
# ============================================================================ #
"""Compatibility smoke test for the CUDA-Q integration surface.

`cudaq-convert` is released independently of CUDA-Q, so nothing but this module
keeps the two in step. It pins down the entire surface the package depends on —
`make_kernel`, the builder methods the translators drive, and the
`SampleResult` accessors the README documents — so an incompatible CUDA-Q
release fails here, in one obvious place, instead of somewhere deep inside a
translator.

`pyproject.toml` declares a floor (`cudaq>=0.14.2`) rather than a pinned
window: newer CUDA-Q releases are expected to keep working, and this module is
what tells you when one stops. If a release breaks something here, adapt the
translators; if the old behaviour is not worth supporting, raise the floor.
"""

import importlib.metadata
import pathlib
import re

import pytest
from packaging.requirements import Requirement
from packaging.version import InvalidVersion, Version

from qiskit import QuantumCircuit

import cudaq
from cudaq import make_kernel

import cudaq_convert
from cudaq_convert import from_qasm_str, from_qiskit

# --------------------------------------------------------------------------- #
# The integration surface
# --------------------------------------------------------------------------- #

# Every kernel-builder method the translators call. Together with `make_kernel`
# this is the whole CUDA-Q API the package uses at runtime.
# `test_source_calls_nothing_undeclared` keeps this list honest.
BUILDER_METHODS = frozenset({
    # Allocation, measurement, reset
    'qalloc',
    'mz',
    'reset',
    # Paulis and 1-qubit Cliffords
    'x',
    'y',
    'z',
    'h',
    's',
    'sdg',
    't',
    'tdg',
    # Rotations and phases
    'rx',
    'ry',
    'rz',
    'r1',
    'u3',
    # Controlled variants
    'ch',
    'cx',
    'cy',
    'cz',
    'cs',
    'cr1',
    'crx',
    'cry',
    'crz',
    'cu3',
    # Swaps
    'swap',
    'cswap',
})

# `SampleResult` members the README documents and the test suite relies on.
SAMPLE_RESULT_MEMBERS = (
    'count',
    'probability',
    'most_probable',
    'expectation',
    'get_marginal_counts',
    'dump',
)

# Distributions that can provide the `cudaq` module. `cudaq` is a meta-package
# that resolves to one of the concrete wheels at install time; CI installs
# `cuda-quantum-cu12` directly because the meta-package's CUDA autodetection
# has no GPU to find on a hosted runner.
CUDAQ_DISTRIBUTIONS = (
    'cudaq',
    'cuda-quantum-cu12',
    'cuda-quantum-cu13',
    'cuda-quantum',
)

# Matches `kernel.foo(`, `self.kernel.foo(` and the `k.foo(` form used by the
# lambdas in `_GATE_HANDLERS`.
_BUILDER_CALL = re.compile(r'\b(?:self\.kernel|kernel|k)\.([A-Za-z_]\w*)\s*\(')

BELL_QASM2 = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0], q[1];
"""

BELL_QASM3 = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""


def _installed_cudaq_version():
    """Return the installed CUDA-Q version, or `None` if undeterminable."""
    for distribution in CUDAQ_DISTRIBUTIONS:
        try:
            return Version(importlib.metadata.version(distribution))
        except (importlib.metadata.PackageNotFoundError, InvalidVersion):
            continue
    # Fall back to the module attribute, which may carry a descriptive suffix.
    match = re.search(r'\d+\.\d+(?:\.\d+)*', str(getattr(cudaq, '__version__',
                                                         '')))
    return Version(match.group()) if match else None


def _declared_cudaq_requirement():
    """Return the `cudaq` requirement declared in `pyproject.toml`.

    Read back from the installed metadata so the test and the package agree on
    a single source of truth. Returns `None` when `cudaq-convert` itself is not
    installed (e.g. running straight from a source checkout).
    """
    try:
        requires = importlib.metadata.requires('cudaq-convert') or ()
    except importlib.metadata.PackageNotFoundError:
        return None
    for raw in requires:
        requirement = Requirement(raw)
        if requirement.name == 'cudaq':
            return requirement
    return None


@pytest.fixture(scope='module')
def declared_requirement():
    requirement = _declared_cudaq_requirement()
    if requirement is None:
        pytest.skip('cudaq-convert is not installed; no metadata to read the '
                    'declared CUDA-Q range from')
    return requirement


# --------------------------------------------------------------------------- #
# The declared version range
# --------------------------------------------------------------------------- #


class TestDeclaredVersionRange:
    """The range in `pyproject.toml` must describe what is installed."""

    def test_range_declares_a_lower_bound(self, declared_requirement):
        operators = {spec.operator for spec in declared_requirement.specifier}
        assert operators & {'>=', '>', '=='}, (
            'the `cudaq` dependency declares no lower bound; pin the oldest '
            'CUDA-Q this package is known to work with')

    def test_installed_cudaq_is_within_the_range(self, declared_requirement):
        version = _installed_cudaq_version()
        if version is None:
            pytest.skip('could not determine the installed CUDA-Q version')
        assert declared_requirement.specifier.contains(version,
                                                       prereleases=True), (
            f'CUDA-Q {version} is installed but cudaq-convert declares support '
            f'for cudaq{declared_requirement.specifier}. Install a supported '
            f'version, or adjust the declaration in pyproject.toml if this one '
            f'is meant to be supported.')


# --------------------------------------------------------------------------- #
# The kernel-builder API
# --------------------------------------------------------------------------- #


class TestIntegrationSurface:
    """`make_kernel` and the builder methods the translators drive."""

    def test_make_kernel_builds_a_kernel(self):
        kernel = make_kernel()
        assert kernel is not None
        assert kernel.qalloc(1) is not None

    @pytest.mark.parametrize('method', sorted(BUILDER_METHODS))
    def test_builder_exposes_method(self, method):
        kernel = make_kernel()
        assert callable(getattr(kernel, method, None)), (
            f'the CUDA-Q kernel builder no longer exposes `{method}`, which '
            f'the gate handlers call')

    def test_source_calls_nothing_undeclared(self):
        """`BUILDER_METHODS` must match what the package actually calls."""
        source_dir = pathlib.Path(cudaq_convert.__file__).parent
        called = set()
        for path in sorted(source_dir.glob('*.py')):
            called |= set(
                _BUILDER_CALL.findall(path.read_text(encoding='utf-8')))

        undeclared = called - BUILDER_METHODS
        assert not undeclared, (
            f'these builder calls are missing from BUILDER_METHODS: '
            f'{sorted(undeclared)}. Add them (or rename the local variable if '
            f'the scan picked up something that is not a kernel).')

        stale = BUILDER_METHODS - called
        assert not stale, (
            f'BUILDER_METHODS lists methods no longer called by the package: '
            f'{sorted(stale)}. Drop them so the surface stays accurate.')

    def test_controlled_gates_accept_a_list_of_controls(self):
        """`_mcx` and `_mcp` rely on passing several controls at once."""
        kernel = make_kernel()
        q = kernel.qalloc(3)
        kernel.x(q[0])
        kernel.x(q[1])
        kernel.cx([q[0], q[1]], q[2])
        counts = cudaq.sample(kernel, shots_count=100)
        assert counts['111'] == 100


# --------------------------------------------------------------------------- #
# `SampleResult`
# --------------------------------------------------------------------------- #


class TestSampleResultApi:
    """The `SampleResult` accessors documented in the README."""

    @pytest.fixture
    def counts(self):
        kernel = make_kernel()
        q = kernel.qalloc(1)
        kernel.x(q[0])
        return cudaq.sample(kernel, shots_count=100)

    def test_membership_and_indexing(self, counts):
        assert '1' in counts
        assert '0' not in counts
        assert counts['1'] == 100

    @pytest.mark.parametrize('member', SAMPLE_RESULT_MEMBERS)
    def test_member_exists(self, counts, member):
        assert callable(getattr(counts, member, None)), (
            f'`SampleResult.{member}` is documented in the README but is no '
            f'longer available')

    def test_count_and_probability(self, counts):
        assert counts.count('1') == 100
        assert counts.probability('1') == pytest.approx(1.0)
        assert counts.most_probable() == '1'


# --------------------------------------------------------------------------- #
# End to end through both public entry points
# --------------------------------------------------------------------------- #


class TestEndToEnd:
    """A Bell state through every entry point, all the way to sampled counts."""

    def _assert_bell(self, kernel):
        counts = cudaq.sample(kernel, shots_count=1000)
        assert '00' in counts
        assert '11' in counts
        assert '01' not in counts
        assert '10' not in counts
        assert counts['00'] + counts['11'] == 1000

    def test_from_qasm_str_qasm2(self):
        self._assert_bell(from_qasm_str(BELL_QASM2))

    def test_from_qasm_str_qasm3(self):
        self._assert_bell(from_qasm_str(BELL_QASM3))

    def test_from_qiskit(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        self._assert_bell(from_qiskit(qc))
