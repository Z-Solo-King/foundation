from datetime import date, datetime, timezone
from dataclasses import replace
import pytest


def test_contradiction_typed_and_legacy_all_markers():
    from backend.intelligence.contradiction import TypedClaim, detect_contradiction, detect_typed_contradiction
    assert detect_contradiction("", "x") is None and detect_contradiction("same", "same") is None
    for pos, neg in (("true", "false"), ("yes", "no"), ("enabled", "disabled"), ("available", "unavailable")):
        assert detect_contradiction(pos, neg) is not None and detect_contradiction(neg, pos) is not None
    assert detect_contradiction("not available", "available") is not None
    base = dict(entity="E", predicate="P", scope=None, valid_from=None, valid_until=None, unit="u", qualifier="q", version=None)
    def claim(cid, value, value_type, **changes):
        data = dict(base); data.update(changes); return TypedClaim(cid, data.pop("entity"), data.pop("predicate"), value, value_type, **data)
    assert detect_typed_contradiction(claim("a",1,"numeric"), claim("b",2,"numeric")) is not None
    assert detect_typed_contradiction(claim("a","2024-01-01","date"), claim("b",date(2024,1,2),"date")) is not None
    assert detect_typed_contradiction(claim("a","yes","boolean"), claim("b","no","boolean")) is not None
    assert detect_typed_contradiction(claim("a",1,"quantity"), claim("b",2,"quantity")) is not None
    assert detect_typed_contradiction(claim("a","alpha","text"), claim("b","beta","text")) is not None
    assert detect_typed_contradiction(claim("a","alpha","text", qualifier="x"), claim("b","alpha","text", qualifier="y")) is not None
    assert detect_typed_contradiction(claim("a",1,"numeric",unit="kg"), claim("b",2,"numeric",unit="lb")) is None
    assert detect_typed_contradiction(claim("a",1,"numeric",scope="a"), claim("b",2,"numeric",scope="b")) is None
    assert detect_typed_contradiction(claim("a",1,"numeric",valid_until=datetime(2024,1,1)), claim("b",2,"numeric",valid_from=datetime(2024,1,2))) is None
    assert detect_typed_contradiction(claim("a",1,"numeric",version="v1"), claim("b",2,"numeric",version="v2")) is None


def test_lineage_contradiction_and_observation_remaining_edges():
    from backend.intelligence.contradiction import TypedClaim, _as_date, _numeric, detect_contradiction, detect_typed_contradiction
    from backend.intelligence.lineage import SourceLineage
    assert _numeric("not-a-number") is None and _as_date("not-a-date") is None
    assert _as_date(datetime(2024,1,2)).isoformat() == "2024-01-02" and _as_date(date(2024,1,2)).isoformat() == "2024-01-02"
    assert detect_contradiction("something","else") is None and detect_contradiction("not available","available") is not None
    base = dict(entity="E", predicate="P", scope=None, valid_from=None, valid_until=None, unit="u", qualifier="q", version=None)
    def c(cid,value,value_type,**changes):
        data=dict(base); data.update(changes); return TypedClaim(cid,data.pop("entity"),data.pop("predicate"),value,value_type,**data)
    assert detect_typed_contradiction(c("a","bad","numeric"),c("b","other","numeric")) is None
    assert detect_typed_contradiction(c("a","bad-date","date"),c("b","also-bad","date")) is None
    assert detect_typed_contradiction(c("a","one","enum"),c("b","two","enum")) is not None
    assert detect_typed_contradiction(c("a","same","text",unit="a"),c("b","same","text",unit="b")) is None
    assert detect_typed_contradiction(c("a","same","text"),c("b","same","text")) is None
    assert detect_typed_contradiction(c("a",1,"numeric",valid_until=datetime(2024,1,1)),c("b",2,"numeric",valid_from=datetime(2024,1,2))) is None
    assert detect_typed_contradiction(c("a",1,"numeric"),c("b",2,"other")) is None
    with pytest.raises(ValueError): SourceLineage("s","f",lineage_type="republished").validate()
    SourceLineage("s","f",lineage_type="republished",origin_fingerprint="fp",parent_source_id="p").validate()


