"""Bind FEA operations to an existing official MCP client and its catalog."""
import asyncio
import json
from weakref import WeakKeyDictionary

from fea_controller import digest, execute_one


_LOCKS = WeakKeyDictionary()
IDENTITY_KEYS = ('session', 'release', 'owner', 'model')


class OfficialMcpAdapter:
    """Reuse the host transport and the FEA controller's operation policy."""

    def __init__(self, session, profile, catalog, observed_target, evidence_ref):
        if not evidence_ref or any(not observed_target.get(k) for k in (*IDENTITY_KEYS, 'revision')):
            raise ValueError('fresh host and model identity evidence is required')
        self.session = session
        self.profile = profile
        self.identity = {k: observed_target[k] for k in IDENTITY_KEYS}
        # Preserve the descriptors observed at binding time.
        self.catalog = json.loads(json.dumps(catalog))
        self.catalog_digest = digest(self.catalog)
        self.lock = _LOCKS.setdefault(session, asyncio.Lock())

    async def execute_chain(self, controller, steps, readback):
        """Each async step factory receives the preceding accepted receipt."""
        receipts = []
        async with self.lock:
            for build in steps:
                predecessor = receipts[-1] if receipts else None
                operation, target_evidence, authorization = await build(predecessor)
                operation = dict(operation)
                if predecessor:
                    dependency = predecessor['request']['operation_id']
                    if dependency not in operation.get('depends_on', ()):
                        raise ValueError('successor must explicitly depend on the preceding operation')
                target = operation['target']
                if (any(target.get(k) != v for k, v in self.identity.items())
                        or operation['profile'] != self.profile):
                    raise ValueError('operation differs from the bound session or profile')
                entries = [t for t in self.catalog if t.get('name') == operation['tool']]
                if len(entries) != 1:
                    raise ValueError('tool is absent or ambiguous in the current catalog')
                binding = dict(profile=self.profile, target=target, schema=entries[0],
                               evidence_ref=target_evidence, catalog_digest=self.catalog_digest)
                receipt = await execute_one(controller, operation, binding, self._invoke,
                                            readback, authorization)
                receipts.append(receipt)
                if receipt['status'] != 'ACCEPTED':
                    break
        return receipts

    @staticmethod
    async def execute_operation(controller, operation, binding, session, preflight, readback, authority=None):
        """Use an already-authorized programmatic host session with the v1 ledger."""
        async with _LOCKS.setdefault(session, asyncio.Lock()):
            prepared = controller.transition("prepare", operation=operation, binding=binding, authority=authority)
            names = {key: operation[key] for key in ("run_id", "operation_id")}
            witness = await preflight(operation) if prepared["effect"] != "PURE_READ" else None
            controller.transition("reserve", **names, request_digest=prepared["request_digest"],
                                  binding=binding, authority=authority, preflight=witness)
            try:
                reply = await session.call_tool(binding["tool"], arguments=operation["args"])
                raw = reply if isinstance(reply, dict) else reply.model_dump(mode="json", by_alias=True)
            except BaseException as exc:
                controller.transition("record", **names, transport_error=str(exc)[:4096] or type(exc).__name__)
                raise
            receipt = controller.transition("record", **names, raw=raw)
            if receipt["status"] == "READ_FAILED":
                return receipt
            observation = await readback(operation)
            return controller.transition("observe", **names, observation=observation)

    async def _invoke(self, profile, tool, arguments):
        reply = await self.session.call_tool(tool, arguments=arguments)
        return reply if isinstance(reply, dict) else reply.model_dump(mode='json', by_alias=True)
