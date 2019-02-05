from datetime import datetime

from json import loads, dumps

from decimal import Decimal

from unittest import TestCase

import bson
from pymongo.errors import InvalidOperation
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from marshmallow.exceptions import ValidationError

from slugify import slugify

from yModel.mongo import MongoJSONEncoder, NotFound

from yModel.utils import AioTestCase

from tests import models

MONGO_URI = "mongodb://localhost:27017"

class TestMongoEncoder(TestCase):
  def test(self):
    data = {"_id": bson.ObjectId(), "name": "The name", "age": 18, "reward": bson.decimal128.Decimal128("100")}
    dumpedandreloaded = loads(dumps(data, cls = MongoJSONEncoder))
    self.assertEqual(str(data["_id"]), dumpedandreloaded["_id"])
    self.assertEqual(str(data["reward"]), dumpedandreloaded["reward"])
    self.assertEqual(data["name"], dumpedandreloaded["name"])
    self.assertEqual(data["age"], dumpedandreloaded["age"])

  def testEncoderError(self):
    data = {"datetime": self.test}
    with self.assertRaises(TypeError):
      dumps(data, cls = MongoJSONEncoder)

class TestObjectIdErrors(TestCase):
  def test(self):
    model = models.MinimalMongo()
    data = {"_id": Decimal(10), "name": "This should produce a deserialization error"}
    model.load(data)
    errors = model.get_errors()
    self.assertNotIn("_id", model.get_data())
    self.assertIn("_id", errors)
    self.assertEqual('invalid ObjectId `10`', errors["_id"][0])

class TestCreate(AioTestCase):
  def setUp(self):
    self.table = AsyncIOMotorClient(MONGO_URI).tests.tests

  async def testNoTable(self):
    model = models.MinimalMongo()
    data = {"name": "Test create no table"}
    model.load(data)
    with self.assertRaises(InvalidOperation):
      await model.create()

  async def testNoData(self):
    model = models.MinimalMongo(self.table)
    with self.assertRaises(InvalidOperation):
      await model.create()

  async def test(self):
    model = models.MinimalMongo(self.table)
    data = {"name": "Test create"}
    model.load(data)
    await model.create()
    saved = await self.table.find_one(data)
    model_data = model.get_data()

    self.assertDictEqual(model_data, saved)
    self.assertIn("_id", model_data.keys())

    self.table.delete_one({"_id": model_data["_id"]})

class TestGet(AioTestCase):
  def setUp(self):
    self.table = AsyncIOMotorClient(MONGO_URI).tests.tests

  async def testNoTable(self):
    model = models.MinimalMongo()
    data = {"name": "Test get no table"}
    model.load(data)
    with self.assertRaises(InvalidOperation):
      await model.get(name = data["name"])

  async def testNoData(self):
    model = models.MinimalMongo(self.table)
    with self.assertRaises(NotFound):
      await model.get(name = "A name that doesn't exists")

  async def test(self):
    data = {"name": "Test get"}
    result = await self.table.insert_one(data)
    data["_id"] = result.inserted_id

    model = models.MinimalMongo(self.table)
    await model.get(name = data["name"])

    modeldata = model.get_data()
    self.assertEqual(sorted(data.items()), sorted(modeldata.items()))

    self.table.delete_one({"_id": modeldata["_id"]})

class TestUpdate(AioTestCase):
  def setUp(self):
    self.table = AsyncIOMotorClient(MONGO_URI).tests.tests

  async def testNoTable(self):
    model = models.MinimalMongo()
    model.load({"_id": bson.ObjectId(), "name": "Test update no table"})

    with self.assertRaises(InvalidOperation):
      await model.update({"name": "Test update no table updated"})

  async def testNotSaved(self):
    model = models.MinimalMongo(self.table)
    model.load({"name": "Test update not saved"})

    with self.assertRaises(InvalidOperation):
      await model.update({"name": "Test update not saved updated"})

  async def testActualData(self):
    data = {"name": "Test update actual data"}
    result = await self.table.insert_one(data)
    data["_id"] = result.inserted_id

    model = models.MinimalMongo(self.table)
    await model.get(name = data["name"])
    new_name = "Test update actual data edited"
    model.__data__["name"] = new_name
    await model.update()

    new_data = await self.table.find_one({"_id": model.get_data()["_id"]})

    self.assertEqual(new_data["name"], new_name)

    await self.table.delete_one({"_id": data["_id"]})

  async def testValidationError(self):
    data = {"name": "Test update validation error"}
    result = await self.table.insert_one(data)
    data["_id"] = result.inserted_id

    model = models.MinimalMongo(self.table)
    await model.get(name = data["name"])

    with self.assertRaises(ValidationError):
      await model.update({"name": 25})

    await self.table.delete_one({"_id": data["_id"]})

