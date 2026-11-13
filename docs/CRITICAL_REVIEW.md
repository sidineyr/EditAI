# Critical review and mitigation record

This initial review converts the three required adversarial perspectives into tracked engineering constraints. Tests listed below are planned unless explicitly reported as executed in `VALIDATION.md`.

## Economics and autonomy

| Criticism | Mitigation in this slice | Test/evidence | Remaining limitation |
| --- | --- | --- | --- |
| Export could depend on an account, credit balance, or paid backend. | The worker invokes a local FFmpeg executable; no account or remote inference is in this path. | Source review: `photo-animation` constructs a local subprocess invocation. Runtime/export not executed; future network-denied integration test required. | FFmpeg installation and codec availability are external; cross-platform packaging and licensing review remain. |
| A nominally local project could be trapped in a vendor format. | The initial operation emits conventional MP4; no proprietary project format exists yet. | Output is intended for ordinary media players; no rendered file was produced in this session. | Portable editable project format and save/reopen are not implemented. |

## Privacy and control

| Criticism | Mitigation in this slice | Test/evidence | Remaining limitation |
| --- | --- | --- | --- |
| Media could be uploaded or silently sent to a service. | Worker source has no network client or fetch operation; diagnostics only inspect local executables. | Source inspection only; network-denied execution not run. | This does not sandbox FFmpeg or unrelated processes, nor prove whole-device egress control. |
| Outputs could overwrite originals or existing work. | Rejects same input/output path and existing destination; attempts to remove a partial output after failed render. | Unit tests are present but were not executed. | Filesystem races and platform-specific permission behavior need integration testing. |
| Opaque agent actions could execute arbitrary commands. | This slice has no agent interface; FFmpeg arguments are passed as a list, without shell interpolation. | Source inspection; no dynamic/security testing run. | No user approval UI, media sandbox, or agent tool registry exists yet. |

## Repairability, reproducibility, and honest capability

| Criticism | Mitigation in this slice | Test/evidence | Remaining limitation |
| --- | --- | --- | --- |
| “Pan/zoom” could be marketed as AI video generation. | Registry and README explicitly mark the operation conventional and `neural: false`. | Registry source and user-facing status text. | No neural adapter exists. |
| External tools, codecs, or hardware may not be available. | Diagnostics report Python, platform, FFmpeg and ffprobe presence/version; missing FFmpeg is an explicit render error. | Code path present; diagnostic was not run here. | No automated installer, codec compatibility matrix, GPU capability detection, or packaging yet. |
| Tests or mock output could be reported as a successful render. | Validation states tests and actual rendering were not run; tests are unit checks, not render acceptance. | `VALIDATION.md` records session limits. | Tests must be executed in an environment with Python; a real fixture render and decoded-output checks remain release blockers. |
| License terms can be assumed from a free download. | No model weights or model runtimes are included in this slice. FFmpeg's license/codec status is explicitly left unverified. | Documentation and capability metadata. | A complete project license and third-party audit are still required before distribution. |

## Review conclusion

This slice is intentionally narrow. Its existence does not satisfy the full implementation prompt. Continue only with observable operations, explicit dependencies, meaningful tests, and a status record that distinguishes source presence from installed, hardware-compatible, and validated capabilities.
