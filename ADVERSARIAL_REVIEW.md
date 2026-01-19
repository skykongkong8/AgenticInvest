# AgenticInvest 적대적 리뷰 (Adversarial Review)

**검토 일자**: 2024-01-15  
**검토 목적**: 프로덕션 배포 전 시스템 취약점 식별  
**가정**: 작성자들이 과신하고 있으며, 모호한 추상화는 설계 결함을 숨기고 있다.

---

## 요약

이 시스템은 **금융 의사결정을 자동화**한다고 주장하지만, 실제로는 **LLM 출력을 맹신하고 문자열 파싱에 의존하는 취약한 파이프라인**이다. 최소 7개의 치명적 약점이 식별되었으며, 각각은 **실제 금융 손실이나 시스템 실패**를 초래할 수 있다.

---

## 치명적 약점 #1: 문자열 파싱에 의존한 신호 추출

### 위치
```24:36:src/orchestrator/synthesis.py
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

### 문제점
- **Evidence의 `claim` 필드를 문자열 파싱**하여 숫자 값을 추출한다.
- LLM이 "Volatility for TSLA over 20 days is approximately 45.2%"라고 생성하면 파싱이 실패한다.
- "is"가 claim에 여러 번 나타나면 잘못된 값을 추출한다.
- 파싱 실패 시 **조용히 무시**되어 (`except: pass`) 신호가 `None`으로 남는다.

### 금융 손실 시나리오
1. 변동성 파싱 실패 → `volatility_20d = None` → 변동성 리스크 계산 스킵
2. 실제 변동성이 60%인데 시스템이 이를 감지하지 못함
3. VerdictEngine이 변동성 리스크를 고려하지 않아 **과도하게 낙관적인 BUY 판단**
4. 사용자가 고변동성 주식에 투자하여 예상치 못한 손실 발생

### 암묵적 가정
- LLM이 항상 "X is Y%" 형식으로 출력한다고 가정
- 파싱 실패가 예외 상황이 아니라 정상적인 경우일 수 있다는 것을 무시

---

## 치명적 약점 #2: 에러 처리 부재 - Crew 실행 실패 시 시스템이 계속 진행

### 위치
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

### 문제점
- Crew가 존재하지 않으면 **로그만 남기고 계속 진행**
- `crew_inst.execute()`가 예외를 발생시키면 **전체 파이프라인이 중단**됨
- 일부 Crew가 실패해도 **부분적 증거로 판단을 내림**
- **타임아웃 메커니즘 없음** - LLM API 호출이 무한정 대기할 수 있음

### 금융 손실 시나리오
1. NewsCrew가 API 호출 실패 (네트워크 오류, API 키 만료)
2. 시스템이 뉴스 증거 없이 계속 진행
3. 중요한 부정적 뉴스(예: SEC 조사 시작)를 놓침
4. 시스템이 **불완전한 정보로 BUY 판단**
5. 사용자가 조사가 시작된 주식에 투자하여 규제 리스크로 인한 손실

### 암묵적 가정
- 모든 Crew가 항상 성공한다고 가정
- 부분적 실패가 전체 시스템을 무효화해야 한다는 것을 무시

---

## 치명적 약점 #3: 임의의 하드코딩된 임계값 - 근거 없는 결정 경계

### 위치
```16:16:src/orchestrator/triggers.py
if signals.volatility_20d and signals.volatility_20d > 0.40: # 40% threshold example
```

```13:18:src/orchestrator/verdict.py
if signals.sentiment_score > 0.3:
    score += 1.0
    rationale["bull_case"].append(f"Strong positive sentiment ({signals.sentiment_score:.2f}).")
elif signals.sentiment_score < -0.3:
    score -= 1.0
    rationale["bear_case"].append(f"Negative sentiment ({signals.sentiment_score:.2f}).")
```

```51:60:src/orchestrator/verdict.py
if score >= 1.5:
    verdict = Verdict.STRONG_BUY
elif score >= 0.5:
    verdict = Verdict.BUY
elif score <= -1.5:
    verdict = Verdict.STRONG_SELL
elif score <= -0.5:
    verdict = Verdict.SELL
else:
    verdict = Verdict.HOLD
