"""Pure planner algorithms: classification, query generation, scoring and recovery."""
from __future__ import annotations
import re
from dataclasses import replace
from typing import Iterable, Mapping, Sequence
from .planner_models import Action, ClaimRequirement, Coverage, CoverageState, FactType, FieldRequirement, MethodCandidate, QueryCandidate, ResourceEnvelope, SourcePlan, SourceProfileHint, StopReason, TaskMode, TaskPlan


def classify_task(question: str, output_type: str = "") -> TaskMode:
    text=f"{question} {output_type}".lower()
    if "spec" in text: return TaskMode.SPECIFICATION
    signals={TaskMode.RECOMMENDATION:("recommend","best","which should","buy"),TaskMode.COMPARISON:("compare","versus","vs","difference"),TaskMode.TEMPORAL:("history","historical","changed","when","latest"),TaskMode.CONTRADICTION:("contradict","disagree","is it true","conflict"),TaskMode.PRICE_AVAILABILITY:("price","cost","stock","available"),TaskMode.DIAGNOSIS:("why","problem","error","broken","debug"),TaskMode.COMMUNITY:("reddit","forum","community","user experience","sentiment"),TaskMode.PRIMARY_SOURCE:("official","manufacturer","source of record","primary source"),TaskMode.ENTITY_RESOLUTION:("same product","same model","match","identify entity"),TaskMode.CODE:("code","repository","python","javascript","bug","pull request"),TaskMode.DATA:("dataset","csv","spreadsheet","columns","dataframe"),TaskMode.DOCUMENT:("document","pdf","report","contract"),TaskMode.MEDIA:("image","video","audio","transcript","frame")}
    matches=[mode for mode,words in signals.items() if any(w in text for w in words)]
    return TaskMode.MIXED if len(matches)>1 else (matches[0] if matches else TaskMode.FACT)


def infer_fact_type(text: str) -> FactType:
    value=text.lower()
    if any(x in value for x in ("price","cost","discount","currency")): return FactType.COMMERCIAL
    if any(x in value for x in ("stock","availability","available")): return FactType.AVAILABILITY
    if any(x in value for x in ("release","launched","updated","current","historical")): return FactType.TEMPORAL
    if any(x in value for x in ("compatible","works with","depends on")): return FactType.RELATIONAL
    if any(x in value for x in ("review","experience","feel","quality")): return FactType.QUALITATIVE
    if any(x in value for x in ("policy","terms","rule","regulation")): return FactType.NORMATIVE
    if any(x in value for x in ("model","sku","mpn","gtin","version","name")): return FactType.IDENTITY
    return FactType.SPECIFICATION if any(x in value for x in ("spec","size","port","hz","memory","weight")) else FactType.IDENTITY


def decompose_claims(question: str, required: Sequence[str]|None=None)->tuple[ClaimRequirement,...]:
    if required is None:
        items=[]
    else:
        items=[x.strip() for x in required if x and x.strip()]
    if not items: items=[p.strip() for p in re.split(r"\s*(?:,|;|\band\b|\bplus\b)\s*",question,flags=re.I) if len(p.strip())>=8]
    if not items: items=[question.strip()]
    return tuple(ClaimRequirement(f"claim-{i+1}",text,fact_type=infer_fact_type(text)) for i,text in enumerate(items))


def normalize_fields(fields: Sequence[FieldRequirement]|None)->tuple[FieldRequirement,...]:
    seen=set(); out=[]
    if fields is None:
        return ()
    for field in fields:
        if not field.field_id or not field.semantic_name: raise ValueError("field requirement identifiers must be non-empty")
        if field.field_id in seen: raise ValueError(f"duplicate field requirement: {field.field_id}")
        seen.add(field.field_id); out.append(field)
    return tuple(out)


def generate_query_portfolio(question: str, claims: Sequence[ClaimRequirement], languages: Sequence[str]=(), source_families: Sequence[str]=(), max_queries: int=12)->tuple[QueryCandidate,...]:
    base=question.strip(); candidates=[]; seen=set()
    def add(query,purpose,gain,family=None,claim_ids=()):
        normalized=" ".join(query.split()).lower()
        if not normalized or normalized in seen or len(candidates)>=max_queries:return
        seen.add(normalized); candidates.append(QueryCandidate(query,purpose,gain,1.,family,claim_ids))
    claim_ids=tuple(c.claim_id for c in claims); add(base,"exact",.9,claim_ids=claim_ids)
    for claim in claims[:3]:
        add(f'"{claim.text}"',"identifier/exact-claim",.85,claim_ids=(claim.claim_id,))
    add(f"{base} official","primary-source",.88,"official",claim_ids); add(f"{base} specifications","specification",.75,"manufacturer",claim_ids); add(f"{base} counterclaim","counterclaim",.7,claim_ids=claim_ids); add(f"{base} recent","freshness",.72,claim_ids=claim_ids)
    for family in source_families:
        add(f"site:{family} {base}","site-restricted",.65,family,claim_ids)
    for language in languages:
        if language.lower() not in {"en","english"}: add(f"{base} {language}","multilingual",.62,claim_ids=claim_ids)
    add(f"{base} review experience","community",.55,"community",claim_ids); return tuple(candidates)


def method_utility(method: MethodCandidate)->float:
    positive=method.evidence_directness*.22+method.authority*.18+method.expected_success*.18+method.expected_completeness*.16+method.freshness*.08+method.independence*.08+method.information_gain*.10
    return positive-(.06*method.latency_cost+.08*method.resource_cost+.10*method.risk_penalty)


