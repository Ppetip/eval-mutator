# SPDX-License-Identifier: GPL-3.0-only
import copy
import json
import unittest
from app import evaluate, plan


def case(left,right,relation="equal",name="a"):
    return {"id":name,"relation":relation,"before":left,"after":right,"observed":True}


class RelationTests(unittest.TestCase):
    def test_strict_equality_ignores_key_order_but_not_types(self):
        cases=[case({"a":1,"b":2},{"b":2,"a":1},name="order"),case(True,1,name="types")]
        self.assertEqual([r["passed"] for r in evaluate({"cases":cases})["cases"]],[True,False])

    def test_unordered_relation_preserves_multiplicity(self):
        cases=[case([1,2,1],[1,1,2],"unordered","ok"),case([1,1],[1],"unordered","missing"),case([True],[1],"unordered","types")]
        self.assertEqual(evaluate({"cases":cases})["passed"],1)

    def test_nondecreasing_has_explicit_direction_and_rejects_bool(self):
        self.assertEqual(evaluate({"cases":[case(1,2,"nondecreasing"),case(2,1,"nondecreasing","b")]})["passed"],1)
        for value in (True,float("nan"),float("inf"),"1"):
            with self.assertRaises(ValueError):evaluate({"cases":[case(value,2,"nondecreasing")]})

    def test_plan_preserves_json_values_and_template_cannot_pass_unobserved(self):
        supplied={"tasks":[{"id":"a","input":{"b":[1,True],"a":"demo"}}]};before=copy.deepcopy(supplied)
        report=plan(supplied);probe=report["probes"][0]
        self.assertEqual(json.loads(probe["original_input"]),json.loads(probe["variant_input"]))
        self.assertNotEqual(probe["original_input"],probe["variant_input"])
        self.assertEqual(supplied,before)
        with self.assertRaises(ValueError):evaluate(report["evaluation_template"])

    def test_empty_results_are_unavailable_not_perfect(self):
        self.assertIsNone(evaluate({"cases":[]})["pass_rate"])

    def test_validation_rejects_malformed_late_cases(self):
        for bad in (case(1,1,name="a"),case(1,1,"unknown","b"),case({},[],"unordered","b"),{**case(1,1,name="b"),"observed":False}):
            with self.assertRaises(ValueError):evaluate({"cases":[case(1,1),bad]})

    def test_report_omits_raw_outputs_and_preserves_inputs(self):
        supplied={"cases":[case("synthetic-private-text","changed")]};before=copy.deepcopy(supplied)
        result=evaluate(supplied)
        self.assertEqual(supplied,before)
        self.assertNotIn("synthetic-private-text",json.dumps(result))
        self.assertEqual(len(result["cases"][0]["before_sha256"]),64)

    def test_plan_rejects_duplicate_ids_and_nonobject_inputs(self):
        for tasks in ([{"id":"a","input":[]}],[{"id":"a","input":{}},{"id":"a","input":{}}]):
            with self.assertRaises(ValueError):plan({"tasks":tasks})