```

### 문제점
- **40% 변동성 임계값**이 왜 40%인지 문서화되지 않음
- **0.3 감정 점수 임계값**이 왜 0.3인지 근거 없음
- **1.5 점수 임계값**이 왜 1.5인지 설명 없음
- `configs/thresholds.yaml`이 존재하지만 **실제로 사용되지 않음**

### 금융 손실 시나리오
1. 보수적 투자자가 시스템을 사용
2. 시스템의 임계값이 공격적 투자자용으로 설정됨
3. 변동성 35% 주식이 "안전"하다고 판단 (40% 미만)
4. 보수적 투자자에게는 여전히 위험한 수준
5. **리스크 프로필과 무관하게 동일한 임계값 적용**으로 부적절한 투자 권고

### 암묵적 가정
- 모든 투자자가 동일한 리스크 허용도를 가진다고 가정
- `risk_profile` 파라미터가 실제로 사용되지 않음

---

## 치명적 약점 #4: 신뢰도(Confidence) 계산의 일관성 부재

### 위치
```14:23:src/crews/price_crew.py
evidences.append(Evidence(
    id=str(uuid4()),
    source_type="price",
    source_ref="mock_price_feed",
    claim=f"Volatility for {ticker} is {volatility:.2%}",
    confidence=0.95,
    raw_snippet=str(prices[-5:]),
    tags=["volatility", "risk"]
))
```

```15:22:src/crews/news_crew.py
evidences.append(Evidence(
    id=str(uuid4()),
    source_type="news",
    source_ref="mock_news_api",
    claim=f"Found {len(news_items)} recent articles for {ticker}",
    confidence=0.8,
    tags=["volume", "sentiment"]
))
```

```49:49:src/orchestrator/verdict.py
confidence = max(0.0, 1.0 - signals.uncertainty)
```

### 문제점
- 각 Crew가 **임의로 confidence 값을 하드코딩**
- PriceCrew는 0.95, NewsCrew는 0.8 - **근거 없음**
- VerdictEngine의 confidence는 `1.0 - uncertainty`로 계산되지만, **uncertainty 계산도 임의적**
- **동일한 증거라도 Crew마다 다른 confidence 부여**

### 금융 손실 시나리오
1. NewsCrew가 부정확한 뉴스를 confidence 0.8로 보고
2. PriceCrew가 정확한 가격 데이터를 confidence 0.95로 보고
3. VerdictEngine이 두 증거를 동등하게 취급하지 않지만, **confidence 차이가 실제 정확도를 반영하지 않음**
4. 부정확한 뉴스 기반 판단이 높은 confidence로 표시됨
5. 사용자가 **과신하여 잘못된 투자 결정**

### 암묵적 가정
- 모든 Crew가 동일한 기준으로 confidence를 계산한다고 가정
- Confidence가 실제 정확도를 반영한다고 가정

---

## 치명적 약점 #5: 증거(Evidence) 검증 부재 - LLM 출력을 사실로 취급

### 위치
```38:46:src/orchestrator/verdict.py
for ev in evidences:
    cid = f"[{ev.id[:6]}]"
    
    # Map evidence to bull/bear based on content (naive keyword matching)
    # In a real system, the Synthesizer would tag evidence as supporting bull or bear
    if "undervalued" in ev.claim or "positive" in ev.claim or "Buy" in ev.claim:
        rationale["bull_case"].append(f"{ev.claim} {cid}")
    elif "overvalued" in ev.claim or "negative" in ev.claim or "risk" in ev.claim or "red flags" in ev.claim:
        rationale["bear_case"].append(f"{ev.claim} {cid}")
