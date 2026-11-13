# Critical review and mitigation record

Review status: mitigations are partly implemented in source; tests and integration evidence have not been executed in this session. Read alongside `VALIDATION.md`.

## Economics and autonomy

| Criticism | Mitigation in source | Test/evidence | Remaining limitation |
| --- | --- | --- | --- |
| Export could depend on an account, credit balance, or paid backend. | Conventional worker paths use a local FFmpeg process; no account or remote inference is part of these operations. | Source review only; render not executed. | User must install FFmpeg and compatible codecs; licensing and distribution are not audited. |
| Project interchange could be tied to a vendor. | Project v1 is JSON with relative copied assets and content hashes; exports are ordinary MP4. | Unit coverage is present, unexecuted. | Schema migration, archive export/import, project UI, and recovery are absent. |

## Privacy and control

| Criticism | Mitigation in source | Test/evidence | Remaining limitation |
| --- | --- | --- | --- |
| Media may be uploaded or silently sent away. | This worker contains no network client or model fetcher. | Source review only; OS network isolation not tested. | It does not sandbox FFmpeg or unrelated processes. |
| Inputs or existing outputs may be overwritten. | Inputs are copied into project assets; render uses a private temporary file and checks destination before publish. | Unit guards exist but not run. | Cross-platform concurrent-write behavior still needs integration testing; no promise of crash-proof storage on every filesystem. |
| A malformed project may reference files outside its directory. | Manifest size/count bounds, relative resolution, path containment, and SHA-256 verification are implemented. | Path traversal and tampering tests are present but unexecuted. | Malformed media decoding still depends on external FFmpeg hardening; resource limits need more tests. |

## Repairability, reproducibility, and capability honesty

| Criticism | Mitigation in source | Test/evidence | Remaining limitation |
| --- | --- | --- | --- |
| Conventional pan/zoom or montage could be misrepresented as neural video. | Capability registry and docs mark both paths non-neural. | Source/doc review. | No neural adapter exists. |
| Open source/local does not guarantee easy setup, reproducibility, or affordability. | No Python package setup is needed for current helper commands; dependency requirement is disclosed; failure path says to install FFmpeg explicitly. | No install/runtime testing performed. | Binary packaging, codec compatibility, and cross-platform toolchain validation remain. |
| Unit or mock tests could be presented as real exports. | Validation explicitly says the tests/render were not run and commands are instructions only. | `VALIDATION.md`. | Must run real tests, render, decode, and playback before claims. |
| Optional model licensing could be assumed from runtime licensing. | No model weights or AI runtime are included in this slice. | Source/docs. | Model catalog and license audit remain future work; no AI claims are supported. |