def test_typed_contradiction_date_boolean_and_text_edges():
    from backend.intelligence.contradiction import TypedClaim, detect_typed_contradiction
    def c(cid,value,value_type,**kwargs): return TypedClaim(cid,"E","P",value,value_type,unit=kwargs.get("unit","u"),qualifier=kwargs.get("qualifier","q"),valid_from=kwargs.get("valid_from"),valid_until=kwargs.get("valid_until"))
    assert detect_typed_contradiction(c("a","2024-01-01","date"),c("b","2024-01-02","date")) is not None
    assert detect_typed_contradiction(c("a",True,"boolean"),c("b",False,"boolean")) is not None
    assert detect_typed_contradiction(c("a","x","text",unit="a"),c("b","y","text",unit="b")) is None
    assert detect_typed_contradiction(c("a","x","text",qualifier="q1"),c("b","x","text",qualifier="q2")) is not None


def test_typed_contradiction_entity_predicate_and_version_guards():
    from backend.intelligence.contradiction import TypedClaim, detect_typed_contradiction
    base=TypedClaim("a","E","P","x","text")
    assert detect_typed_contradiction(base,TypedClaim("b","F","P","x","text")) is None
    assert detect_typed_contradiction(base,TypedClaim("c","E","Q","x","text")) is None
    assert detect_typed_contradiction(TypedClaim("d","E","P","x","text",version="1"),TypedClaim("e","E","P","y","text",version="2")) is None
    a=TypedClaim("aa","E","P","x","unknown",unit=None,qualifier=None); b=TypedClaim("bb","E","P","y","unknown",unit=None,qualifier=None)
    assert detect_typed_contradiction(a,b) is None
    left=TypedClaim("left","E","P",1,"numeric",valid_until=datetime(2026,1,1,tzinfo=timezone.utc),unit="kg")
    right=TypedClaim("right","E","P",2,"numeric",valid_from=datetime(2026,2,1,tzinfo=timezone.utc),unit="kg")
    assert detect_typed_contradiction(left,right) is None
    quantity=TypedClaim("q","E","P",1,"quantity",unit=None); quantity2=TypedClaim("q2","E","P",2,"quantity",unit=None)
    assert detect_typed_contradiction(quantity,quantity2) is None
    enum_a=TypedClaim("ea","E","P","same","enum",unit=None); enum_b=TypedClaim("eb","E","P","same","enum",unit=None)
    assert detect_typed_contradiction(enum_a,enum_b) is None
    assert detect_typed_contradiction(TypedClaim("t1","E","P","a","text",unit="kg",qualifier="x"),TypedClaim("t2","E","P","b","text",unit="lb",qualifier="x")) is None


def test_lineage_constructor_and_validation_guards():
    from backend.intelligence.lineage import SourceLineage
    with pytest.raises(ValueError): SourceLineage("s","f",lineage_type="invalid").validate()
    with pytest.raises(ValueError): SourceLineage("s","f",lineage_type="republished").validate()
    with pytest.raises(ValueError, match="origin_fingerprint"): SourceLineage("s","f",lineage_type="republished").validate()
    with pytest.raises(ValueError, match="identify its origin"): SourceLineage("s","f",lineage_type="republished",origin_fingerprint="fp").validate()
    rep=SourceLineage("s","f",parent_source_id="p",lineage_type="republished",origin_fingerprint="fp"); rep.validate(); assert rep.effective_origin == "fp"
    assert SourceLineage("s","f").effective_origin == "family:f"
    with pytest.raises(ValueError): SourceLineage("","f").validate()


