# API 타입 시스템

이 디렉토리는 백엔드 API와의 통신을 위한 공통 타입 정의와 Axios 설정을 포함합니다.

## 📁 파일 구조

```
src/api/
├── types.ts                    # 공통 타입 및 응답 구조
├── types/
│   ├── auth.types.ts          # 인증 관련 타입 (/user/*, /hospital-staff/*, /auth/*)
│   ├── child.types.ts         # 자녀 관리 타입 (/child/*)
│   ├── inviteCode.types.ts    # 초대코드 타입 (/invite-code/*)
│   └── doctor.types.ts        # 의사/병원 타입 (/doctor/*, /hospital-staff/*)
├── axiosConfig.ts             # Axios 인스턴스 및 인터셉터
└── index.ts                   # 통합 export
```

## 🚀 사용 방법

### 1. API 타입 import

```typescript
// 공통 타입만 필요한 경우
import type { ApiResponse, UUID } from '@/api/types';

// 특정 도메인 타입이 필요한 경우
import type { UserLoginRequest, UserLoginResponse } from '@/api/types/auth.types';
import type { ChildCreateRequest, ChildInfoResponse } from '@/api/types/child.types';

// 모든 타입을 한 번에 import
import type { 
  ApiResponse, 
  UserLoginRequest, 
  ChildInfoResponse 
} from '@/api';
```

### 2. Axios 인스턴스 사용

```typescript
import api from '@/api/axiosConfig';
import type { ApiResponseUserLogin, UserLoginRequest } from '@/api/types/auth.types';

// API 호출 예시
const login = async (credentials: UserLoginRequest) => {
  const response = await api.post<ApiResponseUserLogin>(
    '/user/login',
    credentials
  );
  
  if (response.data.code === 200) {
    const { accessToken, userInfoDTO } = response.data.data;
    // 토큰 저장 및 사용자 정보 처리
  }
};
```

### 3. 공통 응답 구조

모든 API 응답은 다음 구조를 따릅니다:

```typescript
interface ApiResponse<T> {
  code: number;        // HTTP 상태 코드 (200, 400, 401 등)
  status: HttpStatus;  // HTTP 상태 문자열
  message: string;     // 응답 메시지
  data: T;            // 실제 데이터
}
```

## 🔐 인증 시스템

### Access Token
- **저장 위치**: `localStorage.getItem('accessToken')`
- **사용**: 모든 API 요청의 Authorization 헤더에 자동 추가
- **형식**: `Bearer {token}`

### Refresh Token
- **저장 위치**: HTTP-only Cookie (서버에서 관리)
- **사용**: 401 에러 발생 시 자동으로 토큰 갱신
- **엔드포인트**:
  - 일반 사용자: `POST /user/refresh`
  - 병원 직원: `POST /hospital-staff/refresh`

### 자동 토큰 갱신 플로우

```
1. API 요청 → 401 Unauthorized
2. Refresh Token으로 새 Access Token 요청
3. 성공 시: 새 토큰 저장 후 원래 요청 재시도
4. 실패 시: 로그아웃 처리 및 로그인 페이지로 리다이렉트
```

## 📝 타입 정의 규칙

### Enum 대신 Const Object 사용

TypeScript의 `erasableSyntaxOnly` 설정을 준수하기 위해 enum 대신 const object를 사용합니다:

```typescript
// ❌ 사용하지 않음
export enum Gender {
  MALE = 'MALE',
  FEMALE = 'FEMALE',
}

// ✅ 올바른 방법
export const Gender = {
  MALE: 'MALE',
  FEMALE: 'FEMALE',
} as const;
export type Gender = typeof Gender[keyof typeof Gender];
```

### 날짜/시간 타입

```typescript
type ISODate = string;      // YYYY-MM-DD
type ISODateTime = string;  // YYYY-MM-DDTHH:mm:ss
type UUID = string;         // UUID v4
```

## 🛠️ 개발 가이드

### 새로운 API 엔드포인트 추가

1. **타입 정의 추가**
   - 해당 도메인의 `*.types.ts` 파일에 Request/Response 타입 추가
   - 공통 타입은 `types.ts`에 추가

2. **API 함수 작성**
   ```typescript
   // src/features/{domain}/api/{domain}Api.ts
   import api from '@/api/axiosConfig';
   import type { ApiResponseChildInfo, ChildCreateRequest } from '@/api/types/child.types';

   export const createChild = async (data: ChildCreateRequest) => {
     const response = await api.post<ApiResponseChildInfo>('/child', data);
     return response.data;
   };
   ```

3. **에러 핸들링**
   ```typescript
   try {
     const result = await createChild(childData);
     if (result.code === 200) {
       // 성공 처리
     }
   } catch (error) {
     if (axios.isAxiosError(error)) {
       // API 에러 처리
       console.error('API Error:', error.response?.data);
     }
   }
   ```

## 🔍 주요 기능

### Request Interceptor
- 모든 요청에 자동으로 Authorization 헤더 추가
- Cookie 전송 활성화 (`withCredentials: true`)

### Response Interceptor
- 401 에러 자동 처리 (토큰 갱신)
- 대기열 관리로 동시 요청 처리
- 토큰 갱신 실패 시 자동 로그아웃

### 타입 안정성
- 모든 API 응답에 제네릭 타입 적용
- TypeScript strict 모드 준수
- 런타임 타입 체크 가능

## 📚 참고 자료

- [Axios 공식 문서](https://axios-http.com/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [OpenAPI 3.1.0 스펙](https://spec.openapis.org/oas/v3.1.0)

## ⚠️ 주의사항

1. **절대 경로 사용**: `@/api`로 import
2. **타입 import**: `import type` 사용 권장
3. **Refresh Token**: localStorage에 저장하지 않음 (Cookie 사용)
4. **에러 처리**: 모든 API 호출에 try-catch 적용
5. **응답 코드 확인**: `response.data.code === 200` 체크 필수
