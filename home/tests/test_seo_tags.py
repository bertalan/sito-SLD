import json
from django.test import RequestFactory, TestCase
from django.template import Context, Template

class SchemaOrgJsonLDTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_schema_org_jsonld_valid(self):
        # Simula una pagina Wagtail con attributi SEO
        class DummyPage:
            seo_title = "Studio Legale D'Onofrio"
            title = "Home"
            search_description = "Descrizione SEO"
            url_path = "/home/"
            get_ancestors = lambda self, inclusive: []
        
        request = self.factory.get("/")
        page = DummyPage()
        context = Context({"request": request, "page": page})

        # Renderizza il tag custom
        template = Template("{% load seo_tags %}{% schema_org_jsonld %}")
        rendered = template.render(context)

        # Estrai il JSON dal tag script
        start = rendered.find('<script type="application/ld+json">') + len('<script type="application/ld+json">')
        end = rendered.find('</script>')
        jsonld = rendered[start:end].strip()
        data = json.loads(jsonld)

        # Test base: deve avere @context e @graph
        assert "@context" in data
        assert "@graph" in data
        assert isinstance(data["@graph"], list)

        # Test: deve contenere LegalService e WebPage
        types = [item["@type"] for item in data["@graph"] if "@type" in item]
        assert "LegalService" in types
        assert "WebPage" in types

        # Test: indirizzo Lecce corretto
        legal_service = next(item for item in data["@graph"] if item["@type"] == "LegalService")
        lecce = next(loc for loc in legal_service["location"] if "Lecce" in loc["name"])
        assert lecce["address"]["streetAddress"] == "Piazza Mazzini 72"

        # Test: orari di apertura sono una lista o vuoti
        for loc in legal_service["location"]:
            assert "openingHoursSpecification" in loc
            assert isinstance(loc["openingHoursSpecification"], list)

        # Puoi aggiungere altri assert per validare i campi richiesti da schema.org
