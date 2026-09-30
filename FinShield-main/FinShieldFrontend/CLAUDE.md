# FinShield 프론트엔드

## 기술 스택
- **프레임워크**: React Native (Expo SDK 55)
- **언어**: TypeScript
- **웹 지원**: Expo Web
- **상태관리**: Zustand
- **백엔드**: FastAPI (http://localhost:8000)

## 폴더 역할 규칙
components/  → 공통 컴포넌트 (2곳 이상 쓰이면 여기로)
components/common/ → 어디서나 쓰는 컴포넌트 (Button, Input, Alert 등)
api/         → FastAPI 호출 함수만 (컴포넌트에서 직접 fetch 금지)
hooks/       → 커스텀 훅만 (use로 시작)
constants/   → 디자인 시스템, 상수
app/         → 화면 (Expo Router)

## 현재 구현 상태 (2025-04)
### app/ (화면)
- app/(tabs)/index.tsx    : 기본 홈 탭 (미개발, Expo 기본 템플릿)
- app/(tabs)/explore.tsx  : 기본 탐색 탭 (미개발, Expo 기본 템플릿)
- app/(tabs)/_layout.tsx  : 탭 레이아웃
- app/_layout.tsx         : 루트 레이아웃
- app/modal.tsx           : 모달 화면

### components/ (공통 컴포넌트)
- external-link.tsx       : 외부 링크 컴포넌트
- haptic-tab.tsx          : 햅틱 피드백 탭
- hello-wave.tsx          : 웨이브 애니메이션
- parallax-scroll-view.tsx: 패럴랙스 스크롤
- themed-text.tsx         : 테마 적용 텍스트
- themed-view.tsx         : 테마 적용 뷰

### hooks/
- use-color-scheme.ts     : 다크/라이트 모드 감지
- use-color-scheme.web.ts : 웹 전용 색상 스킴
- use-theme-color.ts      : 테마 색상 훅

### 미생성 폴더 (개발 시 생성 필요)
- api/         : FastAPI 호출 함수 (아직 없음)
- components/common/ : 공통 UI 컴포넌트 (아직 없음)
- store/ or context/ : 상태관리 (아직 없음)

## 1. 디자인 시스템

### 색상 (constants/theme.ts)
```typescript
export const COLORS = {
  primary: '#1A56DB',
  primaryLight: '#E6F1FB',
  primaryDark: '#185FA5',
  danger: '#E24B4A',
  dangerLight: '#FCEBEB',
  dangerDark: '#A32D2D',
  warning: '#EF9F27',
  warningLight: '#FAEEDA',
  warningDark: '#854F0B',
  success: '#639922',
  successLight: '#EAF3DE',
  successDark: '#27500A',
  gray100: '#F1EFE8',
  gray200: '#D3D1C7',
  gray400: '#888780',
  gray900: '#2C2C2A',
}
```

### 폰트 크기
```typescript
export const FONT_SIZE = {
  display: 28,
  h1: 24,
  h2: 20,
  body: 18,     // 본문 최소 (고령층 권장)
  caption: 13,
}
```

### 간격
```typescript
export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,   // 화면 좌우 패딩
  xl: 32,
  xxl: 48,
}
```

### 컴포넌트 규격
- 버튼 높이: 52px 이상 (고령층 터치 영역)
- 입력 필드 높이: 52px
- border-radius: 12px
- 글자 크기: 최소 16px

## 2. 네이밍 규칙
| 종류 | 규칙 | 예시 |
|---|---|---|
| 컴포넌트 파일 | PascalCase | RiskAlert.tsx |
| 화면 파일 | 소문자 | transfer.tsx |
| 훅 | use + PascalCase | useAuth.ts |
| API 파일 | 소문자 | transfer.ts |
| 상수 | UPPER_SNAKE_CASE | PRIMARY_COLOR |
| 타입/인터페이스 | PascalCase | TransferRequest |
| 일반 함수/변수 | camelCase | getRiskScore() |

## 3. 화면 구조 (탭)
탭 1. 홈         - 잔액, 최근 거래, 위험 알림
탭 2. 송금       - 계좌입력, 금액, 위험도 분석, 보호자 승인
탭 3. 신고       - 사기 신고, 신고 내역
탭 4. 마이페이지 - 내 정보, 보호자 설정, 알림 설정

## 4. 코딩 컨벤션
언어        TypeScript 필수 (any 사용 금지)
들여쓰기    2칸
따옴표      작은따옴표 ('') 사용
세미콜론    없음
주석        한국어로 작성

### import 순서
```typescriptcd..
import { useState } from 'react'              // 1. React
import { View, Text } from 'react-native'     // 2. React Native
import { useRouter } from 'expo-router'       // 3. 외부 라이브러리
import { COLORS } from '@/constants/theme'   // 4. 내부 파일
```

### API 호출 규칙
```typescript
// api/ 폴더에서만 호출, 컴포넌트에서 직접 fetch 금지
const BASE_URL = process.env.EXPO_PUBLIC_API_URL

export const analyzeRisk = async (data: TransferRequest) => {
  const res = await fetch(`${BASE_URL}/api/v1/transfer/risk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return res.json()
}
```

### 컴포넌트 작성 규칙

1파일 1컴포넌트
Props 타입 반드시 정의
export default function 사용
StyleSheet.create() 또는 theme.ts 상수 사용
2곳 이상 쓰이면 components/common/ 으로 이동


## 개발 시작
```bash
npx expo start
# w → 웹 / a → 안드로이드 / i → iOS
```