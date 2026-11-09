# Admit a real Runtime observation without losing ownership or physical identity

Contents: [evidence scope](#decide-what-evidence-the-engineering-task-actually-needs),
[discovery](#discover-before-deciding-whether-an-operation-can-run),
[identity and receipts](#bind-the-object-incarnation-then-consume-bounded-readback),
[worked case](#worked-flange-case-and-the-misleading-observation),
[recovery](#recover-without-repeating-an-uncertain-native-action),
[execution](#execute-and-interpret-the-source-demonstration).

## Decide what evidence the engineering task actually needs

Use session metadata to locate a session and check freshness; use qualified
part/result readers to establish engineering facts. A bolted-joint assessment
needs more than a CAD body count: FEM/SIM ownership, bolt and contact-region
membership, units, mesh revision, active step and effective load state must also
be grounded. If the available reader cannot obtain one of those facts, retain
that precise gap. Do not request a native mutation under a differently named
effect merely to make admission succeed.

The source implementation is `fea_agent.runtime_client`. Its default profile
is pinned to Runtime main `5c9238ea2daa628f58a683dd356983d3aefd65f6`, inspected
2026-10-28. It calls the existing `runtime.capabilities` and `inspect_session`
MCP tools. The optional qualified Java read profile is separately pinned to
unmerged PR23 `c601491790cfe54214efdd53d768cb75d66e207f`. That candidate is not
an installed capability. Current source profiles do not contain a qualified
FEM/SIM/mesh/solution/result handler or a CAE_MUTATION effect.

## Discover before deciding whether an operation can run

Use the embedding application's existing initialized MCP connection:

```python
from fea_agent.runtime_client import McpSessionTransport, RuntimeClient

async def inspect(runtime_session, session_id, revision, fingerprint):
    client = RuntimeClient(McpSessionTransport(runtime_session))
    inventory = await client.discover(page_size=2)
    session = await client.inspect_session(
        session_id, expected_revision=revision,
        expected_fingerprint=fingerprint,
    )
    admission = inventory.assess(
        effect="CAE_MUTATION", product="simcenter-3d", release="2606"
    )
    return session, admission
```

No endpoint, executable path or credential belongs in the engineering request.
The discovery input is `engineering-desktop.runtime-capabilities.input.v1`;
output is `engineering-desktop.runtime-capabilities.output.v2`. Metadata filters
are top-level MCP arguments. Each next page supplies the exact snapshot/query
digests returned with page one. The client detects changing snapshots, query
drift, duplicates, incomplete pagination and inline-schema hash mismatches.

Interpret a capability row's source, host-test, grant, build, license, native and
release axes separately. Main's five descriptive rows do not authorize any FEA
operation. The part-identity filter is specifically unsupported by that source
inventory: its zero-row UNVERIFIED result cannot prove that a target has no
features or that the requested part matched. Inspecting session metadata also
does not authenticate an engineering observation or supply a missing part
incarnation. A partial fingerprint cannot establish an unchanged full model.

## Bind the object incarnation, then consume bounded readback

The optional Java part/expression methods accept this exact target shape:

```json
{
  "identity_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "open_generation": "fem-incarnation-7",
  "model_revision": 19,
  "model_fingerprint_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
}
```

These are example bytes, not observed host evidence. Obtain the real generation
and fingerprint from the qualified owner. Names, paths and session tags cannot
exclude close/reopen or edit/undo ABA. For an expression, compare exact name,
owner, journal identifier and optional uint32 session tag; preserve the observed
formula and native unit status instead of evaluating the formula as Python.

The concrete optional calls are `java_inspect_part`, `java_inspect_expression`
and `java_session_status`; reconciliation uses `java_read_status`. Their response
schema is `engineering-desktop.nx2606-java-read-response.v1`. Require common
request/release/recipient/operation bindings and exact part state in BEFORE and
AFTER observations. AFTER must bind the complete BEFORE envelope and payload,
with a common exclusive interval, different stage challenges and valid bounded
time ordering. Require broker ACK and ownership flags. Hash consistency is
necessary but does not authenticate a signer or prove the physical interval.

Choose `source_fixture=True` only for source tests. Real host evidence requires
an embedding-owned `HostTrustBinding` and independently installed
`HostReceiptVerifier`. The latter validates signature authority, domain,
release/recipient, exact builds/license, physical interval and current or
retained-ACK custody, then returns `VerifiedHostReceipt` for the exact bytes and
expected target. Never decode this trust configuration from user JSON. A
server's `BROKER_AUTHENTICATED_HOST` string is insufficient by itself.

## Worked flange case and the misleading observation

Before pretensioning an eight-bolt flange, inspect the expected assembly at
revision 19. A response that reports 64 bodies and
`body_count_complete=false` looks usable as an assembly total. Reject it:
the real contract requires an incomplete count to be null. A prefix must not
become a total or evidence that all bolts/contact faces were found. The client
rejects this response before releasing model evidence. A valid incomplete
response still requires a different qualified reader for complete FEA region
membership.

Likewise, `bolt_preload = preload_base * thermal_factor` with N units does not
prove the effective bolt force in a locked thermal service step. Obtain the
actual solved step/deck/result evidence. Reject a response from another open
generation even if its name, tag and all recomputed hashes look consistent.

## Recover without repeating an uncertain native action

Supply an explicit filesystem `SQLiteReadLedger(path)` for every live Java
composition; omitted/memory ledgers are rejected. Retain the configured absolute
path across restart. It records the correlation and session hold before dispatch.
Persisted trust mode and complete source/host binding must match before status
dispatch: a restarted source-fixture client cannot clear a host hold. Changed
bindings and legacy records without trust context remain held. Runtime retains native ownership;
this client database is not a grant, writer lease or rollback-resistant trust
store. A new correlation ID cannot bypass an unresolved session hold.

If a read returns PENDING with request ID `11111111111111111111111111111111`,
call `client.reconcile(original_correlation_id)`. The only subsequent tool call
is `java_read_status` for that ID. A changed ID/digest or part state is rejected.
If transport fails before any request ID arrives, retain UNKNOWN_HELD and report
RECONCILIATION_HANDLE_UNAVAILABLE. The upstream handler mints IDs server-side;
the Runtime owner must reconcile that session. Do not invent an ID, replay the
getter, release someone else's owner or infer that cancellation prevented work.

## Execute and interpret the source demonstration

```sh
python -m fea_agent assess-runtime-contract examples/engineering_v2/runtime_contract_case.json
python -m unittest tests.test_runtime_client_v2 -v
```

The first command reports source compatibility and exact missing CAE capability,
not live discovery. The tests exercise actual main DTO fixtures through the
concrete MCP wrapper plus negative owner, receipt and restart cases. All native,
solver and engineering execution in these fixtures remains NOT_RUN.

Use the complete compatibility contract (source: fea_expert_agent_plugin/docs/architecture/runtime-compatibility.md)
for exact source links, schemas and native-owner dependencies, and the
injected-client example (source: fea_expert_agent_plugin/examples/engineering_v2/runtime_client_example.py)
for a reusable connection-facing function. The Runtime owns installed handlers;
verified .NET CAE recipes cannot be executed through a Java CAD read-only scope.
