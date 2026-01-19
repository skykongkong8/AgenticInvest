# 반사실적 분석 보고서: AgenticInvest 아키텍처 취약점 분석

## 요약 및 결론

본 보고서는 다음 반사실적 가정 하에서 AgenticInvest 시스템의 아키텍처 취약점을 분석합니다:
- ❌ LLM이 추론 일관성에서 신뢰할 수 없음
- ❌ 모델 출력이 동일한 입력에 대해 모순됨
- ❌ 도구 호출이 조용히 실패함

**핵심 결론**: 현재 시스템은 LLM의 신뢰성과 일관성을 암묵적으로 가정하고 있어, 이러한 가정이 거짓일 경우 **증거 수집 단계부터 최종 판단 단계까지 전반적으로 실패**합니다. 특히 **Synthesizer의 문자열 파싱 로직**, **TriggerEngine의 결정론적 평가**, **VerdictEngine의 점수 기반 판단**이 가장 먼저 깨집니다.

---

## 0. 반사실적 분석 프롬프트 엔지니어링 기법의 효율성

본 보고서는 **반사실적 분석(Counterfactual Analysis)** 프롬프트 기법을 사용하여 작성되었습니다. 이 기법이 다른 프롬프팅 접근법에 비해 효율적인 이유를 분석합니다.

### 0.1 사용된 프롬프트 기법의 핵심 요소

본 분석에 사용된 프롬프트는 다음 요소들을 포함합니다:

1. **명시적 반사실적 가정 설정**
   - "LLM이 신뢰할 수 없다"는 가정을 명시적으로 TRUE로 설정
   - "Do NOT describe the current system optimistically" 지시로 낙관적 편향 제거

2. **암묵적 가정 식별 요구**
   - "현재 설계가 암묵적으로 의존하는 가정"을 명시적으로 요구
   - 시스템의 숨겨진 전제를 드러내도록 강제

3. **실패 시나리오 우선순위화**
   - "먼저 깨지는 부분"을 식별하도록 요구
   - 취약점의 심각도를 자동으로 분류

4. **재설계 요구사항 명시**
   - "재설계가 필요한 부분"을 구분하도록 요구
   - 해결책을 구체적으로 제시하도록 유도

### 0.2 다른 프롬프팅 기법과의 비교

#### 비교 1: 직접적 분석 요청 vs 반사실적 분석

**직접적 분석 프롬프트 예시**:
```
"AgenticInvest 시스템의 아키텍처를 분석하고 개선점을 제시하세요."
```

**문제점**:
- LLM이 시스템의 장점을 과도하게 강조하는 경향
- 암묵적 가정을 그대로 받아들이고 분석
- 실제 취약점보다 이론적 개선점에 집중
- 방어적 설계보다는 기능 추가에 초점

**반사실적 분석의 장점**:
- 시스템이 실패하는 시나리오를 강제로 탐색
- 암묵적 가정을 명시적으로 드러냄
- 실제 운영 환경의 불확실성을 반영
- 방어적 설계를 자연스럽게 유도

#### 비교 2: 단순 질문 기반 vs 구조화된 반사실적 분석

**단순 질문 프롬프트 예시**:
```
"시스템의 문제점은 무엇인가요? 어떻게 개선할 수 있나요?"
```

**문제점**:
- 질문이 추상적이어서 구체적인 답변을 얻기 어려움
- 분석의 깊이가 일관되지 않음
- 우선순위가 불명확함
- 가정과 결론이 혼재됨

**반사실적 분석의 장점**:
- 구체적인 실패 시나리오를 가정하여 분석 시작
- "먼저 깨지는 부분" 식별로 우선순위 자동 설정
- 암묵적 가정 → 실패 시나리오 → 해결책의 명확한 흐름
- 각 단계가 논리적으로 연결됨

#### 비교 3: 긍정적 프레이밍 vs 부정적 프레이밍

**긍정적 프레이밍 예시**:
```
"시스템을 더 견고하게 만들기 위한 방법을 제시하세요."
```

**문제점**:
- 현재 시스템의 문제를 간과할 수 있음
- "더 나은" 기능에 집중하여 근본적 취약점을 놓침
- 점진적 개선에 초점하여 급격한 실패 시나리오를 고려하지 않음

