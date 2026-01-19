# AgenticInvest 시스템 불변식 (System Invariants)

## 개요

이 문서는 AgenticInvest 시스템의 핵심 불변식(Invariants)을 정의합니다. 불변식은 시스템이 **항상** 만족해야 하는 조건이며, 위반 시 시스템의 신뢰성과 무결성이 심각하게 훼손됩니다.

---

## 불변식 정의

### INV-1: 증거 추적성 불변식 (Evidence Traceability Invariant)

**정의**: 모든 최종 판단(verdict)과 리포트의 주요 주장은 하나 이상의 검증 가능한 Evidence 객체에 연결되어야 합니다. Evidence가 없는 판단은 생성될 수 없습니다.

**위반 시 재앙적 결과**:
- **법적 책임**: 증거 없이 생성된 판단은 금융 조언으로 오인될 수 있으며, 법적 분쟁의 원인이 됩니다.
- **신뢰성 붕괴**: 사용자가 판단의 근거를 확인할 수 없어 시스템 전체에 대한 신뢰가 무너집니다.
- **재현 불가능성**: 동일한 입력에 대해 다른 결과가 나올 수 있어 디버깅과 개선이 불가능합니다.
- **책임 추적 불가**: 잘못된 판단의 원인을 찾을 수 없어 시스템 개선이 불가능합니다.

**강제 모듈**:
- **`src/orchestrator/verdict.py` (VerdictEngine)**: `compute_verdict()` 메서드에서 모든 rationale 항목이 Evidence ID를 포함하는지 검증
- **`src/orchestrator/flow.py` (OrchestratorFlow)**: `_render_markdown()` 및 최종 리포트 생성 시 Evidence 연결 검증
- **`src/schemas/report.py` (VerdictReport)**: Pydantic 모델 레벨에서 `evidence` 필드가 비어있지 않은지 검증
- **Quality Gate 모듈** (현재 미구현): 최종 판단 전 Evidence 연결성 검증

**현재 구현 상태**:
- ✅ `VerdictReport` 스키마에 `evidence: List[Evidence]` 필드 존재
- ⚠️ `VerdictEngine.compute_verdict()`에서 Evidence를 rationale에 연결하지만, **모든 rationale 항목이 Evidence를 참조하는지 강제하지 않음**
- ❌ **Quality Gate 모듈이 없음** - R6 규칙에 명시되어 있으나 구현되지 않음
- ⚠️ `_render_markdown()`에서 Evidence ID를 표시하지만, 누락된 경우를 검증하지 않음

**격차 (Gaps)**:
1. VerdictEngine에서 rationale의 모든 항목이 Evidence ID를 포함하는지 검증하는 로직 없음
2. Quality Gate 모듈이 없어 최종 판단 전 Evidence 연결성 검증이 수행되지 않음
3. Evidence가 비어있을 때 Verdict 생성이 차단되지 않음 (Pydantic은 빈 리스트를 허용)

---

### INV-2: 결정론적 판단 경계 불변식 (Deterministic Verdict Boundaries Invariant)

**정의**: 모든 최종 판단(verdict)은 고정된 `Verdict` enum 값 중 하나여야 합니다. 시스템은 enum 외의 값이나 임의의 문자열을 생성할 수 없습니다.

**위반 시 재앙적 결과**:
- **다운스트림 시스템 오류**: Verdict를 소비하는 자동화 시스템(예: 주문 실행 시스템)이 예상치 못한 값을 받아 크래시하거나 잘못된 동작을 수행합니다.
- **계약 위반**: API 계약이 깨져 클라이언트 코드가 예외를 발생시킵니다.
- **데이터 무결성 손상**: 데이터베이스나 로그에 잘못된 값이 저장되어 후속 분석이 불가능합니다.
- **규정 준수 실패**: 금융 규제 기관이 요구하는 표준화된 분류 체계를 준수하지 못합니다.

**강제 모듈**:
- **`src/schemas/report.py` (Verdict Enum)**: Pydantic 모델이 enum 타입을 강제
- **`src/orchestrator/verdict.py` (VerdictEngine)**: `compute_verdict()` 메서드가 항상 enum 값을 반환하도록 보장
- **`src/orchestrator/flow.py` (OrchestratorFlow)**: VerdictReport 생성 시 enum 값만 허용
- **타입 시스템**: Python 타입 힌트와 Pydantic 검증

