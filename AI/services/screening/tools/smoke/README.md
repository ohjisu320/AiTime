# Local LiveKit Smoke Test

이 폴더의 스모크 테스트는 **프론트/백엔드 연동 없이도** 아래 3가지를 한번에 확인하려고 만든 것입니다.

1) AI 서버가 LiveKit 방에 접속해서 **영상 트랙을 subscribe** 하는지  
2) AI 서버가 Data Channel로 **가이드 메시지를 publish** 하는지  
3) AI 서버가 완료 시 백엔드(여기서는 fake backend)로 **HTTP 콜백**을 보내는지

## Quickstart (Windows)

1. LiveKit 서버 실행 준비
   - `livekit-server`를 PATH에 설치해두거나,
   - Docker Desktop이 설치되어 있어야 합니다.

2. 프로젝트 루트에서 실행:
   ```bat
   tools\local_livekit_smoke_test.bat
   ```

3. 브라우저가 열리면 카메라/마이크 권한을 허용하세요.
   - 화면 하단 로그에 `data_received`가 찍히면 OK 입니다.

## Generated files

- `artifacts/smoke/tokens_*.json` : room/user/ai 토큰이 들어있습니다.

## Notes

- LiveKit dev 서버(`--dev`)는 로컬 개발용이며, 문서의 예시처럼 기본 API key/secret(`devkey`/`secret`)로 토큰을 생성해 테스트할 수 있습니다.
- 배포 환경에서는 반드시 `wss://` 및 실제 API key/secret를 사용하세요.