**반사실적 분석의 장점**:
- "가정이 거짓일 경우"를 명시하여 급격한 실패 시나리오 탐색
- 현재 시스템의 근본적 취약점을 먼저 식별
- 방어적 설계가 자연스럽게 도출됨

### 0.3 반사실적 분석 기법의 효율성 메커니즘

#### 1. 인지적 편향 제거

**낙관적 편향 제거**:
- "Do NOT describe optimistically" 지시로 LLM의 긍정적 편향 억제
- 시스템의 문제점을 객관적으로 분석하도록 강제

**확증 편향 제거**:
- 반사실적 가정을 TRUE로 설정하여 현재 설계를 의심하도록 유도
- 암묵적 가정을 명시적으로 드러내어 검증 가능하게 만듦

#### 2. 체계적 취약점 탐색

**우선순위 자동 설정**:
- "먼저 깨지는 부분" 식별로 Critical Path 자동 탐지
- Synthesizer → TriggerEngine → VerdictEngine 순서로 실패 전파 분석

**연쇄 실패 시나리오 발견**:
- 단일 컴포넌트 실패가 전체 시스템에 미치는 영향 추적
- 예: Synthesizer 파싱 실패 → 신호 누락 → 트리거 미발동 → 증거 부족

#### 3. 구체적 해결책 도출

**재설계 요구사항 명시**:
- "재설계가 필요한 부분"을 구분하여 즉시/중기/장기 우선순위 설정
- 각 컴포넌트별로 구체적인 변경 방안 제시

**방어적 설계 유도**:
- 실패 시나리오를 가정하므로 자연스럽게 견고성 메커니즘 도입
- 예: 도구 호출 실패 → 재시도 메커니즘, Evidence 모순 → 일관성 검증

### 0.4 실제 분석 결과에서 드러난 효율성

본 분석에서 반사실적 프롬프트 기법이 효과적으로 작동한 사례:

1. **암묵적 가정의 명시화**
   - "LLM이 일관된 형식으로 출력 생성"이라는 가정을 명시적으로 식별
   - 이 가정이 Synthesizer의 문자열 파싱 로직에 의존하고 있음을 발견

2. **실패 시나리오의 구체화**
   - 단순히 "파싱이 실패할 수 있다"가 아닌, "파싱 실패 → `volatility = None` → 트리거 미발동"의 연쇄 실패 시나리오 도출

3. **우선순위의 자동 설정**
   - Synthesizer가 "최우선 실패"로 식별되어 즉시 재설계 필요 항목으로 분류

4. **구체적 해결책 제시**
   - 단순한 "개선 필요"가 아닌, `StructuredEvidence` 스키마 도입과 같은 구체적 변경 방안 제시

### 0.5 다른 프롬프팅 기법 대비 효율성 지표

| 측면 | 직접적 분석 | 단순 질문 | 반사실적 분석 |
|------|------------|----------|--------------|
| 암묵적 가정 식별 | ⚠️ 부분적 | ❌ 미흡 | ✅ 체계적 |
| 실패 시나리오 탐색 | ⚠️ 제한적 | ⚠️ 추상적 | ✅ 구체적 |
| 우선순위 설정 | ⚠️ 수동 | ❌ 불명확 | ✅ 자동 |
| 해결책 구체성 | ⚠️ 일반적 | ⚠️ 모호함 | ✅ 구체적 |
| 방어적 설계 유도 | ❌ 미흡 | ⚠️ 부분적 | ✅ 자연스러움 |
| 분석 깊이 | ⚠️ 중간 | ⚠️ 얕음 | ✅ 깊음 |

### 0.6 반사실적 분석 기법의 적용 범위

이 기법은 다음 상황에서 특히 효율적입니다:

1. **복잡한 시스템의 취약점 분석**
   - 여러 컴포넌트가 상호 의존하는 시스템
   - 암묵적 가정이 많은 레거시 시스템

2. **운영 환경의 불확실성 고려**
   - 외부 의존성(LLM, API 등)이 있는 시스템
   - 실패 모드가 다양하고 예측하기 어려운 시스템

3. **방어적 설계가 중요한 시스템**
   - 금융, 의료 등 고신뢰성 시스템
   - 실패 시 큰 손실이 발생하는 시스템

### 0.7 결론: 반사실적 분석 프롬프트 기법의 핵심 가치