**현재 구현 상태**:
- ✅ `Verdict` enum이 정의되어 있음 (`STRONG_BUY`, `BUY`, `HOLD`, `SELL`, `STRONG_SELL`, `DO_NOT_TOUCH`)
- ✅ `VerdictEngine.compute_verdict()`가 enum 값을 반환
- ✅ `VerdictReport` 스키마가 `verdict: Verdict` 타입으로 정의됨
- ⚠️ **예외 처리 부족**: VerdictEngine에서 예외 발생 시 기본값(예: `HOLD`)을 반환하는 로직이 없음

**격차 (Gaps)**:
1. VerdictEngine에서 예외 발생 시 안전한 기본값을 반환하는 fallback 로직 없음
2. Verdict 값이 None이거나 잘못된 경우를 처리하는 검증 로직 없음

---

### INV-3: 실행 불변성 불변식 (Run Immutability Invariant)

**정의**: 한 번 완료된 run의 아티팩트(evidence, verdict, report)는 수정될 수 없습니다. 새로운 증거나 판단이 필요하면 새로운 run을 생성해야 합니다.

**위반 시 재앙적 결과**:
- **감사 추적 불가능**: 어떤 판단이 언제 변경되었는지 추적할 수 없어 규제 감사에서 실패합니다.
- **재현성 파괴**: 동일한 run_id로 다른 결과가 나올 수 있어 과학적 재현성이 무너집니다.
- **법적 증거 손상**: 법적 분쟁 시 증거로 사용할 수 없습니다.
- **버전 관리 혼란**: 어떤 버전이 최종 판단인지 알 수 없어 의사결정이 혼란스러워집니다.

**강제 모듈**:
- **파일 시스템 권한**: `runs/<run_id>/` 디렉토리를 읽기 전용으로 설정 (현재 미구현)
- **`src/orchestrator/flow.py` (OrchestratorFlow)**: 완료된 run 디렉토리에 대한 쓰기 시도 차단
- **데이터베이스 스키마** (미래 확장 시): 완료된 run 레코드를 immutable로 마킹
- **버전 관리 시스템**: Git과 같은 버전 관리로 변경 이력 추적 (현재 미구현)

**현재 구현 상태**:
- ✅ 각 run이 고유한 `run_id`로 디렉토리 생성 (`<timestamp>_<ticker>`)
- ❌ **완료된 run 디렉토리를 보호하는 메커니즘 없음** - 파일 시스템 레벨에서 덮어쓰기 가능
- ❌ **run 완료 상태를 추적하는 플래그 없음** - 언제 run이 완료되었는지 명확하지 않음
- ⚠️ `_log_event()`가 계속 호출되면 기존 이벤트 로그에 추가됨 (append 모드)

**격차 (Gaps)**:
1. Run 완료 후 디렉토리 보호 메커니즘 없음
2. Run 상태(진행 중/완료)를 추적하는 메타데이터 없음
3. 완료된 run에 대한 쓰기 시도 감지 및 차단 로직 없음

---

### INV-4: 스키마 무결성 불변식 (Schema Integrity Invariant)

**정의**: 시스템 내부를 흐르는 모든 구조화된 데이터(Evidence, RequestInput, VerdictReport, Signals 등)는 해당 Pydantic 스키마를 통과해야 합니다. 스키마 검증을 통과하지 못한 데이터는 시스템에 진입할 수 없습니다.

**위반 시 재앙적 결과**:
- **런타임 크래시**: 예상치 못한 데이터 구조로 인해 AttributeError, KeyError 등이 발생합니다.
- **데이터 손실**: 필수 필드가 누락되어 후속 처리에서 정보가 손실됩니다.
- **보안 취약점**: 검증되지 않은 입력이 시스템에 주입되어 보안 문제가 발생할 수 있습니다.
- **디버깅 불가능**: 어디서 잘못된 데이터가 생성되었는지 추적하기 어렵습니다.

