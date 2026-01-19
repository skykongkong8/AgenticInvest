# 데이터 흐름 샘플 데이터

이 디렉토리는 AgenticInvest 프로젝트의 데이터 및 정보 흐름을 시각화하기 위한 실제 시나리오 기반 샘플 데이터 파일들을 포함합니다.

## 시나리오

**주식**: TSLA (Tesla Inc.)  
**투자 기간**: 1개월 (1m)  
**리스크 프로필**: normal  
**포트폴리오 컨텍스트**: Tech growth portfolio, 15% allocation target

## 데이터 흐름 단계별 파일

### 1. 사용자 입력 (User Input)
**파일**: `01_request_input.json`

CLI 또는 JSON API를 통해 시스템에 입력되는 초기 요청 데이터입니다. `RequestInput` Pydantic 스키마를 따릅니다.

```json
{
  "ticker": "TSLA",
  "horizon": "1m",
  "risk_profile": "normal",
  "portfolio_context": "Tech growth portfolio, 15% allocation target",
  "requested_at": "2024-01-15T10:30:00Z"
}
```

### 2. 연구 계획 (Research Plan)
**파일**: `02_research_plan.json`

`Planner.create_base_plan()` 메서드에 의해 생성된 초기 연구 계획입니다. 여러 `ResearchTaskSpec` 객체들을 포함하며, 각 태스크는 특정 Crew에 할당됩니다.

**주요 태스크**:
- `price_analysis` → PriceCrew
- `news_analysis` → NewsCrew
- `fundamental_analysis` → FundamentalsCrew

### 3. 초기 증거 (Initial Evidence)
**파일**: `03_evidence_initial.json`

초기 연구 계획의 태스크들을 실행한 결과로 생성된 `Evidence` 객체들의 리스트입니다.

**증거 유형**:
- **Price Evidence**: 변동성, 드로우다운, 모멘텀 데이터
- **News Evidence**: 뉴스 감정 분석, 제품 뉴스, 규제 관련 뉴스
- **Fundamental Evidence**: P/E 비율, 수익 성장률

### 4. 신호 합성 (Signals)
**파일**: `04_signals.json`

`Synthesizer.build_signals()` 메서드에 의해 Evidence 리스트로부터 추출된 종합 신호입니다.

**주요 신호**:
- `volatility_20d`: 45.2% (높은 변동성)
- `event_risk`: 0.90 (높은 이벤트 리스크)
- `momentum_score`: 0.65 (긍정적 모멘텀)
- `news_red_flags`: ["regulatory scrutiny", "legal risk"]

### 5. 트리거된 추가 작업 (Triggered Tasks)
**파일**: `05_triggered_tasks.json`

`TriggerEngine.evaluate()` 메서드에 의해 신호와 증거를 분석하여 동적으로 생성된 추가 연구 태스크들입니다.

**트리거 조건**:
- 변동성 스파이크 (volatility_20d > 40%) → `options_liquidity_analysis`
- 법적/규제 리스크 플래그 → `legal_analysis`

### 6. 추가 증거 (Additional Evidence)
**파일**: `06_evidence_additional.json`

트리거된 추가 작업들을 실행한 결과로 생성된 추가 `Evidence` 객체들입니다.

**추가 증거 유형**:
- **Options Analysis**: 옵션 시장 감정, 유동성 분석
- **Legal Analysis**: 규제 조사 상세 분석, 리스크 완화 요소

### 7. 최종 리포트 (Final Report - JSON)
**파일**: `07_final_report.json`

`VerdictEngine.compute_verdict()` 메서드에 의해 생성된 최종 판단 리포트입니다. 모든 증거, 신호, 판단 근거를 포함합니다.

**주요 구성 요소**:
- `verdict`: "HOLD" (최종 판단)
- `rationale`: bull_case와 bear_case를 Evidence ID로 인용
- `risks`: 식별된 주요 리스크
- `next_actions`: 권장 후속 조치

### 8. 최종 리포트 (Final Report - Markdown)
**파일**: `08_final_report.md`

인간이 읽을 수 있는 형태로 렌더링된 마크다운 리포트입니다. JSON 리포트의 모든 정보를 포함하되, 더 읽기 쉬운 형식으로 구성됩니다.

## 데이터 흐름 다이어그램

```
User Input (CLI/JSON)
    ↓
RequestInput (Pydantic Schema)          → 01_request_input.json
    ↓
Planner.create_base_plan()                → 02_research_plan.json
    ↓
Execute Tasks                             → 03_evidence_initial.json
    ↓
Synthesizer.build_signals()              → 04_signals.json
    ↓
TriggerEngine.evaluate()                  → 05_triggered_tasks.json
    ↓
Execute New Tasks                         → 06_evidence_additional.json
    ↓
VerdictEngine.compute_verdict()          → 07_final_report.json
    ↓
Render Markdown                           → 08_final_report.md
```

## 사용 방법

이 샘플 데이터들은 다음 목적으로 사용할 수 있습니다:

1. **시스템 이해**: 각 단계에서 어떤 데이터가 생성되고 변환되는지 이해
2. **테스트**: 시스템 테스트 시 예상되는 데이터 구조 확인
3. **문서화**: API 문서나 시스템 아키텍처 문서 작성 시 참고
4. **개발**: 새로운 기능 개발 시 데이터 구조 참고

## 주의사항

- 이 샘플 데이터는 실제 시나리오를 가정한 것이지만, 실제 API 응답이나 데이터베이스 쿼리 결과와는 다를 수 있습니다.
- 날짜, 가격, 증거 ID 등은 예시용이며 실제 값과 다를 수 있습니다.
- Evidence의 `confidence` 값과 신호 값들은 시나리오를 설명하기 위한 예시입니다.
