"""BOQ 22 参数核价引擎测试"""
import pytest
from app.services.boq_calculator import BOQCalculator, BOQ_PARAMS


@pytest.fixture
def calc():
    return BOQCalculator()


class TestBOQCalculator:
    def test_param_count_is_22(self):
        assert len(BOQ_PARAMS) == 22

    def test_calculate_basic(self, calc):
        result = calc.calculate({"material_type": "marble", "quantity_sqm": 100, "incoterms": "FOB"})
        assert result["base_price"] == 80
        assert result["quantity"] == 100
        assert result["subtotal"] == 8000
        assert result["total"] == 8000
        assert result["currency"] == "USD"
        assert result["valid_days"] == 30

    def test_unknown_material_defaults_to_50(self, calc):
        result = calc.calculate({"material_type": "unknown", "quantity_sqm": 10, "incoterms": "FOB"})
        assert result["base_price"] == 50
        assert result["total"] == 500

    def test_missing_required_params(self, calc):
        result = calc.calculate({})
        assert "error" in result
        assert "material_type" in result["error"]

    def test_customization_surcharge(self, calc):
        result = calc.calculate({"material_type": "ceramic", "quantity_sqm": 100, "incoterms": "FOB", "customization": True})
        assert result["total"] == 25 * 100 * 1.15

    def test_logo_printing_flat_fee(self, calc):
        result = calc.calculate({"material_type": "ceramic", "quantity_sqm": 100, "incoterms": "FOB", "logo_printing": True})
        assert result["total"] == 2500 + 500

    def test_inspection_flat_fee(self, calc):
        result = calc.calculate({"material_type": "ceramic", "quantity_sqm": 100, "incoterms": "FOB", "inspection_required": True})
        assert result["total"] == 2500 + 200

    def test_insurance_percentage(self, calc):
        result = calc.calculate({"material_type": "ceramic", "quantity_sqm": 100, "incoterms": "FOB", "insurance_required": True})
        assert result["total"] == round(2500 * 1.02, 2)

    def test_all_addons_stacked(self, calc):
        result = calc.calculate({
            "material_type": "granite", "quantity_sqm": 200, "incoterms": "CIF",
            "customization": True, "logo_printing": True, "inspection_required": True, "insurance_required": True,
        })
        expected = ((60 * 200) * 1.15 + 500 + 200) * 1.02
        assert result["total"] == round(expected, 2)