def test_observation_and_certificate_validation_edges():
    from backend.intelligence.certificates import create_certificate, verify_certificate
    from backend.intelligence.observations import Observation, EvidenceSpan
    from backend.intelligence.lineage import SourceLineage
    from backend.intelligence.sources import Source, SourcePolicy, SourceType, canonical_source_url, evaluate_source
    obs=Observation.create("o","sid","https://Example.com","hello evidence"); span=EvidenceSpan("o",0,5); cert=create_certificate(obs,span)
    assert verify_certificate(obs,cert) is True
    for bad in (cert.__class__(cert.observation_id,"other",cert.source_url,cert.content_hash,cert.span_start,cert.span_end,cert.span_text,True),cert.__class__(cert.observation_id,cert.source_id,"https://other",cert.content_hash,cert.span_start,cert.span_end,cert.span_text,True),cert.__class__(cert.observation_id,cert.source_id,cert.source_url,"bad",cert.span_start,cert.span_end,cert.span_text,True),cert.__class__(cert.observation_id,cert.source_id,cert.source_url,cert.content_hash,0,99,cert.span_text,True),cert.__class__(cert.observation_id,cert.source_id,cert.source_url,cert.content_hash,cert.span_start,cert.span_end,"other",True),cert.__class__(cert.observation_id,cert.source_id,cert.source_url,cert.content_hash,cert.span_start,cert.span_end,cert.span_text,False)):
        assert verify_certificate(obs,bad) is False
    with pytest.raises(TypeError): Observation("o","sid","u","c","bad","extra")
    with pytest.raises(TypeError): Observation.create("o","u","c","x","y","z")
    with pytest.raises(ValueError): EvidenceSpan("x",0,1).validate(obs)
    with pytest.raises(ValueError): EvidenceSpan("o",-1,1).validate(obs)
    with pytest.raises(ValueError): EvidenceSpan("o",5,4).validate(obs)
    with pytest.raises(ValueError): EvidenceSpan("o",0,99).validate(obs)
    with pytest.raises(ValueError): canonical_source_url("bad")
    assert canonical_source_url("https://EXAMPLE.com:443//a?utm_source=x&b=2") == "https://example.com/a?b=2"
    source=Source("s","https://example.com",SourceType.WEB,family_id="f"); source.validate(); assert source.lineage("fp").origin_fingerprint == "fp"
    with pytest.raises(ValueError): Source("s","https://example.com",SourceType.WEB,lineage_type="bad").validate()
    with pytest.raises(ValueError): Source("s","https://example.com",SourceType.WEB,lineage_type="republished").validate()
    assert evaluate_source(source,SourcePolicy()) is True and evaluate_source(source,SourcePolicy(allowed=False)) is False
    with pytest.raises(ValueError, match="max_requests"):
        SourcePolicy(max_requests=0).validate()


def test_observation_create_and_span_guards():
    from backend.intelligence.observations import EvidenceSpan, Observation
    one=Observation.create("o1","https://e","body"); two=Observation.create("o2","sid","https://e","body"); three=Observation.create("o3","sid","https://e","body",datetime.now(timezone.utc))
    assert one.content == two.content == three.content == "body"
    with pytest.raises(TypeError): Observation.create("o4","a","b","c","d","e")
    obs=Observation.create("o","sid","https://e","abc")
    with pytest.raises(ValueError): EvidenceSpan("o",3,2).text_from(obs)
    with pytest.raises(ValueError): EvidenceSpan("wrong",0,1).text_from(obs)
    with pytest.raises(TypeError): Observation("o1","sid",None,"text",datetime.now(timezone.utc))
    with pytest.raises(TypeError): Observation("o2","sid","https://e",None,datetime.now(timezone.utc))
    assert Observation("o","https://e","x",None).observed_at.tzinfo is not None


def test_verifier_strict_and_inaccessible_paths():
    from backend.intelligence.certificates import create_certificate
    from backend.intelligence.claims import Claim
    from backend.intelligence.observations import Observation, EvidenceSpan
    from backend.intelligence.lineage import SourceLineage
    from backend.intelligence.verifier import EvidenceVerifier, ClaimStatus
    good_obs=Observation.create("good","sid","https://e","banana"); bad_obs=Observation.create("bad","sid","https://e","unrelated evidence")
    good_cert=create_certificate(good_obs,EvidenceSpan("good",0,6)); bad_cert=create_certificate(bad_obs,EvidenceSpan("bad",0,18)); claim=Claim.create("c","banana")
    strict=EvidenceVerifier(semantic_strict=True)
    partial=strict.verify_claim(claim,(good_cert,bad_cert),{"good":good_obs,"bad":bad_obs},{"sid":SourceLineage("sid","family")}); assert partial.status == ClaimStatus.PARTIAL
    missing=strict.verify_claim(claim,(good_cert,),{},{}); assert missing.status == ClaimStatus.INACCESSIBLE and "inaccessible" in " ".join(missing.reasons)
    bad=replace(good_cert,span_text="bad"); assert strict.verify_claim(claim,(bad,),{"good":good_obs},{}).status == ClaimStatus.CONTRADICTED
    stale_obs=Observation.create("s","sid","https://e","banana",datetime.now(timezone.utc)-__import__('datetime').timedelta(days=31)); stale_cert=create_certificate(stale_obs,EvidenceSpan("s",0,6)); stale_claim=Claim.create("stale","banana")
    assert strict.verify_claim(stale_claim,(stale_cert,),{"s":stale_obs},{"sid":SourceLineage("sid","family")}).status == ClaimStatus.STALE