반사실적 분석 프롬프트 기법은 다음과 같은 이유로 효율적입니다:

1. **인지적 편향 제거**: 낙관적 편향과 확증 편향을 억제하여 객관적 분석 유도
2. **체계적 탐색**: 암묵적 가정 → 실패 시나리오 → 해결책의 명확한 분석 흐름
3. **구체적 결과**: 추상적 개선점이 아닌, 즉시 적용 가능한 구체적 변경 방안 도출
4. **방어적 설계**: 실패를 가정하므로 자연스럽게 견고성 메커니즘 도입

이 기법은 특히 **LLM 기반 시스템의 아키텍처 분석**에 적합하며, LLM 자체의 불확실성을 시스템 설계에 반영하는 데 효과적입니다.

---

## 1. 현재 아키텍처가 암묵적으로 의존하는 가정

### 1.1 LLM 신뢰성 가정

현재 시스템은 다음을 암묵적으로 가정합니다:

1. **일관된 출력 형식**: LLM이 동일한 입력에 대해 일관된 구조의 출력을 생성함
2. **신뢰할 수 있는 추론**: LLM의 추론이 논리적으로 일관됨
3. **도구 호출 성공**: 도구 호출 실패 시 예외가 발생하거나 명시적으로 처리됨

### 1.2 현재 설계의 핵심 의존성

```43:93:src/orchestrator/flow.py
    def run(self, ticker: str, horizon: str, risk_profile: str) -> str:
        run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ticker}"
        run_dir = f"runs/{run_id}"
        os.makedirs(run_dir, exist_ok=True)
        
        request = RequestInput(ticker=ticker, horizon=horizon, risk_profile=risk_profile)
        self._log_event(run_dir, "RUN_STARTED", {"ticker": ticker, "run_id": run_id})
        
        # 1. Plan
        plan = self.planner.create_base_plan(request)
        self._log_event(run_dir, "PLAN_CREATED", {"task_count": len(plan.tasks)})
        write_json(f"{run_dir}/plan.json", plan.model_dump())
        
        # 2. Execute Base Plan
        evidences = self._execute_tasks(plan.tasks, run_dir)
        
        # 3. Synthesis & Triggers
        signals = self.synthesizer.build_signals(evidences)
        new_tasks = self.triggers.evaluate(request, evidences, signals)
        
        if new_tasks:
            self._log_event(run_dir, "TRIGGERS_FIRED", {"new_tasks": [t.name for t in new_tasks]})
            new_evidences = self._execute_tasks(new_tasks, run_dir)
            evidences.extend(new_evidences)
            
            # Re-synthesize
            signals = self.synthesizer.build_signals(evidences)
            
        write_json(f"{run_dir}/evidence.json", [e.model_dump() for e in evidences])
        
        # 4. Verdict
        verdict_label, rationale, confidence = self.verdict_engine.compute_verdict(signals, evidences)
        
        report = VerdictReport(
            request=request,
            signals=signals,
            research_plan=plan, # Note via basic plan, in real app update with new tasks
            evidence=evidences,
            verdict=verdict_label,
            rationale=rationale,
            risks=signals.news_red_flags,
            next_actions=["Monitor earnings", "Check regulatory updates"]
        )
        
        # 5. Output
        write_json(f"{run_dir}/final_report.json", report.model_dump())
        self._render_markdown(f"{run_dir}/final_report.md", report)
        
        self._log_event(run_dir, "run_COMPLETE", {"verdict": verdict_label})
        logger.info(f"Run completed. Verdict: {verdict_label}. Output: {run_dir}")
        return run_dir
```

현재 설계는 다음을 가정합니다:
- `_execute_tasks`가 항상 유효한 Evidence 리스트를 반환함
- `build_signals`가 일관된 Signals 객체를 생성함
- `compute_verdict`가 결정론적 판단을 수행함

---

## 2. 반사실적 가정 하에서 먼저 깨지는 부분

### 2.1 Synthesizer의 문자열 파싱 로직 (최우선 실패)

```22:36:src/orchestrator/synthesis.py
        for ev in evidences:
            # 1. Parse Volatility/Drawdown (Price)
            if "volatility" in ev.tags and "Volatility for" in ev.claim:
                try:
                    val_str = ev.claim.split(" is ")[-1].replace("%", "")
                    volatility = float(val_str) / 100.0
                except:
                    pass
            
            if "drawdown" in ev.tags and "drawdown for" in ev.claim:
                    try:
                         val_str = ev.claim.split(" is ")[-1].replace("%", "")
                         drawdown = float(val_str) / 100.0
                    except:
                        pass
```

