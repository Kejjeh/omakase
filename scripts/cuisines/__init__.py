from __future__ import annotations

from typing import Protocol

from scripts.cuisines.italian import ItalianCuisine
from scripts.cuisines.kensington import KensingtonCuisine
from scripts.cuisines.omakase import OmakaseCuisine
from scripts.cuisines.philly import PhillyCuisine


class Cuisine(Protocol):
    name: str
    sources: list

    def read_restaurants(self) -> list[dict]: ...

    def load_specialties(self) -> dict[str, dict]: ...

    def dashboard_fields(self) -> list[str]: ...


_REGISTRY: dict[str, type] = {
    OmakaseCuisine.name: OmakaseCuisine,
    ItalianCuisine.name: ItalianCuisine,
    PhillyCuisine.name: PhillyCuisine,
    KensingtonCuisine.name: KensingtonCuisine,
}


def get_cuisine(name: str) -> Cuisine:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown cuisine: {name!r}. Known: {sorted(_REGISTRY)}")
    return _REGISTRY[name]()


__all__ = ["Cuisine", "OmakaseCuisine", "ItalianCuisine", "PhillyCuisine", "KensingtonCuisine", "get_cuisine"]