**강제 모듈**:
- **Pydantic 모델**: 모든 스키마가 `BaseModel`을 상속하여 자동 검증
- **`src/schemas/` 모듈**: Evidence, RequestInput, VerdictReport 등 모든 스키마 정의
- **입력 검증 레이어**: CLI/API에서 RequestInput 검증
- **Crew 출력 검증**: 각 Crew가 Evidence 객체를 반환하도록 강제

**현재 구현 상태**:
- ✅ 모든 주요 스키마가 Pydantic `BaseModel`로 정의됨
- ✅ `Evidence.confidence`가 `Field(ge=0.0, le=1.0)`로 범위 검증됨
- ✅ `RequestInput.horizon`과 `risk_profile`이 정규식 패턴으로 검증됨
- ⚠️ **Crew 출력 검증 부족**: Crew가 Evidence 리스트를 반환하는지 검증하는 로직 없음
- ⚠️ **중간 데이터 검증 부족**: Signals 객체 생성 시 값 범위 검증이 없음 (예: sentiment_score가 -1.0~1.0 범위를 벗어날 수 있음)

**격차 (Gaps)**:
1. Crew의 `execute()` 메서드 반환값이 Evidence 리스트인지 검증하는 로직 없음
2. Signals 객체의 값 범위 검증이 없음 (예: `sentiment_score`, `momentum_score`가 -1.0~1.0 범위를 벗어날 수 있음)
3. Evidence의 `source_type`이 허용된 값(`price|news|filing|analysis`)인지 검증하는 enum 없음

---

### INV-5: 트리거 결정론 불변식 (Trigger Determinism Invariant)

**정의**: 동일한 입력(request, evidences, signals)에 대해 TriggerEngine은 항상 동일한 결과(새로운 task 리스트)를 반환해야 합니다. 트리거 평가는 비결정론적 요소(랜덤, 현재 시간 등)에 의존하지 않아야 합니다.

**위반 시 재앙적 결과**:
- **재현 불가능성**: 동일한 입력으로 실행해도 다른 task가 생성되어 디버깅이 불가능합니다.
- **예측 불가능한 비용**: 트리거가 불필요하게 발동하거나 누락되어 API 비용이 예측 불가능하게 증가합니다.
- **품질 불일치**: 같은 증거에 대해 다른 깊이의 분석이 수행되어 일관성 없는 리포트가 생성됩니다.
- **테스트 불가능**: 단위 테스트가 불안정해져 CI/CD 파이프라인이 실패합니다.

**강제 모듈**:
- **`src/orchestrator/triggers.py` (TriggerEngine)**: `evaluate()` 메서드가 순수 함수로 구현되어야 함
- **임의성 제거**: UUID 생성 등은 task ID 생성에만 사용되고 평가 로직에는 영향 없어야 함
- **시간 의존성 제거**: 현재 시간을 직접 사용하지 않고, Evidence의 timestamp를 사용
- **외부 상태 의존성 제거**: 전역 변수, 파일 시스템 상태 등에 의존하지 않음

**현재 구현 상태**:
- ✅ `TriggerEngine.evaluate()`가 request, evidences, signals만을 입력으로 받음
- ✅ 트리거 조건이 결정론적임 (예: `volatility_20d > 0.40`, `len(evidences) < 3`)
- ⚠️ **UUID 생성**: `uuid4()`를 사용하여 task ID를 생성하지만, 이는 평가 결과에는 영향 없음 (올바른 구현)
- ✅ 시간 의존성 없음 - Evidence의 timestamp를 사용하지 않고 현재 시간도 사용하지 않음

**격차 (Gaps)**:
1. 트리거 평가 결과를 로깅하지만, 동일 입력에 대한 재평가 결과가 동일한지 검증하는 테스트 없음
2. 트리거 임계값이 하드코딩되어 있어 설정 파일로 분리되지 않음 (결정론적이지만 유연성 부족)

---

### INV-6: 시간 일관성 불변식 (Temporal Consistency Invariant)

**정의**: 모든 Evidence 객체의 `timestamp`는 해당 Evidence가 생성된 실제 시간을 반영해야 하며, Evidence 간의 시간 순서가 논리적으로 일관되어야 합니다. 또한 run의 모든 아티팩트는 run 시작 시간 이후의 시간을 가져야 합니다.