**문제점**:
- LLM이 일관되지 않은 형식으로 `claim`을 생성하면 파싱이 실패함
- 예: "Volatility for AAPL is 25%" vs "AAPL volatility: 0.25" vs "25% volatility observed"
- `except: pass`로 인해 조용히 실패하여 `volatility = None`이 됨
- 이후 TriggerEngine이 `volatility_20d`를 확인할 때 `None`이므로 트리거가 발동하지 않음

**실패 시나리오**:
1. LLM이 모순된 형식으로 Evidence 생성
2. Synthesizer가 파싱 실패 → `volatility = None`
3. TriggerEngine이 `signals.volatility_20d > 0.40` 체크 시 `None > 0.40` → `False`
4. 고변동성 상황임에도 추가 분석이 트리거되지 않음

### 2.2 Crew의 도구 호출 실패 처리 부재

```95:109:src/orchestrator/flow.py
    def _execute_tasks(self, tasks: List[ResearchTaskSpec], run_dir: str) -> List[Evidence]:
        results = []
        for task in tasks:
            logger.info(f"Executing task: {task.name} with {task.crew}")
            self._log_event(run_dir, "TASK_STARTED", {"task": task.name})
            
            crew_inst = self.crews.get(task.crew)
            if crew_inst:
                task_evidences = crew_inst.execute(task.inputs)
                results.extend(task_evidences)
                self._log_event(run_dir, "TASK_FINISHED", {"task": task.name, "evidence_count": len(task_evidences)})
            else:
                logger.error(f"Crew {task.crew} not found!")
                
        return results
```

**문제점**:
- `crew_inst.execute()`가 조용히 실패하면 빈 리스트를 반환할 수 있음
- 도구 호출 실패 시 예외가 발생하지 않으면 시스템이 실패를 감지하지 못함
- 예: `fetch_prices()`가 네트워크 오류로 `None` 반환 → `compute_volatility(None)` → 예외 발생 가능

```7:12:src/crews/price_crew.py
    def execute(self, inputs: dict) -> list[Evidence]:
        ticker = inputs.get("ticker", "UNKNOWN")
        prices = fetch_prices(ticker)
        
        volatility = compute_volatility(prices)
        drawdown = compute_drawdown(prices)
```

**실패 시나리오**:
1. `fetch_prices()`가 조용히 `None` 반환 (네트워크 타임아웃, API 키 만료 등)
2. `compute_volatility(None)` 호출 → `TypeError: 'NoneType' object is not iterable`
3. 예외가 처리되지 않으면 전체 워크플로우 중단
4. 또는 예외가 처리되어 빈 Evidence 리스트 반환 → 증거 부족

### 2.3 VerdictEngine의 키워드 기반 분류 (모순 증거 처리 불가)

```38:46:src/orchestrator/verdict.py
        for ev in evidences:
            cid = f"[{ev.id[:6]}"
            
            # Map evidence to bull/bear based on content (naive keyword matching)
            # In a real system, the Synthesizer would tag evidence as supporting bull or bear
            if "undervalued" in ev.claim or "positive" in ev.claim or "Buy" in ev.claim:
                rationale["bull_case"].append(f"{ev.claim} {cid}")
            elif "overvalued" in ev.claim or "negative" in ev.claim or "risk" in ev.claim or "red flags" in ev.claim:
                rationale["bear_case"].append(f"{ev.claim} {cid}")
```

**문제점**:
- LLM이 모순된 증거를 생성하면 (예: "undervalued"와 "overvalued"를 동시에 포함) 둘 다 bull_case에 추가됨
- 키워드 매칭은 모순을 감지하지 못함
- 동일한 Evidence가 여러 번 처리되면 중복 추가됨

**실패 시나리오**:
1. LLM이 "AAPL is undervalued but faces overvalued risk" 같은 모순된 claim 생성
2. `"undervalued" in ev.claim` → `True` → bull_case 추가
3. `"overvalued" in ev.claim` → `True` → bear_case 추가 (하지만 이미 bull_case에 추가됨)
4. 최종 판단이 모순된 근거로 인해 왜곡됨

