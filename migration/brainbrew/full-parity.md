# Full production parity certification

Result: **PASS** — 48 targets (16 Standard, 16 Extended, 16 Experimental).

## Toolchain and commands

- Legacy: Python Brain Brew `0.3.11`; `pipenv run build` and `pipenv run build_experimental`.
- Rust: Brain Brew `1.0.0-alpha.8` at `1e56a90a42be2522431cd678dfd81617eb4214a6`.
- Rust verification: `brainbrew verify --manifest brainbrew.yaml --all-targets --media-root build/brainbrew-media/standard`, plus validate, compose, per-target verify, explain, translations, and CrowdAnki export for each discovered target.
- Comparison normalizes only JSON object keys, top-level notes by GUID, and `media_files` by filename; every other array and all media names/bytes remain strict.
- This package has no federated dependencies, so no federation lock is required; explain reports record source fingerprints.

## Target evidence

| Target | Semantic SHA-256 | Media tree SHA-256 | Media | Raw JSON bytes | CSV translation units |
|---|---|---|---:|---|---:|
| `cs-experimental` | `b462d90848b5c399ac5dec38127dfedcaca1032f46d800d8643c92c923d03652` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1013 |
| `cs-extended` | `37bbd431088eab6800a8f1a425de1f59dc38fd983e0ce97dc840b9b9f3ea51c4` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1013 |
| `cs-standard` | `b12232535af9f7716322613d4d6ef8a7c24dc5a9d5137d7378e62f30b8919fbf` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1013 |
| `da-experimental` | `f2f954ba1a00a8727b967e2f6432cf39f3a305a4d74828d674fe3f087ffc831a` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1018 |
| `da-extended` | `e78888ef8d5615196fb92b1b36720e07a3df9c0857ab182cf08854b62ddf9037` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1018 |
| `da-standard` | `d810dfb3d843759396f1baf27f97564e1ee8aebb6d19800dc254c0a64295a0a6` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1018 |
| `de-experimental` | `0275c43ebe4167d452e99ad8325e955c2b17c84e314e818bcdb6c18103fc2e63` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1028 |
| `de-extended` | `8ef41fdba1a4e1418940784a2e87fe4443c9624faecfdebfb0b4b28d7b7cef0c` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1028 |
| `de-standard` | `9a396d0012403123d8be062bd859b744a85715e8d204dc4e396eb092bdd42d58` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1028 |
| `en-experimental` | `d946192704bc21ee0c6d02c9c0fed8825be707520e5674f2edc66ac0c6731a5f` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 0 |
| `en-extended` | `26f550ddfa7271c02fee16d69cd4a6dd7d18c53c5c027d7ce5ba13952dae9c6e` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 0 |
| `en-standard` | `de48fb4df5846ff9250cf3ac3e62cd8f2073b862942cf3389a4cdf8a2ea3cfa4` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 0 |
| `es-experimental` | `895d43f55f0c382676a0554911cd7f896fe58c1c228acc76936dacfa60bf1b00` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1012 |
| `es-extended` | `ff324f6ee1ff839194d2854a01b8ce383c5a7c115796dcf673540891d5ec3fdc` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1012 |
| `es-standard` | `6934b15ebcc78d62e798b81e7c9a024a01aeeebd97f6f61d1bb315256d78fd81` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1012 |
| `fr-experimental` | `89c411a65ae89873b09e42116e54e476c3d52795de362ba4f2983d2a544d949b` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1012 |
| `fr-extended` | `7b38404f4787d941297197b9b753a656af8dbac2ecb9441bffae1939640506d1` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1012 |
| `fr-standard` | `5be49194a55c77d169c8c9396979f6d8aae3817e2479dd0479fcca5ad280769f` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1012 |
| `he-experimental` | `8175b2d14adbcb8b80f5027d4d31f62ec84282a7ec8ba4910348e9ed259a7f9d` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1015 |
| `he-extended` | `6f4a3e9d5e6e1ecfe116cc3c4a78d85117e295f96fd641e8a38519bf5ab694fe` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1015 |
| `he-standard` | `e4b0ba607ba7bbfb97c255dadd973e4b93dd47593b77d5bffdfcbaf5aa29ac99` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1015 |
| `it-experimental` | `ffbac2255deebedf21e47cfa0117cf14b2f0224a984e96034077732d6d976e39` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1012 |
| `it-extended` | `12550f8282152c0396046b4b3d96b0750d4a2f3d1fcf1a72314a53f71c4f4847` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1012 |
| `it-standard` | `6cbb955a0f2824e51dd74e9da345de521cff16d47e128047c4aa111b64d661cb` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1012 |
| `nb-experimental` | `7d7ac4de5a5e359e89662417a6eab99d952e11e609b229c71740ed7bac1e0080` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1029 |
| `nb-extended` | `ba5c8e3abb5ec2e5677ce834c428b7f1686e9ac8f06f58c94c7e08321cc9fb52` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1029 |
| `nb-standard` | `353c36f5d5c57130169d0eac8e0ae06d118fd9ac861d94ffb406a2053a5336f8` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1029 |
| `nl-experimental` | `ae2482626eff63f5b574f086113550212d91a24e459ac7d3dc595d51d8399f8d` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1018 |
| `nl-extended` | `fba42d1843f923bf599ff3bcfcfdf2edd63008d57dcd42aae623f0a8b8b86727` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1018 |
| `nl-standard` | `527dd8f17462ee54c3cd333b4e96c68d50c8cc773817c71db992ba973a062e06` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1018 |
| `pl-experimental` | `04d0552026addb1fc885e3fc45f094398fd7c91ba2e532f03cc052ebde73d9aa` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1018 |
| `pl-extended` | `1a6f9a1dc94bbab88e9ed06291f1966564ddf5d629ffbfbf4945e2ec2a1a2c7e` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1018 |
| `pl-standard` | `0b331bdc2450f3b84157a3a6c88511da2296d4d282313e49d57633b6488d016c` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1018 |
| `pt-experimental` | `1fd786938240f8ec24f9dc72c5fc94dfb69500128d05527dfd552c39366193ed` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1014 |
| `pt-extended` | `21c4fc514f7c2862370a22f8d6718d3d6ffe64c2301862c9d82a9ad3c3ac6174` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1014 |
| `pt-standard` | `72cfd9b527a024b629032ec85a77d655d27755ad6fc177349f2b2b0bdf1181ad` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1014 |
| `ru-experimental` | `8d79ec16cece9c0d027cd621c0e2c1bbaacb6677c9e1d14329e1fb1e20ce3933` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1015 |
| `ru-extended` | `6d299d03c1736d565a870a221f8a87d48ef8c5ca5513833f9cc4cfc16066c1a6` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1015 |
| `ru-standard` | `2a54c0d0f32e88b3a7feb48bc6020af25772f6023998a482712e06f9c104a3c9` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1015 |
| `sv-experimental` | `d3e713bda16631f7cc8562498e467cc3de33b4b9048d49ee1cdbf5e4fb39c174` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1026 |
| `sv-extended` | `00bf4174a8a59f26098a950db1ad0f6e192ca3fb6f1e135e667cc28a7636880b` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1026 |
| `sv-standard` | `83ff89ff349193d9bd14c3bf91e3a6b7200644c1b14bb282ee2ebe4c01d963ee` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1026 |
| `zh-experimental` | `5cf9bb72217a02ace8de42b4bf4d561fefabb1128168c4aa320051c052097180` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1014 |
| `zh-extended` | `dbe79474df58b22c3c9e3469aba2801890943752f207e66d11b78044ab81f308` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1014 |
| `zh-standard` | `a4db6de8db64e698c2687a63105bee4f9f90e6bbde21a0f2ed5b8fa9115f70a4` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1014 |
| `zh-tw-experimental` | `69868d7d0bef273007609d03d51ce49e5ba29f2b02d8fe441ce9f8ef436a2a26` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` | 555 | serializer-only difference | 1012 |
| `zh-tw-extended` | `2a284bf6dec106f74b97b2b6da3630246e41cc8d0a3dc0ffadc9bdac179454fe` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1012 |
| `zh-tw-standard` | `9e21cf3bc51f2e7f84f8c3281f1ae15ab75f8a48592089b801dd69dde94d6cab` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` | 550 | serializer-only difference | 1012 |

Every row has semantic JSON equality and exact media filename/byte equality. Raw JSON byte differences are serializer formatting/order only and are not used to excuse content differences.

## Ownership and Workbench evidence

All 323 production notes and localized CSV fields remain CSV-owned and read-only; identity validation proves 323 unique stable note IDs and exact typed-media references while `main.csv` remains byte-identical to the legacy source.

No Hardcore/federation targets, translation corrections, editorial changes, CSV write-back, generated note YAML, or generic transformation layer are included.
