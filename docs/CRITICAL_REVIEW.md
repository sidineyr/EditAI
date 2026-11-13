# Critical review and mitigation record

This review tracks economics/autonomy, privacy/control, and repairability/reproducibility risks. Tests below are present or planned as stated; none were executed in this repository-writing session.

## Economics and autonomy

| Criticism | Mitigation in source | Test/evidence | Remaining limitation |
| --- | --- | --- | --- |
| Export could depend on an account, credit balance, or paid backend. | The conventional worker invokes a local FFmpeg process; project helpers use Python's standard library. No account or cloud inference is used. | Source review only; render not executed. | User installs FFmpeg/codecs. Their binaries and codec terms are not audited or packaged. |
| Projects could be trapped in a vendor format. | Project v1 is JSON with relative assets; archive export/import is portable and output video is ordinary MP4. Selected scenes can be included in an archive. | Unit tests for bundle roundtrip exist but were not run. | No migration tooling beyond schema v1; no GUI/project recovery flow. |

## Privacy and control

| Criticism | Mitigation in source | Test/evidence | Remaining limitation |
| --- | --- | --- | --- |
| Media could be silently uploaded. | No network client or model downloader is present in the worker or bundle helper. | Source inspection only; network-denied run not performed. | This does not sandbox FFmpeg or unrelated OS processes. |
| Projects could overwrite user work or import hostile archive paths. | Existing destinations are refused. Import accepts only a manifest and `assets/<file>`, rejects traversal, symlinks, duplicate paths, oversized members, and excessive expansion; validates hashes/schema before creating destination. | Security-oriented unit tests are present but not run. | Resource limits do not substitute for hardened media decoders; filesystem behavior varies by OS. |
| An edit could silently alter original media. | Photos are copied into project assets; scene timing/approval edits only update the manifest. | Source and unit coverage, not executed. | No undo/history UI or crash-recovery journal yet. |

## Repairability and capability honesty

| Criticism | Mitigation in source | Test/evidence | Remaining limitation |
| --- | --- | --- | --- |
| Conventional pan/zoom/montage could be sold as neural video. | Capability registry and docs label these workflows non-neural. | Source/docs review. | Neural adapters do not exist. |
| Local/open software can still be unusable or unmaintained. | Current project helpers require no third-party Python packages; FFmpeg is explicitly an external requirement. | No installation or platform run performed. | No binary packaging, dependency compatibility matrix, or desktop/Android UI. |
| A test/mocked result could be presented as a real render. | Validation states tests and renders were not run; commands are instructions, not results. | `VALIDATION.md`. | Must run real tests, render, decode, and playback before capability claims. |

## Conclusion

Continue by adding observable conventional workflows with constrained inputs and portable formats. Do not list features as released merely because their roadmap exists; report exact test and device evidence.
