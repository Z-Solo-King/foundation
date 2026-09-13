from backend.intelligence.field_routing import (
    FieldRequirement,
    PaginationKind,
    PaginationPlan,
    Representation,
    RepresentationRoute,
    choose_routes,
)


def test_choose_routes_prefers_field_coverage_and_directness():
    fields = (
        FieldRequirement("f1", "refresh_rate", preferred_representations=(Representation.STRUCTURED,)),
        FieldRequirement("f2", "panel_type", preferred_representations=(Representation.STRUCTURED,)),
    )
    routes = (
        RepresentationRoute(Representation.STRUCTURED, ("refresh_rate", "panel_type"), .95, .9, .5),
        RepresentationRoute(Representation.BROWSER, ("refresh_rate",), .7, .8, 5.0),
    )
    assert choose_routes(fields, routes)[0].representation is Representation.STRUCTURED


def test_pagination_bounds_to_expected_total():
    plan = PaginationPlan(PaginationKind.PAGE, page_size=20, expected_total=45, max_pages=100, require_completeness=True)
    assert plan.bounded().max_pages == 3
