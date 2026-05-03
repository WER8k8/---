import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.ab_test import ABTestVariantsConfig, ABTestVariantConfig


def test_valid_config():
    """测试有效的配置"""
    print("测试有效的配置...")
    try:
        config = ABTestVariantsConfig(
            variants=[
                {"id": "A", "name": "原版", "weight": 50},
                {"id": "B", "name": "变体1", "weight": 50}
            ]
        )
        print(f"✓ 有效配置通过: {config}")
        return True
    except Exception as e:
        print(f"✗ 有效配置失败: {e}")
        return False


def test_invalid_weight_sum():
    """测试权重总和不等于100"""
    print("\n测试权重总和不等于100...")
    try:
        config = ABTestVariantsConfig(
            variants=[
                {"id": "A", "name": "原版", "weight": 60},
                {"id": "B", "name": "变体1", "weight": 60}
            ]
        )
        print("✗ 应该抛出异常但没有")
        return False
    except ValueError as e:
        print(f"✓ 正确抛出异常: {e}")
        return True
    except Exception as e:
        print(f"✗ 抛出了错误的异常: {e}")
        return False


def test_duplicate_variant_ids():
    """测试重复的 variant id"""
    print("\n测试重复的 variant id...")
    try:
        config = ABTestVariantsConfig(
            variants=[
                {"id": "A", "name": "原版", "weight": 50},
                {"id": "A", "name": "变体1", "weight": 50}
            ]
        )
        print("✗ 应该抛出异常但没有")
        return False
    except ValueError as e:
        print(f"✓ 正确抛出异常: {e}")
        return True
    except Exception as e:
        print(f"✗ 抛出了错误的异常: {e}")
        return False


def test_invalid_weight_range():
    """测试权重超出范围"""
    print("\n测试权重超出范围...")
    try:
        config = ABTestVariantsConfig(
            variants=[
                {"id": "A", "name": "原版", "weight": 101},
                {"id": "B", "name": "变体1", "weight": -1}
            ]
        )
        print("✗ 应该抛出异常但没有")
        return False
    except Exception as e:
        print(f"✓ 正确抛出异常: {e}")
        return True


def test_empty_variants():
    """测试空的 variants 列表"""
    print("\n测试空的 variants 列表...")
    try:
        config = ABTestVariantsConfig(variants=[])
        print("✗ 应该抛出异常但没有")
        return False
    except ValueError as e:
        print(f"✓ 正确抛出异常: {e}")
        return True
    except Exception as e:
        print(f"✗ 抛出了错误的异常: {e}")
        return False


def test_password_validation():
    """测试密码验证"""
    print("\n测试密码验证...")
    sys.path.insert(0, os.path.dirname(__file__))
    from update_admin_password import validate_password_strength
    
    test_cases = [
        ("", False, "空密码"),
        ("short", False, "密码太短"),
        ("onlylowercase", False, "只有小写字母"),
        ("ONLYUPPERCASE", False, "只有大写字母"),
        ("MixedCase", False, "只有大小写字母"),
        ("Mixed123", False, "大小写+数字"),
        ("Mixed123!", True, "大小写+数字+特殊字符"),
        ("StrongPass123!", True, "强密码"),
    ]
    
    all_passed = True
    for password, expected_valid, description in test_cases:
        is_valid, errors = validate_password_strength(password)
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"{status} {description}: '{password}' -> valid={is_valid}")
        if not errors:
            print(f"  无错误")
        else:
            for error in errors:
                print(f"  - {error}")
        
        if is_valid != expected_valid:
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    print("="*60)
    print("A/B 测试配置验证和密码验证测试")
    print("="*60)
    
    results = []
    results.append(("有效配置", test_valid_config()))
    results.append(("权重总和验证", test_invalid_weight_sum()))
    results.append(("重复ID验证", test_duplicate_variant_ids()))
    results.append(("权重范围验证", test_invalid_weight_range()))
    results.append(("空列表验证", test_empty_variants()))
    results.append(("密码验证", test_password_validation()))
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name:20s}: {status}")
    
    all_passed = all(r[1] for r in results)
    print(f"\n总体结果: {'✓ 所有测试通过' if all_passed else '✗ 有测试失败'}")
    sys.exit(0 if all_passed else 1)