```

### 문제점
- **Evidence의 `claim` 필드를 검증하지 않음**
- LLM이 "TSLA is undervalued"라고 생성하면 그대로 사실로 취급
- `source_ref`가 있지만 **실제 데이터 소스와의 일치 여부를 확인하지 않음**
- `raw_snippet`이 있어도 **claim이 snippet과 일치하는지 검증하지 않음**

### 금융 손실 시나리오
1. NewsCrew가 LLM을 사용하여 뉴스 요약 생성
2. LLM이 환각(hallucination)으로 "SEC가 TSLA에 대해 긍정적 발표"라고 잘못 생성
3. 시스템이 이를 confidence 0.8로 Evidence로 저장
4. VerdictEngine이 "positive" 키워드로 인해 bull_case에 추가
5. **거짓 정보 기반으로 BUY 판단**
6. 사용자가 실제로는 부정적 뉴스인 주식에 투자

### 암묵적 가정
- LLM 출력이 항상 정확하다고 가정
- `source_ref`가 실제로 존재하고 접근 가능하다고 가정
- `claim`이 `raw_snippet`과 일치한다고 가정

---

## 치명적 약점 #6: 트리거 무한 루프 가능성 - 동적 작업 생성의 제어 부재

### 위치
```12:53:src/orchestrator/triggers.py
def evaluate(self, request: RequestInput, evidences: List[Evidence], signals: Signals) -> List[ResearchTaskSpec]:
    new_tasks = []
    
    # 1. Volatility Spike
    if signals.volatility_20d and signals.volatility_20d > 0.40:
        logger.info("TRIGGER: Volatility spike detected")
        new_tasks.append(ResearchTaskSpec(...))
    
    # 2. Legal/Regulatory
    if signals.news_red_flags:
        logger.info("TRIGGER: Legal/Regulatory red flags detected")
        new_tasks.append(ResearchTaskSpec(...))
    
    # 3. Insufficient Evidence
    if len(evidences) < 3:
         new_tasks.append(ResearchTaskSpec(...))
            
    return new_tasks
```

```63:69:src/orchestrator/flow.py
if new_tasks:
    self._log_event(run_dir, "TRIGGERS_FIRED", {"new_tasks": [t.name for t in new_tasks]})
    new_evidences = self._execute_tasks(new_tasks, run_dir)
    evidences.extend(new_evidences)
    
    # Re-synthesize
    signals = self.synthesizer.build_signals(evidences)
```

### 문제점
- **트리거된 작업이 또 다른 트리거를 발생시킬 수 있음**
- 무한 루프 방지 메커니즘 없음
- "Insufficient Evidence" 트리거가 증거를 추가해도 여전히 3개 미만일 수 있음
- **최대 반복 횟수 제한 없음**

### 금융 손실 시나리오
1. 초기 증거가 2개만 수집됨
2. "Insufficient Evidence" 트리거로 추가 작업 생성
3. 추가 작업이 또 2개 증거만 생성 (총 4개)
4. 하지만 시스템이 증거를 재집계하기 전에 또 다른 트리거 발생
5. **무한 루프로 인한 시스템 중단 또는 과도한 API 비용**
6. 사용자가 결과를 기다리다가 타임아웃, 또는 잘못된 중간 결과로 투자 결정

### 암묵적 가정
- 트리거가 항상 수렴한다고 가정
- 한 번의 재합성으로 충분하다고 가정

---

## 치명적 약점 #7: 점수 계산의 비선형성과 임의적 가중치

### 위치
```6:33:src/orchestrator/verdict.py
score = 0.0
rationale = {"bull_case": [], "bear_case": []}

# 1. Feature-based Scoring

# Sentiment
if signals.sentiment_score > 0.3:
    score += 1.0
    rationale["bull_case"].append(f"Strong positive sentiment ({signals.sentiment_score:.2f}).")
elif signals.sentiment_score < -0.3:
    score -= 1.0
    rationale["bear_case"].append(f"Negative sentiment ({signals.sentiment_score:.2f}).")
    
# Momentum/Valuation
if signals.momentum_score > 0:
    score += 1.0
elif signals.momentum_score < 0:
    score -= 1.0
    
# Risks
if signals.volatility_risk > 0.7:
    score -= 0.5
    rationale["bear_case"].append(f"High volatility risk ({signals.volatility_risk:.1f}).")
    
if signals.event_risk > 0.5:
    score -= 2.0
    rationale["bear_case"].append(f"Significant event/regulatory risk detected.")
