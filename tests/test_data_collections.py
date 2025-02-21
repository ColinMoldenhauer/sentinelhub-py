"""
Unit tests for data_collections module
"""
from typing import Any

import pytest

from sentinelhub import DataCollection
from sentinelhub.data_collections import DataCollectionDefinition


def test_repr() -> None:
    definition = DataCollection.SENTINEL1_IW.value
    representation = repr(definition)

    assert isinstance(representation, str)
    assert representation.count("\n") >= 5


def test_derive() -> None:
    definition = DataCollectionDefinition(api_id="X", wfs_id="Y")
    derived_definition = definition.derive(wfs_id="Z")

    assert derived_definition.api_id == "X"
    assert derived_definition.wfs_id == "Z"
    assert derived_definition.collection_type is None


def test_compare() -> None:
    def1 = DataCollectionDefinition(api_id="X", _name="A")
    def2 = DataCollectionDefinition(api_id="X", _name="B")

    assert def1 == def2


def test_define() -> None:
    for _ in range(3):
        data_collection = DataCollection.define(
            "NEW", api_id="X", sensor_type="Sensor", bands=("B01",), is_timeless=True
        )

    assert data_collection == DataCollection.NEW

    with pytest.raises(ValueError):
        DataCollection.define("NEW_NEW", api_id="X", sensor_type="Sensor", bands=("B01",), is_timeless=True)

    with pytest.raises(ValueError):
        DataCollection.define("NEW", api_id="Y")


def test_define_from() -> None:
    bands = ["B01", "XYZ"]
    for _ in range(3):
        data_collection = DataCollection.define_from(DataCollection.SENTINEL5P, "NEW_5P", api_id="X", bands=bands)

    assert data_collection == DataCollection.NEW_5P
    assert data_collection.api_id == "X"
    assert data_collection.wfs_id == DataCollection.SENTINEL5P.wfs_id
    assert data_collection.bands == tuple(bands)


def test_define_byoc_and_batch() -> None:
    byoc_id = "0000d273-7e89-4f00-971e-9024f89a0000"
    byoc = DataCollection.define_byoc(byoc_id, name="MY_BYOC")
    batch = DataCollection.define_batch(byoc_id, name="MY_BATCH")

    assert byoc == DataCollection.MY_BYOC
    assert batch == DataCollection.MY_BATCH

    for data_collection in [byoc, batch]:
        assert data_collection.api_id.endswith(byoc_id)
        assert data_collection.collection_id == byoc_id


def test_attributes() -> None:
    data_collection = DataCollection.SENTINEL3_OLCI

    for attr_name in ["api_id", "catalog_id", "wfs_id", "service_url", "bands", "sensor_type"]:
        value = getattr(data_collection, attr_name)
        assert value is not None
        assert value == getattr(data_collection.value, attr_name)

    data_collection = DataCollection.define("EMPTY")

    for attr_name in ["api_id", "catalog_id", "wfs_id", "bands"]:
        with pytest.raises(ValueError):
            getattr(data_collection, attr_name)

    assert data_collection.service_url is None


def test_sentinel1_checks() -> None:
    assert DataCollection.SENTINEL1_IW.is_sentinel1
    assert not DataCollection.SENTINEL2_L1C.is_sentinel1

    assert DataCollection.SENTINEL1_IW_ASC.contains_orbit_direction("ascending")
    assert not DataCollection.SENTINEL1_IW_DES.contains_orbit_direction("ascending")

    assert DataCollection.SENTINEL2_L2A.contains_orbit_direction("descending")


def test_get_available_collections() -> None:
    collections = DataCollection.get_available_collections()
    assert helper_check_collection_list(collections)


def helper_check_collection_list(collection_list: Any) -> bool:
    is_list = isinstance(collection_list, list)
    contains_collections = all(isinstance(data_collection, DataCollection) for data_collection in collection_list)
    return is_list and contains_collections


def test_transfer_with_ray(ray: Any) -> None:
    """This test makes sure that the process of transferring a custom DataCollection object to a Ray worker and back
    works correctly.
    """
    collection = DataCollection.SENTINEL2_L1C.define_from("MY_NEW_COLLECTION", api_id="xxx")

    collection_future = ray.remote(lambda x: x).remote(collection)
    transferred_collection = ray.get(collection_future)

    assert collection is transferred_collection
