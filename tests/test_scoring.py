import unittest
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import date
from src.scoring.engine import evaluate
from src.scoring.service import rank_enterprises, score_one

DAY = date(2026, 11, 25)

class ScoringTests(unittest.TestCase):
    def sample(self, **changes):
        row = dict(id=1, name="测试企业", chain_segment="半导体设备", employee_scale="500-999 人",
                   tech_qualifications={"资质":["国家级专精特新小巨人"]},
                   investment_events=[{"时间":"2026-01"}])
        row.update(changes)
        return row

    def test_weighted_result_and_explanation(self):
        result = evaluate(self.sample(), "半导体设备", DAY)
        self.assertEqual(result["total_score"], 91.5)
        self.assertEqual(result["coverage"], 1)
        self.assertEqual(result["score_upper_bound"], 91.5)
        self.assertTrue(all(d["reason"] and d["evidence"] for d in result["dimensions"]))

    def test_missing_is_not_a_zero_dimension_or_reweighted(self):
        result = evaluate(self.sample(employee_scale=None, tech_qualifications=None, investment_events=None), "半导体设备", DAY)
        self.assertEqual(result["total_score"], 40)
        self.assertEqual(result["score_upper_bound"], 100)
        self.assertEqual(result["coverage"], .4)
        self.assertIsNone(result["dimensions"][1]["score"])

    def test_future_invalid_and_undated_events(self):
        result = evaluate(self.sample(investment_events=[{"时间":"2026-12"},{"时间":"2025-99"},{"轮次":"A轮"}]), "半导体设备", DAY)
        self.assertIsNone(result["dimensions"][3]["score"])
        self.assertEqual(len(result["warnings"]), 3)

    def test_no_qualification_stacking(self):
        row = self.sample(tech_qualifications={"资质":["国家级专精特新小巨人", "高新技术企业"]})
        self.assertEqual(evaluate(row,"半导体设备",DAY)["dimensions"][2]["score"],90)

    def test_interval_lower_bound_and_unrecognized(self):
        self.assertEqual(evaluate(self.sample(employee_scale="1000 人以上"),"半导体设备",DAY)["dimensions"][1]["score"],85)
        self.assertIsNone(evaluate(self.sample(employee_scale="未知"),"半导体设备",DAY)["dimensions"][1]["score"])

    def test_weights_validation_and_reproducibility(self):
        with self.assertRaises(ValueError):
            evaluate(self.sample(),"半导体设备",DAY, {"segment":1})
        self.assertEqual(evaluate(self.sample(),"半导体设备",DAY),evaluate(self.sample(),"半导体设备",DAY))

    def test_mismatch_and_unknown_qualification(self):
        result=evaluate(self.sample(tech_qualifications={"资质":["未识别资质"]}),"芯片设计",DAY)
        self.assertEqual(result["dimensions"][0]["score"],0)
        self.assertIsNone(result["dimensions"][2]["score"])

    def test_service_ranks_before_pagination(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "test.db"
            connection = sqlite3.connect(database)
            connection.executescript((Path(__file__).resolve().parents[1] / "data/schema.sql").read_text(encoding="utf-8"))
            connection.execute("INSERT INTO chain_segment(name,level) VALUES (?,1)", ("芯片设计",))
            for index, scale in enumerate(["1-49 人", "500-999 人", "1000 人以上"], 1):
                connection.execute(
                    "INSERT INTO enterprise(id,name,employee_scale,chain_segment,industry_code,industry_name,region,source,source_url,tech_qualifications,investment_events) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (index, f"测试企业{index}", scale, "芯片设计", "6520", "集成电路设计", "杭州", "测试夹具", "https://example.com", json.dumps({"资质": ["高新技术企业"]}), json.dumps([{"时间": "2026-01"}]))
                )
            connection.commit()
            connection.close()

            def isolated_connection():
                result = sqlite3.connect(database)
                result.row_factory = sqlite3.Row
                return result

            with patch("src.scoring.service.connect", side_effect=isolated_connection):
                first=rank_enterprises("芯片设计", page_size=1,as_of=DAY)
                full=rank_enterprises("芯片设计", page_size=100,as_of=DAY)
                self.assertEqual(first["items"][0],full["items"][0])
                self.assertEqual([r["total_score"] for r in full["items"]],sorted([r["total_score"] for r in full["items"]],reverse=True))
                item=first["items"][0]
                self.assertEqual(item["total_score"],score_one(item["enterprise_id"],"芯片设计",DAY)["total_score"])
                self.assertIsNone(score_one(-1,"芯片设计",DAY))
                with self.assertRaises(ValueError):
                    rank_enterprises("不存在的环节",as_of=DAY)
if __name__ == "__main__":
    unittest.main()