class TestRemoveField(AioTestCase):
  def setUp(self):
    self.table = AsyncIOMotorClient(MONGO_URI).tests.tests

  async def testNoTable(self):
    data = {"_id": bson.ObjectId(), "name": "Test remove field no table", "finished": True}
    model = models.AnotherMongo()
    model.load(data)

    with self.assertRaises(InvalidOperation):
      await model.remove_field("finished")

  async def testNotSaved(self):
    data = {"name": "Test remove field not saved", "finished": True}
    model = models.AnotherMongo(self.table)
    model.load(data)

    with self.assertRaises(AttributeError):
      await model.remove_field("finished")

  async def test(self):
    data = {"name": "Test remove field", "finished": True}
    result = await self.table.insert_one(data)
    data["_id"] = result.inserted_id

    model = models.AnotherMongo(self.table)
    await model.get(_id = data["_id"])
    await model.remove_field("finished")

    new_data = await self.table.find_one({"_id": data["_id"]})

    self.assertNotIn("finished", new_data)
    self.assertNotIn("finished", model.get_data())

    await self.table.delete_one({"_id": data["_id"]})

class TestDelete(AioTestCase):
  def setUp(self):
    self.table = AsyncIOMotorClient(MONGO_URI).tests.tests

  async def testNoTable(self):
    data = {"_id": bson.ObjectId(), "name": "Test delete no table"}
    model = models.MinimalMongo()
    model.load(data)

    with self.assertRaises(InvalidOperation):
      await model.delete()

  async def testNotSaved(self):
    data = {"name": "Test delete not saved"}
    model = models.MinimalMongo(self.table)
    model.load(data)

    with self.assertRaises(AttributeError):
      await model.delete()

  async def test(self):
    data = {"name": "Test delete"}
    result = await self.table.insert_one(data)
    data["_id"] = result.inserted_id

    model = models.MinimalMongo(self.table)
    await model.get(_id = data["_id"])
    await model.delete()

    check_if_exists = await self.table.find_one({"_id": data["_id"]})

    self.assertIsNone(check_if_exists)

class TestAncestors(AioTestCase):
  async def setUp(self):
    self.client = AsyncIOMotorClient(MONGO_URI)
    self.table = self.client.tests.tests
    self.papers = [
      {"type": "MinimalMongoTree", "path": "/", "name": "Parent 1", "slug": "parent-1"},
      {"type": "MinimalMongoTree", "path": "/parent-1", "name": "Parent 2", "slug": "parent-2"},
      {"type": "MinimalMongoTree", "path": "/parent-1/parent-2", "name": "Paper", "slug": "paper"}
    ]

    for paper in self.papers:
      result = await self.table.insert_one(paper)
      paper["_id"] = result.inserted_id

  async def tearDown(self):
    for paper in self.papers:
      await self.table.delete_one({"_id": paper["_id"]})

    self.client.close()

  async def testNoTable(self):
    model = models.MinimalMongoTree()
    model.load({"type": "MinimalMongoTree", "path": "/parent-1/parent-2", "name": "Paper no table", "slug": "paper-no-table"})

    with self.assertRaises(InvalidOperation):
      await model.ancestors(models)

  async def test(self):
    model = models.MinimalMongoTree(self.table)
    await model.get(_id = self.papers[-1]["_id"])
    ancestors = await model.ancestors(models)

    self.assertEqual(len(ancestors), 2)
    self.assertIsInstance(ancestors[0], models.MinimalMongoTree)
    self.assertEqual(ancestors[0].get_data()["_id"], self.papers[0]["_id"])
    self.assertIsInstance(ancestors[1], models.MinimalMongoTree)
    self.assertEqual(ancestors[1].get_data()["_id"], self.papers[1]["_id"])

  async def testParentOnly(self):
    model = models.MinimalMongoTree(self.table)
    await model.get(_id = self.papers[-1]["_id"])
    parent = await model.ancestors(models, True)

    self.assertIsInstance(parent, models.MinimalMongoTree)
    self.assertEqual(parent.get_data()["_id"], self.papers[-2]["_id"])

