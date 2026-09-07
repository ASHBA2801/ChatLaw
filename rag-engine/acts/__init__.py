"""Acts catalog package for ChatLaw legal corpus."""

from .catalog import (
    ActCatalog,
    ActCatalogEntry,
    get_catalog,
    get_default_catalog_path,
    load_catalog,
)

__all__ = [
    "ActCatalog",
    "ActCatalogEntry",
    "get_catalog",
    "get_default_catalog_path",
    "load_catalog",
]