**위반 시 재앙적 결과**:
- **시간 여행 버그**: 미래의 Evidence가 과거의 Evidence를 참조하는 논리적 모순이 발생합니다.
- **트리거 오작동**: 시간 기반 트리거(예: "최근 30일 뉴스")가 잘못된 Evidence를 선택합니다.
- **감사 추적 실패**: 규제 감사에서 시간 순서가 맞지 않아 거부됩니다.
- **데이터 분석 오류**: 시계열 분석이 잘못된 결과를 생성합니다.

**강제 모듈**:
- **`src/schemas/evidence.py` (Evidence)**: `timestamp` 필드가 필수이며 ISO 8601 형식
- **`src/orchestrator/flow.py` (OrchestratorFlow)**: run 시작 시간을 기록하고, 모든 Evidence의 timestamp가 이후인지 검증
- **Crew 모듈**: Evidence 생성 시 올바른 timestamp 설정
- **시간 검증 유틸리티**: Evidence 리스트의 시간 순서 검증

**현재 구현 상태**:
- ✅ `Evidence.timestamp`가 `datetime` 타입으로 정의되고 기본값이 `datetime.utcnow()`로 설정됨
- ❌ **run 시작 시간 추적 없음**: `OrchestratorFlow.run()`에서 run 시작 시간을 저장하지 않음
- ❌ **Evidence timestamp 검증 없음**: Evidence의 timestamp가 run 시작 시간 이후인지 검증하지 않음
- ❌ **시간 순서 검증 없음**: Evidence 리스트의 시간 순서가 논리적으로 일관되는지 검증하지 않음
- ⚠️ Crew가 Evidence를 생성할 때 timestamp를 명시적으로 설정하는지 불명확

**격차 (Gaps)**:
1. Run 시작 시간을 메타데이터로 저장하는 로직 없음
2. Evidence의 timestamp가 run 시작 시간 이후인지 검증하는 로직 없음
3. Evidence 리스트의 시간 순서 일관성 검증 로직 없음
4. Crew가 Evidence 생성 시 timestamp를 올바르게 설정하는지 검증하는 테스트 없음

---

### INV-7: 품질 게이트 강제 불변식 (Quality Gate Enforcement Invariant)

**정의**: 최종 Verdict가 생성되기 전에, 시스템은 반드시 품질 게이트(R6 규칙)를 통과해야 합니다. 품질 게이트를 통과하지 못한 경우 Verdict 생성이 차단되거나, 추가 연구가 트리거되어야 합니다.

**위반 시 재앙적 결과**:
- **저품질 판단**: 증거가 부족하거나 편향된 판단이 생성되어 사용자에게 잘못된 조언을 제공합니다.
- **법적 책임**: 불충분한 증거로 인한 판단은 금융 조언 책임 문제를 야기합니다.
- **신뢰성 손상**: 사용자가 시스템의 판단을 신뢰하지 않게 됩니다.
- **비용 낭비**: 불필요한 API 호출과 계산 리소스가 낭비됩니다.

**품질 게이트 조건 (R6 규칙)**:
- Evidence count: `>= MIN_EVIDENCE_COUNT` (기본값: 8)
- Coverage: 최소 2개 카테고리(`price`, `news`, `fundamental`) 커버
- Counter-argument 존재: `bear_case`가 비어있지 않아야 함
- Confidence sanity: 평균 confidence가 임계값 이상이어야 함

**강제 모듈**:
- **Quality Gate 모듈** (현재 미구현): `src/orchestrator/quality_gate.py`
- **`src/orchestrator/flow.py` (OrchestratorFlow)**: Verdict 생성 전 Quality Gate 호출
- **`src/orchestrator/triggers.py` (TriggerEngine)**: 품질 게이트 실패 시 추가 연구 트리거
- **설정 파일**: `configs/thresholds.yaml`에 임계값 정의