### 2.4 TriggerEngine의 결정론적 평가 (신뢰할 수 없는 신호 기반)

```12:25:src/orchestrator/triggers.py
    def evaluate(self, request: RequestInput, evidences: List[Evidence], signals: Signals) -> List[ResearchTaskSpec]:
        new_tasks = []
        
        # 1. Volatility Spike
        if signals.volatility_20d and signals.volatility_20d > 0.40: # 40% threshold example
            logger.info("TRIGGER: Volatility spike detected")
            new_tasks.append(ResearchTaskSpec(
                id=str(uuid4()),
                name="options_liquidity_analysis",
                description="Investigate options flow and liquidity due to high volatility.",
                crew="OptionsLiquidityCrew",
                inputs={"ticker": request.ticker},
                parallelizable=False
            ))
```

**문제점**:
- `signals.volatility_20d`가 `None`이거나 잘못된 값이면 트리거가 발동하지 않음
- Synthesizer가 파싱 실패로 `None`을 반환하면 중요한 트리거가 누락됨
- LLM이 일관되지 않은 Evidence를 생성하면 신호 계산이 왜곡됨

---

## 3. 견고성 개선을 위한 아키텍처 변경 제안

### 3.1 증거 검증 및 정규화 레이어 추가

**현재 문제**: Evidence의 `claim` 필드가 LLM에 의해 자유 형식으로 생성되어 파싱이 불안정함

**해결책**: Evidence 생성 시점에 구조화된 스키마로 강제

```python
# 새로운 스키마: StructuredEvidence
class StructuredEvidence(BaseModel):
    id: str
    source_type: str
    source_ref: str
    # 구조화된 필드들
    metric_name: str  # "volatility", "sentiment", "valuation" 등
    metric_value: float
    metric_unit: str  # "percentage", "score", "count" 등
    direction: Literal["bullish", "bearish", "neutral"]
    confidence: float
    raw_claim: str  # 원본 LLM 출력 (참고용)
    timestamp: datetime
    tags: List[str]
```

**구현 위치**: 각 Crew의 `execute()` 메서드에서 LLM 출력을 `StructuredEvidence`로 변환하는 검증 레이어 추가

### 3.2 도구 호출 실패 감지 및 재시도 메커니즘

**현재 문제**: 도구 호출이 조용히 실패하면 시스템이 감지하지 못함

**해결책**: 명시적 실패 처리 및 재시도

```python
# 새로운 컴포넌트: ToolExecutionWrapper
class ToolExecutionWrapper:
    def __init__(self, max_retries: int = 3, timeout: float = 30.0):
        self.max_retries = max_retries
        self.timeout = timeout
    
    def execute_with_validation(self, tool_func, *args, **kwargs):
        """도구 호출을 래핑하여 실패를 명시적으로 처리"""
        for attempt in range(self.max_retries):
            try:
                result = tool_func(*args, **kwargs)
                # 결과 검증
                if result is None:
                    raise ValueError(f"Tool {tool_func.__name__} returned None")
                return result
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # 최종 실패 시 Evidence로 기록
                    return self._create_failure_evidence(tool_func.__name__, str(e))
                time.sleep(2 ** attempt)  # 지수 백오프
```

**구현 위치**: `PriceCrew`, `NewsCrew` 등에서 도구 호출 시 래퍼 사용

### 3.3 증거 일관성 검증 및 모순 해결 메커니즘

**현재 문제**: 모순된 Evidence가 그대로 최종 판단에 반영됨

**해결책**: Evidence 일관성 검증 및 투표 메커니즘

```python
# 새로운 컴포넌트: EvidenceConsistencyChecker
class EvidenceConsistencyChecker:
    def check_contradictions(self, evidences: List[Evidence]) -> Dict[str, List[Evidence]]:
        """모순된 Evidence 그룹을 식별"""
        contradictions = {}
        
        # 동일한 metric_name에 대해 반대 방향의 Evidence 찾기
        metric_groups = {}
        for ev in evidences:
            key = ev.metric_name
            if key not in metric_groups:
                metric_groups[key] = {"bullish": [], "bearish": []}
            metric_groups[key][ev.direction].append(ev)
        
        # 모순 감지
        for metric, groups in metric_groups.items():
            if groups["bullish"] and groups["bearish"]:
                contradictions[metric] = groups["bullish"] + groups["bearish"]
        
        return contradictions
    
    def resolve_contradiction(self, contradictory_evidences: List[Evidence]) -> Evidence:
        """모순을 해결하는 전략 (신뢰도 기반, 시간 기반, 소스 기반)"""
        # 신뢰도가 높은 Evidence 우선
        sorted_ev = sorted(contradictory_evidences, key=lambda x: x.confidence, reverse=True)
        return sorted_ev[0]  # 또는 더 복잡한 투표 메커니즘
```

