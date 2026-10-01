from backend.admission import AdmissionPolicy
from backend.sources.access_policy import AccessClass,DisclosureClass,RetentionClass,SourceAccessPolicy
from backend.intelligence.authority import ClaimField,FieldAuthority

def admission_policy():
    return AdmissionPolicy("public-admission/v1",60,30,300,22,22,5, ())

def source_policy(**overrides):
    values={"policy_version":"source-access/v1","access_class":AccessClass.PUBLIC,"acquisition_method":"http_get","requires_authentication":False,"robots_restriction":False,"retention_class":RetentionClass.SHORT,"raw_content_allowed":False,"disclosure_class":DisclosureClass.PUBLIC_SAFE,"revalidation_required":True,"revalidation_after_seconds":None}
    values.update(overrides); return SourceAccessPolicy(**values)

AUTHORITY_RULES={
 ClaimField.SPECIFICATION:{FieldAuthority.MANUFACTURER_DECLARATION,FieldAuthority.INDEPENDENT_MEASUREMENT},
 ClaimField.MEASUREMENT:{FieldAuthority.INDEPENDENT_MEASUREMENT},
 ClaimField.PRICE:{FieldAuthority.RETAILER_CURRENT_STATE},
 ClaimField.STOCK:{FieldAuthority.RETAILER_CURRENT_STATE},
 ClaimField.WARRANTY:{FieldAuthority.MANUFACTURER_POLICY,FieldAuthority.RETAILER_CURRENT_STATE},
 ClaimField.SERVICE:{FieldAuthority.MANUFACTURER_POLICY,FieldAuthority.COMMUNITY_EXPERIENCE},
 ClaimField.EXPERIENCE:{FieldAuthority.COMMUNITY_EXPERIENCE},
}
