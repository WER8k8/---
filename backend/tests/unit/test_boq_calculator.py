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

    def test_off_table_materials_do_not_zero_out(self, calc):
        """回归锁（模块2 P0）：表外材料基价不得归零，回落 _DEFAULT_BASE_PRICE = 50.0。

        porcelain / 铝复合板 / unknown 三个输入，`_get_base_price` 均须 == 50.0；
        porcelain quantity=100 → base_price=50.0 / total=5000.0。
        （HEAD 90ff513b 行为，HS-1 零漂移硬约束。）
        """
        from app.services.boq_calculator import _DEFAULT_BASE_PRICE

        assert _DEFAULT_BASE_PRICE == 50.0
        for material in ("porcelain", "铝复合板", "unknown"):
            assert calc._get_base_price(material) == 50.0
        result = calc.calculate({"material_type": "porcelain", "quantity_sqm": 100, "incoterms": "FOB"})
        assert result["base_price"] == 50.0
        assert result["total"] == 5000.0

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

    def test_industrial_22_params_thickness_and_container_load(self, calc):
        result = calc.calculate({
            "material_type": "marble",
            "material_grade": "premium",
            "quantity_sqm": 1500,
            "thickness_mm": 30,
            "surface_finish": "honed",
            "edge_profile": "bullnose",
            "incoterms": "CIF",
            "certification": "ce",
            "lead_time_days": 45,
            "payment_terms": "30% T/T deposit, 70% against B/L copy",
        })
        assert "breakdown" in result
        assert result["breakdown"]["thickness_mm"] == 30
        assert result["breakdown"]["grade"] == "premium"
        assert result["breakdown"]["estimated_20gp_containers"] >= 1
        assert "20GP" in result["trade_advisory"]
        assert result["currency"] == "USD"