def rank_methods(methods: Iterable[MethodCandidate])->tuple[MethodCandidate,...]: return tuple(sorted(methods,key=lambda m:(-method_utility(m),m.method_id)))


def apply_source_profiles(methods: Sequence[MethodCandidate], profiles: Mapping[str,SourceProfileHint])->tuple[MethodCandidate,...]:
    updated=[]
    for method in methods:
        profile=profiles.get(method.source_id)
        if profile is None:
            updated.append(method)
            continue
        if profile.supported_representations:
            if method.representation not in profile.supported_representations:
                continue
        expected=min(.99,max(.01,(method.expected_success+profile.health)/2))
        if profile.sample_size<5:
            expected=(expected+.5)/2
        updated.append(replace(method,expected_success=expected,risk_penalty=method.risk_penalty+max(0.,.5-profile.health)))
    return rank_methods(updated)


def apply_field_preferences(methods: Sequence[MethodCandidate], fields: Sequence[FieldRequirement]) -> tuple[MethodCandidate, ...]:
    """Prefer representations explicitly requested by the contract without bypassing normal utility scoring."""
    preferred = {representation for field in fields for representation in field.preferred_representations}
    if not preferred:
        return rank_methods(methods)
    ranked=[]
    for method in methods:
        if method.representation in preferred:
            boost=0.10
        else:
            boost=0.0
        ranked.append((-(method_utility(method) + boost), method.method_id, method))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return tuple(item[2] for item in ranked)


def coverage_map(claims: Sequence[ClaimRequirement], evidence: Mapping[str,Coverage])->tuple[Coverage,...]: return tuple(evidence.get(c.claim_id,Coverage(c.claim_id,CoverageState.UNSUPPORTED)) for c in claims)


def recovery_actions(coverage: Sequence[Coverage])->tuple[Action,...]:
    actions=[]
    for item in coverage:
        if item.state in (CoverageState.CONTRADICTED,CoverageState.AMBIGUOUS): actions.append(Action(f"recover-{item.claim_id}-independent","search","independent/counterclaim verification",(item.claim_id,)))
        elif item.state in (CoverageState.PARTIAL,CoverageState.UNSUPPORTED): actions.append(Action(f"recover-{item.claim_id}-primary","search","primary/gap retrieval",(item.claim_id,)))
        elif item.state==CoverageState.STALE: actions.append(Action(f"recover-{item.claim_id}-fresh","search","freshness refresh",(item.claim_id,)))
        elif item.state in (CoverageState.BLOCKED,CoverageState.INACCESSIBLE): actions.append(Action(f"recover-{item.claim_id}-alternate","search","permitted alternate source",(item.claim_id,)))
    return tuple(actions)


def choose_stop_reason(coverage: Sequence[Coverage], budget_remaining: float, min_gain: float=.05)->StopReason|None:
    hard={CoverageState.UNSUPPORTED,CoverageState.PARTIAL,CoverageState.CONTRADICTED,CoverageState.STALE,CoverageState.BLOCKED,CoverageState.INACCESSIBLE,CoverageState.AMBIGUOUS}
    if coverage and all(c.state not in hard for c in coverage): return StopReason.QUALITY_FLOOR
    if budget_remaining<=0:return StopReason.BUDGET_EXHAUSTED
    if budget_remaining<min_gain:return StopReason.LOW_INFORMATION_GAIN
    return None


def build_task_plan(question: str, output_type: str="", claims: Sequence[str]|None=None, fields: Sequence[FieldRequirement]|None=None, languages: Sequence[str]=(), source_families: Sequence[str]=(), methods: Sequence[MethodCandidate]=(), envelope: ResourceEnvelope|None=None, max_queries: int=12)->TaskPlan:
    mode=classify_task(question,output_type); claim_reqs=decompose_claims(question,claims); field_reqs=normalize_fields(fields); queries=generate_query_portfolio(question,claim_reqs,languages,source_families,max_queries); ranked=apply_field_preferences(methods,field_reqs)
    source_plans=tuple(SourcePlan(family,required=(family in ("official","primary"))) for family in source_families)
    field_ids=tuple(f.field_id for f in field_reqs)
    actions=tuple(Action(f"query-{i+1}","search",q.purpose,q.target_claim_ids,field_ids,estimated_cost=q.estimated_cost) for i,q in enumerate(queries))
    if envelope is None:
        env=ResourceEnvelope(search_units=max(1,len(queries)))
    else:
        env=envelope
    env.validate()
    return TaskPlan(mode,tuple(claim_reqs),field_reqs,source_plans,queries,ranked,actions,env,metadata={"output_type":output_type,"planner":"deterministic-v1"})


def create_task_plan(contract: object)->TaskPlan:
    contract.validate()
    return build_task_plan(contract.question,contract.output_type,contract.claims_required,getattr(contract,"field_requirements",()),contract.languages,contract.source_families_required,envelope=contract.resource_envelope,max_queries=contract.max_search_actions)


__all__=["classify_task","infer_fact_type","decompose_claims","normalize_fields","generate_query_portfolio","method_utility","rank_methods","apply_source_profiles","apply_field_preferences","coverage_map","recovery_actions","choose_stop_reason","build_task_plan","create_task_plan"]