**구현 위치**: `Synthesizer.build_signals()` 호출 전에 `EvidenceConsistencyChecker` 실행

### 3.4 신호 계산의 견고성 강화

**현재 문제**: 문자열 파싱에 의존하여 신호 계산이 불안정함

**해결책**: 구조화된 Evidence 기반의 결정론적 계산

```python
# 개선된 Synthesizer
class RobustSynthesizer:
    def build_signals(self, evidences: List[StructuredEvidence]) -> Signals:
        # 구조화된 필드에서 직접 추출 (파싱 불필요)
        volatility_evidences = [e for e in evidences if e.metric_name == "volatility"]
        sentiment_evidences = [e for e in evidences if e.metric_name == "sentiment"]
        
        # 통계적 집계 (평균, 중앙값, 신뢰도 가중 평균 등)
        if volatility_evidences:
            # 신뢰도 가중 평균
            total_weight = sum(e.confidence for e in volatility_evidences)
            volatility = sum(e.metric_value * e.confidence for e in volatility_evidences) / total_weight
        else:
            volatility = None
        
        # 모순 감지
        contradiction_score = self._compute_contradiction_score(evidences)
        
        return Signals(
            volatility_20d=volatility,
            # ... 다른 필드들
            conflict_score=contradiction_score
        )
```

### 3.5 트리거 평가의 견고성 강화

**현재 문제**: `None` 값이나 잘못된 신호로 인해 트리거가 누락됨

**해결책**: 신호 유효성 검증 및 폴백 메커니즘

```python
# 개선된 TriggerEngine
class RobustTriggerEngine:
    def evaluate(self, request: RequestInput, evidences: List[Evidence], signals: Signals) -> List[ResearchTaskSpec]:
        new_tasks = []
        
        # 신호 유효성 검증
        if not self._is_signal_valid(signals):
            # 신호가 유효하지 않으면 기본 트리거 발동
            return self._get_fallback_tasks(request)
        
        # Volatility Spike (개선된 검증)
        if signals.volatility_20d is not None and signals.volatility_20d > 0.40:
            # 추가 검증: Evidence 개수 확인
            volatility_ev_count = len([e for e in evidences if "volatility" in e.tags])
            if volatility_ev_count >= 1:  # 최소 1개 이상의 증거 필요
                new_tasks.append(...)
        
        return new_tasks
    
    def _is_signal_valid(self, signals: Signals) -> bool:
        """신호 객체의 유효성 검증"""
        # 필수 필드가 None이 아니고, 합리적인 범위 내에 있는지 확인
        return (
            signals.volatility_20d is None or 0 <= signals.volatility_20d <= 10.0  # 1000% 이하
            and signals.sentiment_score is None or -1.0 <= signals.sentiment_score <= 1.0
            # ... 다른 검증
        )
```

### 3.6 최종 판단의 견고성 강화

**현재 문제**: 모순된 Evidence가 그대로 반영되고, 키워드 매칭이 불안정함

**해결책**: 구조화된 Evidence 기반의 투표 메커니즘

```python
# 개선된 VerdictEngine
class RobustVerdictEngine:
    def compute_verdict(self, signals: Signals, evidences: List[StructuredEvidence]) -> Tuple[Verdict, Dict, float]:
        # 구조화된 Evidence에서 직접 방향성 추출
        bullish_count = sum(1 for e in evidences if e.direction == "bullish")
        bearish_count = sum(1 for e in evidences if e.direction == "bearish")
        
        # 신뢰도 가중 투표
        bullish_weight = sum(e.confidence for e in evidences if e.direction == "bullish")
        bearish_weight = sum(e.confidence for e in evidences if e.direction == "bearish")
        
        # 모순 점수 반영
        if signals.conflict_score > 0.5:
            # 모순이 높으면 HOLD로 강제
            return Verdict.HOLD, {"reason": "High contradiction detected"}, 0.3
        
        # 점수 계산 (구조화된 방식)
        score = (bullish_weight - bearish_weight) / max(len(evidences), 1)
        
        # ... 나머지 로직
```

