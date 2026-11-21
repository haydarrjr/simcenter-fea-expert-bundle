# Designcenter journal execution

| Route | Input and witness |
|---|---|
| Snippet sandbox | `nxopen_python_snippet` contains plain statements. The observed profile binds `theSession` and `workPart`. Inspect the expected stdout or scoped system-log witness. |
| Journal sandbox | `python_code` defines `main()` and calls it from the `if __name__ == '__main__'` entry point. Verify any argument forwarding and emit the result to stdout. |
| Live execute | `python_code` defines `main(args)` and returns an observation. On 2612.1700, omit envelope `args` when inputs can be bound in the audited payload. `print` is outside the live return contract. |

Check native execution status inside the response. Builders use the appropriate commit method and are destroyed in `finally`. Treat reflective features and standard-library imports as unavailable in the restricted live runner unless the current runtime explicitly admits them. Use the [native runtime gate](../../fea-native-runtime-gate/SKILL.md) for effects.

## Empty sandbox stdout

Designcenter 2612.1700 has returned exit 0 and empty stdout. Generate a new 128-bit hex nonce and write `FEA_SANDBOX_PASS:<nonce>` with `NXOpen.Session.GetSession().LogFile.WriteLine(...)` only after the assertion. Capture the exact worker PID and its system log while the call is active, then apply [verify_sandbox_syslog.py](../scripts/verify_sandbox_syslog.py) to the original MCP capture, log, PID and nonce. Report system-log evidence and MCP output state with their respective scope.

[Siemens standard output guidance](https://docs.sw.siemens.com/en-US/doc/PL20251024323638784.nxopen_prog_guide/html/xid2302954?audience=external)