class TestChildren(AioTestCase):
  async def setUp(self):
    self.client = AsyncIOMotorClient(MONGO_URI)
    self.table = self.client.tests.tests

    self.papers = [
      {"type": "RealMongoTree", "path": "/testchildren/paper", "name": "Child 1", "slug": "child-1"},
      {"type": "RealMongoTree", "path": "/testchildren/paper", "name": "Child 2", "slug": "child-2"},
      {"type": "RealMongoTree", "path": "/testchildren/paper", "name": "Child 3", "slug": "child-3"},
      {"type": "User", "path": "/testchildren/paper", "name": "User 1", "slug": "user-1"},
      {"type": "User", "path": "/testchildren/paper", "name": "User 2", "slug": "user-2"},
      {"type": "RealMongoTree", "path": "/testchildren", "name": "Paper", "slug": "paper",
       "members": [], "elements": ["child-1", "child-2", "child-3"]}
    ]

    for paper in self.papers:
      result = await self.table.insert_one(paper)
      paper["_id"] = result.inserted_id
      if paper["type"] == "User":
        self.papers[-1]["members"].append(paper["_id"])

  async def tearDown(self):
    for paper in self.papers:
      await self.table.delete_one({"_id": paper["_id"]})

    self.client.close()

  async def testNoTable(self):
    model = models.RealMongoTree()

    with self.assertRaises(InvalidOperation):
      await model.children("elements", None)

  async def test(self):
    model = models.RealMongoTree(self.table)
    await model.get(_id = self.papers[-1]["_id"])
    children = await model.children("elements", models)
    ids = [child["_id"] for child in children.get_data()]

    for child in self.papers[:2]:
      self.assertIn(child["_id"], ids)

  async def testMembers(self):
    model = models.RealMongoTree(self.table)
    await model.get(_id = self.papers[-1]["_id"])
    children = await model.children("members", models)
    ids = [child["_id"] for child in children.get_data()]

    for user in self.papers[3:5]:
      self.assertIn(user["_id"], ids)

class TestDeleteTree(AioTestCase):
  async def setUp(self):
    self.client = AsyncIOMotorClient(MONGO_URI)
    self.table = self.client.tests.tests

    self.papers = [
      {"type": "RealMongoTree", "path": "/testdelete/paper", "name": "Child 1", "slug": "child-1"},
      {"type": "RealMongoTree", "path": "/testdelete/paper", "name": "Child 2", "slug": "child-2"},
      {"type": "RealMongoTree", "path": "/testdelete/paper", "name": "Child 3", "slug": "child-3"},
      {"type": "User", "path": "/testdelete/paper", "name": "User 1", "slug": "user-1"},
      {"type": "User", "path": "/testdelete/paper", "name": "User 2", "slug": "user-2"},
      {"type": "RealMongoTree", "path": "/testdelete", "name": "Paper", "slug": "paper",
       "members": [], "elements": ["child-1", "child-2", "child-3"]}
    ]

    for paper in self.papers:
      result = await self.table.insert_one(paper)
      paper["_id"] = result.inserted_id
      if paper["type"] == "User":
        self.papers[-1]["members"].append(paper["_id"])

  async def tearDown(self):
    for paper in self.papers:
      await self.table.delete_one({"_id": paper["_id"]})

    self.client.close()

  async def testNoTable(self):
    model = models.RealMongoTree()

    with self.assertRaises(InvalidOperation):
      await model.delete()

  async def test(self):
    model = models.RealMongoTree(self.table)
    await model.get(_id = self.papers[-1]["_id"])
    url = model.get_url()
    await model.delete(models)

    children = await self.table.find({"path": {"$regex": "^{}".format(url)}}).to_list(None)

    self.assertFalse(children)

class TestUpdateField(AioTestCase):
  async def setUp(self):
    self.client = AsyncIOMotorClient(MONGO_URI)
    self.table = self.client.tests.tests

    self.papers = [
      {"type": "RealMongoTree", "path": "/testupdatefield/paper", "name": "Child 1", "slug": "child-1"},
      {"type": "RealMongoTree", "path": "/testupdatefield/paper", "name": "Child 2", "slug": "child-2"},
      {"type": "RealMongoTree", "path": "/testupdatefield/paper", "name": "Child 3", "slug": "child-3"},
      {"type": "User", "path": "/testupdatefield/paper", "name": "User 1", "slug": "user-1"},
      {"type": "User", "path": "/testupdatefield/paper", "name": "User 2", "slug": "user-2"},
      {"type": "RealMongoTree", "path": "/testupdatefield", "name": "Paper", "slug": "paper",
       "members": [], "elements": ["child-1", "child-2", "child-3"]}
    ]

    for paper in self.papers:
      result = await self.table.insert_one(paper)
      paper["_id"] = result.inserted_id
      if paper["type"] == "User":
        self.papers[-1]["members"].append(paper["_id"])

  async def tearDown(self):
    for paper in self.papers:
      await self.table.delete_one({"_id": paper["_id"]})

    self.client.close()

  async def testNoTable(self):
    model = models.RealMongoTree()

    with self.assertRaises(InvalidOperation):
      await model.update({"name": "This will fail"}, models)

  async def testValidationError(self):
    model = models.RealMongoTree(self.table)
    await model.get(_id = self.papers[-1]["_id"])

    with self.assertRaises(ValidationError):
      await model.update({"path": 25}, models)
