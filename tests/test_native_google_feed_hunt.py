import gzip

from tools.native_google_feed_hunt import extract_candidate_urls, validate_google_xml


GOOD = b'''<?xml version="1.0"?><rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel><item><g:id>SKU-1</g:id><g:title>Widget</g:title><g:link>https://example.test/p/1</g:link><g:price>1999 INR</g:price></item></channel></rss>'''
SITEMAP = b'''<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.test/p/1</loc></url></urlset>'''
RSS = b'''<?xml version="1.0"?><rss><channel><item><title>Widget</title><link>https://example.test/p/1</link></item></channel></rss>'''


def test_validate_native_google_feed_requires_core_google_fields():
    result = validate_google_xml(GOOD, "application/xml")
    assert result.valid is True
    assert result.product_items == 1
    assert "id" in result.reasons[3] or "google_fields" in result.reasons[-1] or result.google_fields >= 4


def test_sitemap_is_excluded():
    result = validate_google_xml(SITEMAP, "application/xml")
    assert result.valid is False
    assert result.format == "sitemap"
    assert result.reasons == ("sitemap_excluded",)


def test_generic_rss_is_not_a_google_merchant_feed():
    result = validate_google_xml(RSS, "application/rss+xml")
    assert result.valid is False


def test_gzip_payload_is_supported():
    result = validate_google_xml(gzip.compress(GOOD), "application/xml")
    assert result.valid is True


def test_discovered_urls_are_same_host_and_feed_like():
    body = '''
      <a href="/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml">feed</a>
      <a href="https://other.example.com/google.xml">other</a>
      <script>var feedUrl="https://example.test/?woocommerce_gpf=google"</script>
    '''
    found = extract_candidate_urls(body, "https://example.test")
    assert "https://example.test/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml" in found
    assert "https://example.test/?woocommerce_gpf=google" in found
    assert all("other.example.com" not in url for url in found)
