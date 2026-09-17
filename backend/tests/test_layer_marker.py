from app.core.layer_marker import (
    domain_service,
    application_service,
    infrastructure_service,
    get_layer
)

def test_domain_service_decorator():
    @domain_service
    class MyDomainService:
        pass
        
    @domain_service
    def my_domain_func():
        pass

    assert get_layer(MyDomainService) == "domain"
    assert get_layer(my_domain_func) == "domain"

def test_application_service_decorator():
    @application_service
    class MyApplicationService:
        pass

    assert get_layer(MyApplicationService) == "application"

def test_infrastructure_service_decorator():
    @infrastructure_service
    class MyInfrastructureService:
        pass

    assert get_layer(MyInfrastructureService) == "infrastructure"

def test_get_layer_none():
    class UnmarkedService:
        pass
        
    assert get_layer(UnmarkedService) is None
    assert get_layer(lambda: None) is None
