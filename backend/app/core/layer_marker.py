# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from typing import Any, Callable, TypeVar

T = TypeVar('T')

def _mark_layer(layer_name: str) -> Callable[[T], T]:
    def decorator(obj: T) -> T:
        setattr(obj, "__layer__", layer_name)
        return obj
    return decorator

def domain_service(obj: T) -> T:
    return _mark_layer("domain")(obj)

def application_service(obj: T) -> T:
    return _mark_layer("application")(obj)

def infrastructure_service(obj: T) -> T:
    return _mark_layer("infrastructure")(obj)

def get_layer(obj: Any) -> str | None:
    return getattr(obj, "__layer__", None)