**현재 구현 상태**:
- ❌ **Quality Gate 모듈이 완전히 없음** - R6 규칙에 명시되어 있으나 구현되지 않음
- ❌ **Evidence count 검증 없음**: `len(evidences) < 3` 체크는 있지만, 최종 Verdict 생성 전 검증 없음
- ❌ **Coverage 검증 없음**: 카테고리별 Evidence 분류 및 검증 로직 없음
- ❌ **Counter-argument 검증 없음**: `bear_case`가 비어있는지 검증하는 로직 없음
- ❌ **Confidence sanity 검증 없음**: 평균 confidence 계산 및 검증 로직 없음
- ⚠️ `configs/thresholds.yaml` 파일이 존재하지만 Quality Gate에서 사용되지 않음

**격차 (Gaps)**:
1. Quality Gate 모듈 자체가 없음
2. 모든 품질 게이트 조건 검증 로직이 없음
3. 품질 게이트 실패 시 Verdict 생성 차단 로직 없음
4. 품질 게이트 실패 시 추가 연구 자동 트리거 로직 없음

---

## 불변식 매핑 요약

### 현재 구현 상태

| 불변식 | 상태 | 주요 격차 |
|--------|------|-----------|
| INV-1: Evidence Traceability | ⚠️ 부분 구현 | Quality Gate 모듈 없음, rationale-Evidence 연결 강제 없음 |
| INV-2: Deterministic Verdict Boundaries | ✅ 잘 구현됨 | 예외 처리 fallback 로직 부족 |
| INV-3: Run Immutability | ❌ 미구현 | Run 완료 후 보호 메커니즘 없음 |
| INV-4: Schema Integrity | ⚠️ 부분 구현 | Crew 출력 검증, Signals 범위 검증 부족 |
| INV-5: Trigger Determinism | ✅ 잘 구현됨 | 재현성 테스트 부족 |
| INV-6: Temporal Consistency | ❌ 미구현 | 시간 검증 로직 전혀 없음 |
| INV-7: Quality Gate Enforcement | ❌ 미구현 | Quality Gate 모듈 자체가 없음 |

### 우선순위별 격차 해결 필요성

**Critical (즉시 해결 필요)**:
1. **INV-7: Quality Gate Enforcement** - 핵심 비즈니스 로직이지만 완전히 누락됨
2. **INV-1: Evidence Traceability** - 법적 책임과 직결되는 핵심 불변식
3. **INV-3: Run Immutability** - 감사 추적을 위해 필수

**High (단기간 내 해결 필요)**:
4. **INV-6: Temporal Consistency** - 데이터 무결성에 필수
5. **INV-4: Schema Integrity** - 런타임 안정성에 중요

**Medium (중기적으로 개선)**:
6. **INV-2: Deterministic Verdict Boundaries** - 예외 처리 강화
7. **INV-5: Trigger Determinism** - 테스트 커버리지 확대

---

## 결론

AgenticInvest 시스템은 현재 **7개 불변식 중 2개만 잘 구현**되어 있고, **3개는 부분 구현**, **2개는 완전히 미구현** 상태입니다. 특히 **Quality Gate Enforcement (INV-7)**와 **Run Immutability (INV-3)**는 핵심 기능임에도 불구하고 전혀 구현되지 않았습니다.

시스템의 신뢰성과 규정 준수를 위해서는 이러한 격차를 해소하는 것이 시급합니다.

---

## 이전 프롬프트의 기여 분석

### 프롬프트 요구사항

이 문서는 다음 프롬프트 지시사항에 따라 작성되었습니다:

> "Before discussing implementation or features:
> 1. Define 5–7 SYSTEM INVARIANTS that must always hold true.
> 2. For each invariant: Explain why violating it would be catastrophic, Identify which modules are responsible for enforcing it
> 3. Only after invariants are defined, map current AgenticInvest components to these invariants and identify gaps.
> DO NOT suggest new features. DO NOT write code. Focus strictly on invariants and enforcement logic."

### 프롬프트의 핵심 기여

#### 1. 구현 전 설계 단계 강제 (Design-Before-Implementation)

**기여**: 프롬프트는 명시적으로 "Before discussing implementation or features"라고 지시하여, 코드 작성이나 기능 제안 전에 시스템의 핵심 원칙을 먼저 정의하도록 강제했습니다.

