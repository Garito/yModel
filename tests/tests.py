from json import dumps

from unittest import TestCase

from tests import models

from yModel.utils import AioTestCase

class FakeApp():
  def __init__(self, models):
    self.models = models

class FakeRequest():
  def __init__(self, models, data):
    self.app = FakeApp(models)
    self.json = data

class TestMinimal(TestCase):
  def test(self):
    model = models.Minimal()
    data = {"name": "Minimal"}
    model.load(data)
    model_data = model.get_data()
    model_errors = model.get_errors()

    self.assertDictEqual(model_data, data)
    self.assertIsNone(model_errors)

  def testErrors(self):
    model = models.Minimal()
    data = {"title": "Errors"}
    model.load(data)
    model_data = model.get_data()
    model_errors = model.get_errors()
    expected_errors = {'name': ['Missing data for required field.']}

    self.assertDictEqual(model_data, {})
    self.assertDictEqual(model_errors, expected_errors)

  def testJson(self):
    model = models.Minimal()
    data = {"name": "JSON"}
    model.load(data)
    json = model.to_json()

    self.assertEqual(json, dumps(data))

  def testAttributeAccess(self):
    model = models.Minimal()
    data = {"name": "Attribute access"}
    model.load(data)

    self.assertEqual(model.name, data["name"])

class TestMinimalTree(TestCase):
  def test(self):
    model = models.MinimalTree()
    data = {"path": "/", "name": "MinimalTree"}
    model.load(data)

    self.assertEqual(model.get_url(), "/minimaltree")

class TestBadTree(TestCase):
  def test(self):
    model = models.MinimalBadTree()
    data = {"name": "BadTree"}
    model.load(data)

    self.assertRaises(AttributeError, model.get_url)

class TestRealTree(TestCase):
  def test(self):
    model = models.RealTree()
    data = {"path": "/", "name": "RealTree"}
    model.load(data)

    self.assertEqual(model.children_of_type("RealTree"), ["elements"])

class TestDecorators(AioTestCase):
  async def test(self):
    edited_name = "TestDecoratorsNameEdited"
    age = 18
    fakeRequest = FakeRequest(models, {"name": edited_name})
    model = models.DecoratorsSchema()
    model.load({"name": "TestDecoratorsName", "age": age})
    result = await model.set_name(fakeRequest)
    result = result.to_plain_dict()

    self.assertDictEqual(result, {"ok": True, "name": edited_name})
    self.assertDictEqual(model.get_data(), {"name": edited_name, "age": age})

  async def testAttributeError(self):
    edited_name = "MakeItCrash"
    age = 18
    fakeRequest = FakeRequest(models, {"name": edited_name})
    model = models.DecoratorsSchema()
    model.load({"name": "TestAttributeErrorName", "age": age})
    result = await model.set_name(fakeRequest)

    print(result.to_plain_dict())

  async def testExceptionError(self):
    edited_name = "Exception"
    age = 18
    fakeRequest = FakeRequest(models, {"name": edited_name})
    model = models.DecoratorsSchema()
    model.load({"name": "TestExceptionName", "age": age})
    result = await model.set_name(fakeRequest)

    print(result.to_plain_dict())
