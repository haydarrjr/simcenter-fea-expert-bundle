"""Check the three-frequency synthetic Hermes Load Identification, TPA and PCA outputs."""

import argparse
import json
from math import isclose, pi, sqrt
from pathlib import Path


FREQUENCIES = [10.0, 12.0, 14.0]
LOADS = (3.0 + 1j, -2.0 + 2j)


def receiver_transfers(frequency):
    """Use cofactors of the three-DOF dynamic stiffness for the held-out receiver."""
    omega = 2 * pi * frequency
    a = 24000 - omega**2 + 7j * omega
    b = 19000 - 1.5 * omega**2 + 9j * omega
    c = 24000 - 2 * omega**2 + 11j * omega
    determinant = a * (b * c - 11000**2) - 8000**2 * c
    return 8000 * 11000 / determinant, a * 11000 / determinant


def legend(dataset, term):
    matches = [dataset.file[ref] for ref in dataset.attrs['LEGENDS']
               if dataset.file[ref].name.endswith('_' + term)]
    if len(matches) != 1:
        raise ValueError(f'{dataset.name} must have one {term} legend')
    return matches[0][...]


def require_grid(dataset):
    if legend(dataset, 'Frequency').tolist() != FREQUENCIES:
        raise ValueError(f'{dataset.name} has an unexpected frequency grid')


def require_close(actual, expected, *, rel_tol=1e-10, abs_tol=1e-12):
    if not isclose(abs(actual - expected), 0.0, abs_tol=max(abs_tol, rel_tol * abs(expected))):
        raise ValueError(f'expected {expected!r}, observed {actual!r}')


def verify_live(path, forces, paths, virtual, receiver):
    curves = json.loads(path.read_text(encoding='utf-8'))
    expected = {
        'load1': ('Force', forces[:, 0], 1e3),
        'load2': ('Force', forces[:, 1], 1e3),
        'total': ('Displacement', paths[0], 1e3),
        'path1': ('Displacement', paths[1], 1e3),
        'path2': ('Displacement', paths[2], 1e3),
        'virtual1': ('Acceleration_cross_Acceleration', virtual[0], 1e6),
        'virtual2': ('Acceleration_cross_Acceleration', virtual[1], 1e6),
        'pca_receiver1': ('Acceleration', receiver[0], 1e3),
        'pca_receiver2': ('Acceleration', receiver[1], 1e3),
    }
    if curves.keys() != expected.keys():
        raise ValueError('live receipt has missing or unexpected curves')
    for name, (quantity, reference, scale) in expected.items():
        actual_quantity, grid, points = curves[name]
        if actual_quantity != quantity or grid != FREQUENCIES:
            raise ValueError(f'{name} has an unexpected live quantity or frequency grid')
        for pair, value in zip(points, reference, strict=True):
            expected_value = value if isinstance(value, complex) else complex(*value)
            require_close(complex(*pair) / scale, expected_value)
    return len(expected)


def verify(load_file, path_files, pca_file, live=None):
    import h5py  # Optional verification dependency for Hermes SC_H5 artifacts.

    load_error = 0.0
    with h5py.File(load_file) as source:
        loads = source['FORCES']
        require_grid(loads)
        if legend(loads, 'Nodes').tolist() != [1, 2] or loads.shape != (3, 2, 1):
            raise ValueError('operational force node, case or axis identity mismatch')
        if source['SVD_DATA_FORCES/RANKS'][...].tolist() != [[2, 2, 2]]:
            raise ValueError('the inverse problem lost rank')
        force_rows = loads[...][:, :, 0, 0, :]
        for row in force_rows:
            for pair, expected in zip(row, LOADS, strict=True):
                actual = complex(*pair)
                require_close(actual, expected, abs_tol=3e-5)
                load_error = max(load_error, abs(actual - expected))

    transfers = []
    for number, path in enumerate(path_files):
        with h5py.File(path) as source:
            response = source[f'PATH{number}']
            require_grid(response)
            if legend(response, 'Nodes').tolist() != [(3, 2)] or response.shape != (1, 1, 3):
                raise ValueError('TPA receiver, case or axis identity mismatch')
            transfers.append([complex(*value) for value in response[...][0, 0, :, 0, :]])
    receiver_error = 0.0
    for frequency, total, first, second in zip(FREQUENCIES, *transfers, strict=True):
        direct_paths = [h * f for h, f in zip(receiver_transfers(frequency), LOADS, strict=True)]
        for actual, expected in zip((first, second), direct_paths, strict=True):
            require_close(actual, expected, rel_tol=3e-5)
        require_close(first + second, total)
        expected_total = sum(direct_paths)
        require_close(total, expected_total, rel_tol=3e-5)
        receiver_error = max(receiver_error, abs(total - expected_total) / abs(expected_total))

    a, b = 2 - 1j, 0.5 + 0.25j
    reference_power = 4 * abs(a)**2 + 2 * abs(b)**2 + 2 * (a * (1 + 1j) * b.conjugate()).real
    with h5py.File(pca_file) as source:
        singular = source['PCA_SVD_DATA/SINGULARVALUES']
        virtual = source['VIRTUAL_REFERENCE_AUTOPOWER']
        response = source['REFERENCED_VIRTUAL_SPECTRA']
        for dataset in (singular, virtual, response):
            require_grid(dataset)
        if (singular.shape != (1, 2, 3) or virtual.shape != (1, 2, 3)
                or response.shape != (2, 3, 3)):
            raise ValueError('unexpected PCA result shape')
        if (legend(response, 'Nodes')['NodeId'].tolist() != [1, 2, 3]
                or legend(response, 'Loadcase')['Name'].tolist() != [b'Principal Component 1', b'Principal Component 2']
                or source['PCA_SVD_DATA/RANKS'][...].tolist() != [[2, 2, 2]]):
            raise ValueError('PCA receiver, principal-component or rank identity mismatch')
        receiver = response[...][:, 2, :, 0, :]
        virtual_power = virtual[...][0, :, :, 2, :]
        for i, scale in enumerate((1, 2, 3)):
            for j, expected in enumerate((3 + sqrt(3), 3 - sqrt(3))):
                require_close(singular[0, j, i], expected * scale)
                require_close(complex(*virtual_power[j, i]), expected * scale)
            require_close(sum(abs(complex(*v))**2 for v in receiver[:, i]), reference_power * scale)

    report = {'load_max_abs_error_n': load_error, 'tpa_receiver_max_relative_error': receiver_error,
              'pca_principal_powers_at_10_hz': [3 + sqrt(3), 3 - sqrt(3)],
              'pca_receiver_power_at_10_hz': reference_power}
    if live is not None:
        report['live_curve_count'] = verify_live(live, force_rows, transfers, virtual_power, receiver)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('loads', 'total_response', 'path_one', 'path_two', 'pca'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--live', type=Path, help='complex curves in the verified metric SIM units')
    args = parser.parse_args()
    print(json.dumps(verify(args.loads, (args.total_response, args.path_one, args.path_two), args.pca, args.live),
                     indent=2))
