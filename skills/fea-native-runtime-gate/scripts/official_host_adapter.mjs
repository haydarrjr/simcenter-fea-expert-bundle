// Existing host tool dictionary binding. The caller owns the CLI and evidence-file transport.
const busy = new WeakMap();
const identityKeys = ['session', 'release', 'owner', 'model'];

export function createOfficialHostAdapter({ tools, profile, catalog, toolKeys, target, evidenceRef, controller }) {
  if (!evidenceRef || ![...identityKeys, 'revision'].every(key => target?.[key])) {
    throw new Error('fresh host and model identity evidence is required');
  }
  const identity = Object.fromEntries(identityKeys.map(key => [key, target[key]]));
  const descriptors = JSON.parse(JSON.stringify(catalog));
  const locks = busy.get(tools) ?? new Set();
  busy.set(tools, locks);

  async function executeChain(builders, readback) {
    if (locks.has(identity.session)) throw new Error('session acceptance cycle already running');
    locks.add(identity.session);
    const receipts = [];
    try {
      for (const build of builders) {
        const previous = receipts.at(-1);
        const { operation, evidenceRef, authorization = null } = await build(previous);
        if (previous && !operation.depends_on?.includes(previous.request.operation_id)) {
          throw new Error('successor must explicitly depend on the preceding operation');
        }
        if (operation.profile !== profile || !identityKeys.every(key => operation.target?.[key] === identity[key])) {
          throw new Error('operation differs from the bound session or profile');
        }
        const entries = descriptors.filter(tool => tool.name === operation.tool);
        const invoke = tools[toolKeys[operation.tool]];
        if (entries.length !== 1 || typeof invoke !== 'function') {
          throw new Error('tool is absent or ambiguous in the current catalog');
        }
        const binding = {profile, target: operation.target, schema: entries[0], evidence_ref: evidenceRef};
        const prepared = await controller('prepare', {operation, binding, authorization});
        const name = operation.operation_id;
        const request = await controller('reserve', {name, binding, request_digest: prepared.request_digest});
        let raw;
        try {
          raw = await invoke(request.arguments);
        } catch (error) {
          await controller('record', {name, transport_error: String(error)});
          throw error;
        }
        await controller('record', {name, raw});
        const observation = await readback(request);
        const receipt = await controller('observe', {name, observation});
        receipts.push(receipt);
        if (receipt.status !== 'ACCEPTED') break;
      }
    } finally {
      locks.delete(identity.session);
    }
    return receipts;
  }
  return {executeChain};
}