```

### 문제점
- **모든 점수가 선형적으로 더해짐** - 상호작용 고려 없음
- 감정 점수 +1.0, 모멘텀 점수 +1.0, 이벤트 리스크 -2.0 - **가중치가 임의적**
- **이벤트 리스크가 감정보다 2배 중요하다는 근거 없음**
- 점수가 0.5와 1.5 사이면 HOLD - **너무 넓은 범위**

### 금융 손실 시나리오
1. 감정 점수 +0.8, 모멘텀 +0.3, 변동성 리스크 0.8, 이벤트 리스크 0.6
2. 계산: +1.0 (감정) + 1.0 (모멘텀) - 0.5 (변동성) - 2.0 (이벤트) = -0.5
3. 판단: SELL
4. 하지만 **감정과 모멘텀이 모두 강한데 이벤트 리스크 하나로 SELL 판단**
5. 실제로는 이벤트 리스크가 과장되었을 수 있음 (LLM 환각)
6. 사용자가 **잘못된 SELL 신호로 인해 수익 기회 상실**

### 암묵적 가정
- 모든 신호가 독립적이라고 가정
- 가중치가 시장 상황과 무관하게 고정되어도 된다고 가정

---

## 추가 약점 요약

### 약점 #8: 동시성 제어 부재
- `parallelizable=True` 플래그가 있지만 **실제 병렬 실행 로직 없음**
- 모든 작업이 순차 실행되어 **성능 병목**

### 약점 #9: 타임아웃 메커니즘 부재
- LLM API 호출에 **타임아웃 없음**
- 네트워크 지연 시 무한 대기 가능

### 약점 #10: 리스크 프로필 무시
- `RequestInput`에 `risk_profile`이 있지만 **실제로 사용되지 않음**
- 보수적/공격적 투자자에게 동일한 판단 제공

---

## 이전 프롬프트의 기여와 장점

### 사용된 프롬프트

이 적대적 리뷰는 다음 프롬프트 지시사항에 따라 수행되었다:

```
You are an adversarial reviewer.

Your job is to aggressively review AgenticInvest
as if it were submitted for a high-stakes production system.

Rules:
- Assume the authors are overconfident.
- Assume vague abstractions hide design flaws.
- Treat any unstated assumption as a potential bug.

Tasks:
1. Identify at least 7 critical weaknesses or ambiguities.
2. For each, explain how it could cause financial loss or system failure.
3. Explicitly call out:
   - Hand-wavy agent logic
   - Missing decision boundaries
   - Implicit trust in LLM behavior