**결과**: 
- 구현 세부사항에 빠지지 않고 시스템의 본질적 제약 조건에 집중할 수 있었습니다.
- 각 불변식이 "왜 필요한가"에 대한 명확한 이해를 바탕으로 정의되었습니다.
- 현재 코드베이스의 문제점을 기능 추가가 아닌 **원칙 위반** 관점에서 분석할 수 있었습니다.

**예시**: Quality Gate Enforcement (INV-7) 불변식은 R6 규칙에 명시되어 있지만 구현되지 않았음을 발견했습니다. 만약 구현부터 시작했다면, 이는 "추가 기능"으로 인식되었을 수 있지만, 불변식 관점에서는 **시스템의 필수 요구사항**으로 인식됩니다.

#### 2. 명확한 제약 조건 (Explicit Constraints)

**기여**: "DO NOT suggest new features. DO NOT write code"라는 명시적 제약이 분석의 범위를 명확히 제한했습니다.

**결과**:
- 해결책 제시에 집중하지 않고 **문제 정의**에 집중할 수 있었습니다.
- 각 불변식의 "위반 시 재앙적 결과"를 구체적으로 분석할 수 있었습니다.
- 격차(Gaps) 식별이 해결책 제안으로 흐르지 않고, **현재 상태의 정확한 진단**에 집중할 수 있었습니다.

**예시**: Run Immutability (INV-3) 불변식의 격차를 식별할 때, "파일 시스템 권한 설정" 같은 해결책을 제안하지 않고, 단순히 "보호 메커니즘 없음"이라는 사실만 기록했습니다.

#### 3. 구조화된 분석 프레임워크 (Structured Analysis Framework)

**기여**: 각 불변식에 대해 다음 구조를 요구했습니다:
- 정의 (Definition)
- 위반 시 재앙적 결과 (Catastrophic Consequences)
- 강제 모듈 식별 (Enforcement Modules)
- 현재 구현 상태 (Current Implementation Status)
- 격차 식별 (Gaps)

**결과**:
- 일관된 형식으로 모든 불변식을 분석할 수 있었습니다.
- 각 불변식의 중요성과 현재 시스템 상태를 명확히 비교할 수 있었습니다.
- 우선순위 설정이 객관적 기준(재앙적 결과의 심각도, 구현 상태)에 기반할 수 있었습니다.

**예시**: Evidence Traceability (INV-1) 불변식에서 "법적 책임"이라는 재앙적 결과를 명시함으로써, 이 불변식이 단순한 "좋은 관행"이 아닌 **시스템 생존에 필수적인 조건**임을 명확히 했습니다.

#### 4. 현재 상태 매핑 요구 (Current State Mapping)

**기여**: "map current AgenticInvest components to these invariants and identify gaps"라는 요구사항이 이론적 분석이 아닌 **실제 코드베이스와의 대조**를 강제했습니다.

**결과**:
- 각 불변식이 실제 코드의 어느 부분과 관련되는지 구체적으로 식별할 수 있었습니다.
- "잘 구현됨", "부분 구현", "미구현"이라는 명확한 상태 분류가 가능했습니다.
- 격차가 단순한 "없음"이 아닌, **구체적인 모듈과 기능**으로 표현되었습니다.

**예시**: Schema Integrity (INV-4) 불변식에서 "Crew 출력 검증 부족"이라는 격차를 식별할 때, `src/crews/` 모듈의 `execute()` 메서드가 Evidence 리스트를 반환하는지 검증하는 로직이 없다는 구체적 사실을 기록했습니다.

#### 5. 실용적 접근 (Pragmatic Approach)

**기여**: 불변식을 "항상 만족해야 하는 조건"으로 정의하고, 위반 시 "재앙적 결과"를 요구함으로써, 이론적이 아닌 **실제 시스템 운영에 필수적인 조건**으로 인식하도록 했습니다.

**결과**:
- 각 불변식이 금융 시스템의 특수성(법적 책임, 규제 준수, 감사 추적)을 반영했습니다.
- "재앙적 결과" 분석이 단순한 기술적 문제가 아닌 **비즈니스 리스크** 관점에서 수행되었습니다.
- 우선순위 설정이 기술적 난이도가 아닌 **비즈니스 영향도**에 기반할 수 있었습니다.