def test_verifier_final_branch_and_remaining_control_flow():
    from backend.intelligence.certificates import create_certificate
    from backend.intelligence.claims import Claim
    from backend.intelligence.lineage import SourceLineage
    from backend.intelligence.observations import EvidenceSpan, Observation
    from backend.intelligence.verifier import ClaimStatus, EvidenceVerifier, VerificationResult
    result=VerificationResult("c",ClaimStatus.UNKNOWN); assert result.verified_at.tzinfo is not None
    obs1=Observation.create("o1","s1","https://a","claim text"); obs2=Observation.create("o2","s2","https://b","claim text")
    cert1=create_certificate(obs1,EvidenceSpan("o1",0,10)); cert2=create_certificate(obs2,EvidenceSpan("o2",0,10)); claim=Claim.create("c","claim text"); verifier=EvidenceVerifier(semantic_strict=True)
    verified=verifier.verify_claim(claim,(cert1,cert2),{"o1":obs1,"o2":obs2},{"s1":SourceLineage("s1","f1",origin_fingerprint="o1"),"s2":SourceLineage("s2","f2",origin_fingerprint="o2")},()); assert verified.status in {ClaimStatus.CORROBORATED,ClaimStatus.SUPPORTED}
    same_origin=verifier.verify_claim(claim,(cert1,cert2),{"o1":obs1,"o2":obs2},{"s1":SourceLineage("s1","f1",origin_fingerprint="same"),"s2":SourceLineage("s2","f2",origin_fingerprint="same")},()); assert same_origin.independent_corroboration_count == 1
    assert verifier.verify_claim(claim,(cert1,),{},{} ,()).status == ClaimStatus.INACCESSIBLE
    obs=Observation.create("o","sid","https://e","banana"); cert=create_certificate(obs,EvidenceSpan("o",0,6)); other=Claim.create("other","apple"); verifier=EvidenceVerifier()
    assert verifier.verify_claim(Claim.create("c","banana"),(cert,),{"o":obs},{"sid":SourceLineage("sid","family")},(Claim.create("c","banana"),other)).status == ClaimStatus.SUPPORTED


def test_verifier_inaccessible_semantic_and_explicit_timestamp_paths():
    from backend.intelligence.certificates import create_certificate
    from backend.intelligence.claims import Claim
    from backend.intelligence.observations import EvidenceSpan, Observation
    from backend.intelligence.verifier import ClaimStatus, EvidenceVerifier, VerificationResult
    claim=Claim.create("c","text"); obs=Observation.create("o","s","https://e","other"); cert=create_certificate(obs,EvidenceSpan("o",0,5)); verifier=EvidenceVerifier(semantic_strict=True)
    result=verifier.verify_claim(claim,(cert,),{"o":obs},{},()); assert result.status in {ClaimStatus.PARTIAL,ClaimStatus.UNKNOWN,ClaimStatus.INACCESSIBLE}
    explicit=datetime(2026,1,1,tzinfo=timezone.utc); assert VerificationResult("v",ClaimStatus.UNKNOWN,verified_at=explicit).verified_at == explicit


def test_source_lineage_independence_and_origin():
    from backend.intelligence.lineage import SourceLineage, origin_fingerprint, is_independent
    assert origin_fingerprint("Example.COM") == origin_fingerprint(" example.com ")
    with pytest.raises(ValueError): origin_fingerprint("")
    assert is_independent(SourceLineage("a","f1"),SourceLineage("b","f2")) is True