Do NOT propose fixes unless absolutely necessary.
Primary goal: expose weaknesses, not to be helpful.
```

### 프롬프트가 이 리뷰에 기여한 방식

#### 1. **명확한 역할 정의**
- "You are an adversarial reviewer" - AI가 도움이 되는 조언자가 아닌 **적대적 검토자** 역할을 명확히 함
- 이로 인해 일반적인 코드 리뷰와 달리 **약점 노출에 집중**할 수 있었음

#### 2. **가정 명시를 통한 편향 제거**
- "Assume the authors are overconfident" - 작성자에 대한 신뢰를 제거하고 **의심의 관점** 채택
- "Assume vague abstractions hide design flaws" - 모호한 부분을 **설계 결함의 징후**로 해석
- "Treat any unstated assumption as a potential bug" - **암묵적 가정을 명시적으로 지적**하도록 유도

이러한 가정 덕분에:
- 각 약점 섹션에 "암묵적 가정" 하위 섹션을 포함할 수 있었음
- 코드에서 명시되지 않은 가정들을 체계적으로 식별할 수 있었음
- 예: 약점 #1에서 "LLM이 항상 'X is Y%' 형식으로 출력한다고 가정" 지적

#### 3. **구체적인 작업 지시**
- "Identify at least 7 critical weaknesses" - **최소 요구사항 명시**로 충분한 깊이 보장
- "explain how it could cause financial loss" - 각 약점에 대해 **구체적인 손실 시나리오** 작성 강제
- "Explicitly call out: Hand-wavy agent logic, Missing decision boundaries, Implicit trust in LLM behavior" - **특정 유형의 문제**를 명시적으로 찾도록 지시

이로 인해:
- 약점 #1, #5에서 "Hand-wavy agent logic" (문자열 파싱, LLM 맹신) 지적
- 약점 #3에서 "Missing decision boundaries" (임의의 임계값) 지적
- 약점 #5에서 "Implicit trust in LLM behavior" (증거 검증 부재) 지적

#### 4. **제약 조건의 효과**
- "Do NOT propose fixes unless absolutely necessary" - **해결책 제시 금지**로 약점 분석에만 집중
- "Primary goal: expose weaknesses, not to be helpful" - **도움을 주려는 유혹 제거**

이 제약 덕분에:
- 각 약점이 **왜 문제인지**에 집중할 수 있었음
- 금융 손실 시나리오를 **구체적으로 묘사**할 수 있었음
- 일반적인 리뷰처럼 "이렇게 수정하면 됩니다"라는 제안으로 분산되지 않음

### 이 프롬프트의 장점 (다른 접근법과 비교)

#### vs. 일반적인 코드 리뷰 프롬프트

**일반 프롬프트**: "이 코드를 리뷰하고 개선 사항을 제안하세요"

**문제점**:
- AI가 긍정적 피드백과 부정적 피드백을 균형있게 제공하려 함
- 약점을 찾아도 "하지만 이 부분은 좋습니다" 같은 완화 표현 사용
- 해결책 제시에 집중하여 근본적인 문제 분석이 약함

**이 프롬프트의 장점**:
- **단일 목표**: 약점 노출에만 집중
- **편향 명시**: "Assume overconfident"로 의심의 관점 채택
- **구체적 지시**: 7개 이상, 금융 손실 설명 등 명확한 요구사항

#### vs. 정적 분석 도구

**정적 분석**: 린터, 타입 체커 등

**한계**:
- 구문 오류, 타입 불일치 등 **표면적 문제**만 발견
- **의도와 실제 동작의 괴리**를 찾지 못함
- **비즈니스 로직의 결함**을 발견하지 못함

**이 프롬프트의 장점**:
- **의미론적 분석**: 코드의 의도와 실제 동작을 비교
- **시나리오 기반**: "이렇게 하면 어떤 일이 일어날까?" 질문
- **도메인 특화**: 금융 시스템의 특수성을 고려한 분석

#### vs. 테스트 기반 검증

**테스트**: 단위 테스트, 통합 테스트

**한계**:
- **명시된 동작**만 검증
- **예상치 못한 실패 모드**를 찾지 못함
- **암묵적 가정**을 테스트하지 않음

**이 프롬프트의 장점**:
- **암묵적 가정 명시**: "이 코드는 무엇을 가정하고 있는가?" 질문
- **실패 모드 탐색**: "이게 실패하면 어떻게 될까?" 시나리오
- **경계 조건**: 임계값, 에러 처리 등 **결정 경계** 집중

### 프롬프트 설계의 핵심 성공 요소

1. **역할 명확화**: "adversarial reviewer" - AI의 정체성과 목표를 명확히 함
2. **가정 명시**: 작성자에 대한 가정을 명시하여 편향 제어
3. **구체적 지표**: "7개 이상", "금융 손실 설명" 등 측정 가능한 요구사항
4. **제약 조건**: 해결책 제시 금지로 분석에만 집중
5. **도메인 인식**: "financial loss", "system failure" 등 도메인 특화 용어 사용

### 결론

이 프롬프트는 **체계적이고 공격적인 코드 리뷰**를 가능하게 했다. 특히:

- **편향 제거**: "Assume overconfident"로 긍정적 편향 제거
- **깊이 보장**: 최소 7개 약점 요구로 표면적 분석 방지
- **구체성 강제**: 금융 손실 시나리오 작성으로 추상적 지적 방지
- **집중도 향상**: 해결책 제시 금지로 약점 분석에만 집중

이러한 구조화된 접근 덕분에 **프로덕션 배포 전에 반드시 발견되어야 할 치명적 약점들**을 체계적으로 식별할 수 있었다.

---

## 결론

이 시스템은 **프로덕션 배포에 전혀 준비되지 않았다**. 핵심 문제는:

1. **LLM 출력을 맹신** - 검증 없이 사실로 취급
2. **문자열 파싱에 의존** - 취약하고 실패하기 쉬운 추출 방식
3. **에러 처리 부재** - 부분적 실패를 정상으로 처리
4. **임의의 임계값** - 근거 없는 결정 경계
5. **일관성 없는 신뢰도** - Crew마다 다른 기준
6. **무한 루프 가능성** - 트리거 제어 부재
7. **비선형적 점수 계산** - 임의적 가중치

**이 시스템으로 인한 금융 손실은 불가피하다.**