**예시**: Temporal Consistency (INV-6) 불변식에서 "규제 감사 실패"라는 재앙적 결과를 명시함으로써, 이 불변식이 금융 시스템에서 특히 중요한 이유를 명확히 했습니다.

### 프롬프트의 장점 (다른 접근 방식과 비교)

#### 장점 1: 범위 제한의 명확성

**일반적인 프롬프트**: "시스템을 분석하고 개선점을 제안하세요"
- 문제: 분석과 해결책 제안이 혼재되어 집중이 분산됨
- 결과: 불완전한 분석과 성급한 해결책 제안

**이 프롬프트**: "불변식만 정의하고, 격차만 식별하세요. 해결책은 제안하지 마세요"
- 장점: 문제 정의에만 집중하여 깊이 있는 분석 가능
- 결과: 각 불변식의 본질과 현재 시스템의 정확한 상태를 파악

#### 장점 2: 구조화된 분석 프레임워크

**일반적인 프롬프트**: "시스템의 문제점을 나열하세요"
- 문제: 임의적이고 일관성 없는 분석
- 결과: 중요도와 우선순위가 불명확

**이 프롬프트**: "각 불변식에 대해 정의, 재앙적 결과, 강제 모듈, 현재 상태, 격차를 구조화하세요"
- 장점: 모든 불변식을 동일한 기준으로 분석 가능
- 결과: 객관적이고 비교 가능한 분석 결과

#### 장점 3: 구현 전 설계 강제

**일반적인 프롬프트**: "시스템을 개선하세요" (코드 작성 허용)
- 문제: 구현 세부사항에 빠져 설계 원칙을 놓침
- 결과: 임시방편적 해결책과 기술 부채 증가

**이 프롬프트**: "구현이나 기능 제안 전에 불변식을 먼저 정의하세요"
- 장점: 시스템의 본질적 제약 조건에 집중
- 결과: 근본적이고 지속 가능한 설계 원칙 확립

#### 장점 4: 현재 상태와의 대조

**일반적인 프롬프트**: "이상적인 시스템을 설계하세요"
- 문제: 현재 시스템과의 연결 고리가 없음
- 결과: 이론적이고 실행 불가능한 설계

**이 프롬프트**: "현재 컴포넌트를 불변식에 매핑하고 격차를 식별하세요"
- 장점: 현재 시스템의 정확한 상태 파악
- 결과: 실행 가능하고 우선순위가 명확한 개선 계획

#### 장점 5: 비즈니스 리스크 관점

**일반적인 프롬프트**: "기술적 문제를 찾으세요"
- 문제: 기술적 관점에만 집중
- 결과: 비즈니스 영향도를 고려하지 않은 분석

**이 프롬프트**: "위반 시 재앙적 결과를 설명하세요"
- 장점: 기술적 문제를 비즈니스 리스크로 해석
- 결과: 금융 시스템의 특수성(법적 책임, 규제 준수)을 반영한 분석

### 결론: 프롬프트의 핵심 가치

이 프롬프트는 단순한 "분석 요청"이 아닌, **구조화된 설계 방법론**을 제시했습니다:

1. **원칙 우선 (Principles First)**: 구현 전에 불변식 정의
2. **명확한 제약 (Explicit Constraints)**: 범위 제한으로 집중도 향상
3. **구조화된 분석 (Structured Analysis)**: 일관된 프레임워크로 객관적 분석
4. **현실 기반 (Reality-Based)**: 현재 상태와의 대조로 실행 가능성 확보
5. **리스크 중심 (Risk-Centric)**: 재앙적 결과 분석으로 우선순위 명확화

이러한 접근 방식은 특히 **금융 시스템**과 같이 신뢰성, 규정 준수, 감사 추적이 중요한 도메인에서 필수적입니다. 불변식 정의를 통해 시스템의 "절대 지켜야 할 원칙"을 명확히 함으로써, 향후 모든 구현 결정이 이러한 원칙에 기반할 수 있는 기반을 마련했습니다.
