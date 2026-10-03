import unittest
from src.schema import validate_output
from src.extractor import extract, ExtractionError
GOOD = '{"name":"Asha Mehta","age":32,"profession":"civil engineer"}'
class FakeModel:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = 0
    def generate(self, prompt):
        self.calls += 1
        return next(self.outputs)
class ValidationTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_output(GOOD).age, 32)
    def test_nulls(self):
        self.assertIsNone(validate_output('{"name":null,"age":null,"profession":null}').age)
    def test_reject_invalid(self):
        invalid = [GOOD.replace('32', v) for v in ['"32"', 'true', '32.0', '-1', '131', 'NaN', 'Infinity']]
        invalid += [GOOD.replace('"age":32,', ''), GOOD.replace('32,', '32,"age":33,'), GOOD.replace('32,', '32,"city":"Pune",'), GOOD.replace('"Asha Mehta"','" "'), GOOD.replace('"civil engineer"', '[]'), '```json\n'+GOOD+'\n```', 'Here: '+GOOD, GOOD+GOOD, '['+GOOD+']', 'null', "{'name':'Asha'}"]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                validate_output(raw)
    def test_retry_success(self):
        model = FakeModel(['not json', GOOD])
        person, attempts = extract('Asha Mehta is 32, a civil engineer.', model)
        self.assertEqual(person.age, 32)
        self.assertEqual(model.calls, 2)
        self.assertEqual([a['valid'] for a in attempts], [False, True])
    def test_failure_is_not_null_record(self):
        model = FakeModel(['bad', 'still bad'])
        with self.assertRaises(ExtractionError) as caught:
            extract('Asha Mehta is 32.', model)
        self.assertEqual(len(caught.exception.attempts), 2)
    def test_retry_disabled(self):
        model = FakeModel(['bad'])
        with self.assertRaises(ExtractionError):
            extract('Asha Mehta is 32.', model, retries=0)
        self.assertEqual(model.calls, 1)
    def test_empty_rejected_before_generation(self):
        model = FakeModel([])
        with self.assertRaises(ValueError):
            extract('  ', model)
        self.assertEqual(model.calls, 0)
    def test_overlong_rejected(self):
        with self.assertRaises(ValueError):
            extract('a'*6001, FakeModel([]))
if __name__ == '__main__':
    unittest.main()
