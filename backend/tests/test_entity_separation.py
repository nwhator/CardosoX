import unittest

try:
    from extractors.entity_extractor import EntityExtractor
    from matchers.entity_matcher import EntityMatcher

    HAS_EXTRACTOR_DEPS = True
except ModuleNotFoundError:
    HAS_EXTRACTOR_DEPS = False


@unittest.skipUnless(HAS_EXTRACTOR_DEPS, "BeautifulSoup dependencies are not installed")
class EntitySeparationTests(unittest.TestCase):
    def test_extracts_repeated_listings_as_separate_companies(self):
        html = """
        <html>
          <body>
            <main class="directory-results">
              <div>
                <h3>Alpha Events</h3>
                <a href="mailto:bookings@alphaevents.com">Email</a>
                <a href="tel:+2348011111111">Call</a>
                <address>12 Marina Road, Lagos, Nigeria</address>
                <a href="https://instagram.com/alphaevents">Instagram</a>
              </div>
              <div>
                <h3>Beta Decor</h3>
                <a href="mailto:hello@betadecor.com">Email</a>
                <a href="tel:+2348022222222">Call</a>
                <address>44 Wuse Avenue, Abuja, Nigeria</address>
                <a href="https://facebook.com/betadecor">Facebook</a>
              </div>
            </main>
          </body>
        </html>
        """

        companies = EntityExtractor().extract(html, "https://directory.example.com/vendors")

        self.assertEqual(len(companies), 2)
        by_name = {company["company_name"]: company for company in companies}
        self.assertEqual(by_name["Alpha Events"]["email"], "bookings@alphaevents.com")
        self.assertEqual(by_name["Alpha Events"]["phone"], "+2348011111111")
        self.assertIn("Marina Road", by_name["Alpha Events"]["address"])
        self.assertEqual(by_name["Alpha Events"]["socials"], ["https://instagram.com/alphaevents"])
        self.assertEqual(by_name["Beta Decor"]["email"], "hello@betadecor.com")
        self.assertEqual(by_name["Beta Decor"]["phone"], "+2348022222222")
        self.assertIn("Wuse Avenue", by_name["Beta Decor"]["address"])
        self.assertEqual(by_name["Beta Decor"]["socials"], ["https://facebook.com/betadecor"])

    def test_does_not_merge_same_name_branches_with_different_contact_data(self):
        entities = [
            {
                "company_name": "City Foods",
                "phone": "+2348011111111",
                "phone_numbers": ["+2348011111111"],
                "address": "12 Marina Road, Lagos, Nigeria",
                "addresses": ["12 Marina Road, Lagos, Nigeria"],
                "emails": [],
                "socials": [],
                "confidence": 0.8,
            },
            {
                "company_name": "City Foods",
                "phone": "+2348022222222",
                "phone_numbers": ["+2348022222222"],
                "address": "44 Wuse Avenue, Abuja, Nigeria",
                "addresses": ["44 Wuse Avenue, Abuja, Nigeria"],
                "emails": [],
                "socials": [],
                "confidence": 0.8,
            },
        ]

        merged = EntityMatcher().merge_entities(entities)

        self.assertEqual(len(merged), 2)


if __name__ == "__main__":
    unittest.main()