---

## 4. 재설계가 필요한 핵심 컴포넌트

### 4.1 즉시 재설계 필요 (Critical)

1. **Synthesizer** (`src/orchestrator/synthesis.py`)
   - 현재: 문자열 파싱 기반
   - 필요: 구조화된 Evidence 기반 결정론적 계산

2. **Evidence 스키마** (`src/schemas/evidence.py`)
   - 현재: 자유 형식 `claim` 필드
   - 필요: 구조화된 `metric_name`, `metric_value`, `direction` 필드

3. **Crew 실행 래퍼** (새로 생성)
   - 현재: 도구 호출 실패 처리 없음
   - 필요: 명시적 실패 감지 및 재시도

### 4.2 중기 재설계 필요 (High Priority)

4. **VerdictEngine** (`src/orchestrator/verdict.py`)
   - 현재: 키워드 매칭 기반
   - 필요: 구조화된 Evidence 기반 투표 메커니즘

5. **TriggerEngine** (`src/orchestrator/triggers.py`)
   - 현재: 단순 조건 체크
   - 필요: 신호 유효성 검증 및 폴백 메커니즘

6. **EvidenceConsistencyChecker** (새로 생성)
   - 현재: 없음
   - 필요: 모순 감지 및 해결 메커니즘

### 4.3 장기 개선 (Medium Priority)

7. **로깅 및 모니터링**
   - LLM 출력 불일치 감지
   - 도구 호출 실패율 추적
   - Evidence 모순 빈도 모니터링

8. **A/B 테스트 및 검증**
   - 동일 입력에 대한 여러 실행 결과 비교
   - 일관성 메트릭 수집

---

## 5. 현재 설계의 암묵적 가정 vs 반사실적 현실

| 현재 설계의 암묵적 가정 | 반사실적 현실 | 영향 |
|------------------------|--------------|------|
| LLM이 일관된 형식으로 출력 생성 | 출력 형식이 매번 다름 | Synthesizer 파싱 실패 |
| LLM 추론이 논리적으로 일관됨 | 모순된 추론 생성 | Evidence 모순 누적 |
| 도구 호출 실패 시 예외 발생 | 조용히 `None` 반환 | 증거 부족 또는 예외 발생 |
| Evidence의 `claim`이 파싱 가능 | 자유 형식으로 생성 | 신호 계산 실패 |
| 신호가 항상 유효함 | `None` 또는 잘못된 값 | 트리거 누락 |
| 모순이 자동으로 해결됨 | 모순이 누적됨 | 최종 판단 왜곡 |

---

## 6. 구현 우선순위

### Phase 1: 즉시 적용 (1-2주)
1. `StructuredEvidence` 스키마 도입
2. Crew 실행 래퍼 추가 (도구 호출 실패 처리)
3. Synthesizer를 구조화된 Evidence 기반으로 변경

### Phase 2: 단기 개선 (1개월)
4. EvidenceConsistencyChecker 구현
5. VerdictEngine을 구조화된 Evidence 기반으로 변경
6. TriggerEngine 신호 유효성 검증 추가

### Phase 3: 장기 개선 (2-3개월)
7. 모니터링 및 메트릭 수집 시스템
8. A/B 테스트 프레임워크
9. 자동 일관성 검증 파이프라인

---

## 결론

현재 AgenticInvest 아키텍처는 **LLM의 신뢰성과 일관성을 암묵적으로 가정**하고 있어, 반사실적 가정 하에서 **Synthesizer의 문자열 파싱 로직이 가장 먼저 실패**하고, 이로 인해 **전체 워크플로우가 연쇄적으로 실패**합니다.

핵심 해결책은 **구조화된 Evidence 스키마 도입**과 **명시적 실패 처리 메커니즘**입니다. 이를 통해 LLM의 불일치를 시스템 레벨에서 흡수하고, 견고한 투표 및 집계 메커니즘으로 최종 판단의 신뢰성을 확보할 수 있습니다.
