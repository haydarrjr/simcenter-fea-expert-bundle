"""Compare synthetic SRS, external superelement and NVH outputs to independent references."""
import argparse
from math import isclose, pi, sqrt
from pathlib import Path
import json
import re


def finished(path):
    logs = path.with_suffix(".log").read_text(encoding="ascii", errors="replace")
    text = path.read_text(encoding="ascii", errors="replace")
    if not re.search(r"Analysis complete[ \t]+0[ \t]*$", logs, re.MULTILINE):
        raise ValueError(f"{path}: no successful terminal job")
    if "END OF JOB" not in text or re.search(r"\bFATAL\s+MESSAGE\b", text):
        raise ValueError(f"{path}: F06 completion or fatal check failed")
    return text


def roots(text):
    section = text.split("R E A L   E I G E N V A L U E S")
    if len(section) != 2:
        raise ValueError("expected one real eigenvalue table")
    return [float(x) for x in re.findall(r"^\s+\d+\s+\d+\s+([+-]?\d\.\d+E[+-]\d+)\s", section[1].split("\n1 ", 1)[0], re.M)]


def external(full, reduced):
    # Characteristic polynomial of the full two-mass stiffness and mass matrices.
    trace = 5000 / 2 + (5000 + 12000)
    determinant = 5000 * 12000 / 2
    delta = sqrt(trace**2 - 4 * determinant)
    expected = [(trace - delta) / 2, (trace + delta) / 2]
    observed = [roots(finished(path)) for path in (full, reduced)]
    if any(len(row) != 2 or not all(isclose(a, b, rel_tol=1e-6) for a, b in zip(row, expected)) for row in observed):
        raise ValueError(f"external superelement result disagrees with full/analytic solution: {observed}")
    return {"roots": observed, "reference": expected}


def transfer(text):
    blocks = re.split(r"^0\s+SUBCASE\s+([1-3])\s*$", text, flags=re.MULTILINE)
    results = {}
    for case, chunk in zip(blocks[1::2], blocks[2::2]):
        if "C O M P L E X   D I S P L A C E M E N T" not in chunk:
            continue
        if "FREQUENCY =  1.200000E+01" not in chunk or "(REAL/IMAGINARY)" not in chunk:
            raise ValueError("unexpected frequency or convention")
        pattern = r"^0\s+([123])\s+G\s+([-\d.E+]+)[^\n]*\n\s+([-\d.E+]+)\s"
        table = [(int(n), complex(float(r), float(i))) for n,r,i in re.findall(pattern, chunk, re.M)]
        if [n for n,_ in table] != [1,2,3] or int(case) in results:
            raise ValueError("ambiguous transfer rows")
        results[int(case)] = [value for _,value in table]
    if sorted(results) != [1,2,3]:
        raise ValueError("three cases required")
    return results


def nvh(path):
    h1, h2, observed = transfer(finished(path)).values()
    determinant = h1[0]*h2[1] - h1[1]*h2[0]
    if abs(determinant) < 1e-12:
        raise ValueError("unobservable load mapping")
    f1 = (observed[0]*h2[1]-observed[1]*h2[0])/determinant
    f2 = (h1[0]*observed[1]-h1[1]*observed[0])/determinant
    if max(abs(f1-complex(3,1)),abs(f2-complex(-2,2))) > 1e-4:
        raise ValueError("incorrect inverse loads")
    paths = [h1[2]*f1, h2[2]*f2]
    error = abs(sum(paths)-observed[2])/abs(observed[2])
    if error > 1e-5:
        raise ValueError("held-out transfer path reconstruction failed")
    # A positive-definite synthetic Hermitian CSD with a non-real off-diagonal term.
    s11, s22, s12 = 4., 2., 1.+1.j
    mean = (s11+s22)/2
    radius = sqrt(((s11-s22)/2)**2 + abs(s12)**2)
    lambdas = [mean+radius,mean-radius]
    a,b = h1[2],h2[2]
    direct = s11*abs(a)**2+s22*abs(b)**2+2*(a*s12*b.conjugate()).real
    modal = []
    for lam in lambdas:
        v0,v1=s12,lam-s11
        modal.append(lam*abs(a*v0+b*v1)**2/(abs(v0)**2+abs(v1)**2))
    if not isclose(direct, sum(modal), rel_tol=1e-12):
        raise ValueError("PCA output spectral power did not close")
    return {"inverse_load_error":max(abs(f1-complex(3,1)),abs(f2-complex(-2,2))),
            "held_out_relative_error":error,"receiver_path_amplitudes":[abs(x) for x in paths],
            "pca_eigenvalues":lambdas,"receiver_power":direct}


def oscillator_peak(samples, step, frequency, damping):
    """Substep RK4 on the sampled, piecewise linear base acceleration."""
    omega = 2*pi*frequency
    stiffness = omega**2
    damper = 2*damping*omega
    x = v = maximum = 0.
    subdivisions = 2
    h = step/subdivisions
    def accel(position, velocity, ground):
        return -stiffness*position-damper*velocity-ground
    for prev, next_ in zip(samples,samples[1:]):
        for j in range(subdivisions):
            left = prev + (next_-prev)*j/subdivisions
            right = prev + (next_-prev)*(j+1)/subdivisions
            middle = (left+right)*0.5
            v1,a1=v,accel(x,v,left)
            v2=v+h*a1/2
            a2=accel(x+h*v1/2,v2,middle)
            v3=v+h*a2/2
            a3=accel(x+h*v2/2,v3,middle)
            v4=v+h*a3
            a4=accel(x+h*v3,v4,right)
            x += h*(v1+2*v2+2*v3+v4)/6
            v += h*(a1+2*a2+2*a3+a4)/6
            maximum=max(maximum,abs(-stiffness*x-damper*v))
    return maximum


def srs(path):
    data=json.loads(path.read_text(encoding="utf-8"))
    pulse,spectrum=data["input.afu"],data["srs.afu"]
    frequencies=[spectrum["first"]+spectrum["step"]*i for i in range(spectrum["count"])]
    if frequencies != list(range(5,56,5)) or pulse["count"]!=len(pulse["values"]):
        raise ValueError("unexpected SRS input or frequency grid")
    reference=[oscillator_peak(pulse["values"],pulse["step"],f,.05) for f in frequencies]
    errors=[abs(a-b)/b for a,b in zip(spectrum["values"],reference,strict=True)]
    if max(errors)>0.01:
        raise ValueError(f"absolute acceleration SRS error {max(errors)}")
    return {"points":len(frequencies),"maximum_relative_error":max(errors)}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("full","reduced","transfer","spectrum"):
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    print(json.dumps({"se":external(args.full,args.reduced),"nvh":nvh(args.transfer),
                      "srs":srs(args.spectrum)},indent=2))
