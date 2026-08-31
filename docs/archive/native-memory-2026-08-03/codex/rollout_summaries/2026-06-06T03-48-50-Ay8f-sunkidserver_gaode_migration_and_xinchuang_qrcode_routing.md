thread_id: 019e9b0c-3968-7bd2-baf0-5114a5379f17
updated_at: 2026-07-28T06:30:54+00:00
rollout_path: /Users/dalwin/.codex/sessions/2026/06/06/rollout-2026-06-06T11-48-50-019e9b0c-3968-7bd2-baf0-5114a5379f17.jsonl
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunKidServer

# SunKidServer rollout covered a GaoDe API migration and production QR-code routing diagnosis

Rollout context: `/Users/dalwin/Library/IdeaProject/ZhiJin/SunKidServer` contains multiple independent Git repositories, especially `skframework`, `skdistdrserver`, `skstreetdrserver`, `sknurseryserver`, `skh5server`, and `skpubserver`.

## Task 1: Migrate GaoDe geocoding from Redis to direct public API

Outcome: partial

Preference signals:
- The user requested behavior to match the existing `pubserver` implementation and emphasized that the server can now access the public network -> future changes should first locate and reuse the established implementation rather than inventing a new protocol.

Key steps:
- Located `/gaode/getLatLng` in `skdistdrserver` and `skstreetdrserver`; both delegate to `skframework/sunkids-basic` `GaoDeService`.
- Confirmed the old implementation publishes Redis message `getLatLng`, sleeps 500 ms, then reads `getLatLng + address`.
- Confirmed `skpubserver` and `skframework/sunkids-common` contain equivalent `GaoDeMapUtil.getLngAndLat` logic.
- Added `GaoDeCoordinateClient`, changed `GaoDeServiceImpl` to inject the configured GaoDe key and call the client directly, while preserving invalid-address `ParamErrorException` behavior.
- Added a regression test covering success, null result, and missing latitude.

Failures and how to do differently:
- `skstreetdrserver` compilation remained blocked by a pre-existing missing `com.iktapp.common.enums.DatabaseType` referenced by `DataBaseConfiguration`; do not attribute this failure to the GaoDe change or modify that unrelated branch without separate investigation.
- The new test and spec were ignored by global rules (`**/*Test.java`, `**/spec-architect/`), so ordinary Git status did not show them and the changes were not committed.

Reusable knowledge:
- For framework changes consumed by API repositories, run `mvn -q -pl sunkids-basic -DskipTests install` before compiling dependent services; this allowed `skdistdrserver` to compile successfully.

References:
- `skframework/sunkids-basic/src/main/java/com/iktapp/basic/service/gaode/GaoDeServiceImpl.java`
- `skframework/sunkids-basic/src/main/java/com/iktapp/basic/service/gaode/GaoDeCoordinateClient.java`
- `skframework/sunkids-basic/src/test/java/com/iktapp/basic/service/gaode/GaoDeServiceImplTest.java`
- Passing commands: `mvn -q -pl sunkids-basic -Dtest=GaoDeServiceImplTest test`, `mvn -q -pl sunkids-basic -DskipTests compile`, `mvn -q -pl sunkids-basic -DskipTests install`, and `mvn -q -DskipTests compile` in `skdistdrserver`.

## Task 2: Diagnose QR-code routing on the Xinchuang deployment

Outcome: success

Preference signals:
- The user narrowed the investigation after confirming Nacos already points to the new database and asked specifically to regress `qrcode_register_url` -> future analysis should distinguish database correctness from URL/routing configuration and trace the exact producer service/Data ID.

Key steps:
- Traced QR generation in `sknurseryserver`, `skdistdrserver`, `skstreetdrserver`, and `skunityadminserver`; each concatenates `qrcode_register_url + qrcode_register_param + courseId` before generating the QR image.
- Identified the important mismatch: the screenshot showed `skh5server-prod`, but institution QR generation runs in `sknurseryserver` and therefore uses `sknurseryserver-prod`.
- Established the expected configuration shape: `h5_url` must be the externally reachable Xinchuang H5 root, `qrcode_register_url=${h5_url}activityDetail`, and `qrcode_register_param=?courseId=`. The generated QR should resolve to `<external-H5-root>/#/activityDetail?courseId=1498`.
- Clarified that `uploadfpath.QRcode` is local filesystem output in `QrCodeUtil`; the QR upload path uses MinIO/file-service settings, so `minio.endpoint`, `minio.port`, and `minio.bucketName` also need environment validation.
- Clarified that existing QR images are immutable; changing Nacos does not rewrite already generated QR codes or posters.

Reusable knowledge:
- Production Nacos identifiers found in repository: `sknurseryserver-prod`, `skh5server-prod`, `skdistserver-prod`, and `skstreetdrserver-prod`; Xinchuang services use namespace `55d312af-89d4-494d-8299-cd2043037d94`, while `skpubserver` has separate legacy production Nacos settings.
- Primary configuration checklist is `sknurseryserver-prod`: `h5_url`, `qrcode_register_url`, `qrcode_register_param`, plus MinIO settings. `skh5server-prod` should be checked for consistency but is not the producer of institution activity QR codes.

References:
- `sknurseryserver/src/main/java/com/iktapp/api/controller/CourseOfflineController.java:75-120`
- `skh5server/src/main/resources/application-prod.properties`
- `sknurseryserver/src/main/resources/application-prod.properties`
- `skframework/sunkids-basic/src/main/java/com/iktapp/basic/utils/qrcode/QrCodeUtil.java`
- QR generation expression: `qrcode_register_url+qrcode_register_param + courseId`
