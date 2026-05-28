"""Integration and contract tests for Phase 2 new endpoints:
signal (billboard, lockup, industry-ranking),
capital (block-trade, holder-num, dividend, fund-flow/daily),
news (telegraph, global-news).
"""
from unittest.mock import patch

import responses
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)

# === Signal layer tests ===

MOCK_BILLBOARD_RECORDS = [
    {"TRADE_DATE": "2026-05-28 00:00:00", "SECURITY_CODE": "002475",
     "EXPLANATION": "日涨幅偏离值达7%", "BILLBOARD_NET_AMT": 50000000,
     "TURNOVERRATE": 5.12}
]

MOCK_BILLBOARD_SEATS = [
    {"OPERATEDEPT_NAME": "中信证券北京总部", "BUY": 20000000, "SELL": 5000000, "NET": 15000000}
]


class TestBillboardAPI:
    @patch("app.services.signal_service.fetch_billboard_records", return_value=MOCK_BILLBOARD_RECORDS)
    @patch("app.services.signal_service.fetch_billboard_seats", return_value=MOCK_BILLBOARD_SEATS)
    def test_billboard_returns_200(self, mock_seats, mock_records):
        response = client.get("/api/v1/billboard/002475?trade_date=2026-05-28")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "records" in data["data"]
        assert "seats" in data["data"]
        assert data["source"] == ["eastmoney"]

    @patch("app.services.signal_service.fetch_billboard_records", return_value=[])
    def test_billboard_empty_returns_empty(self, mock_records):
        response = client.get("/api/v1/billboard/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["records"] == []
        assert data["data"]["seats"]["buy"] == []

    def test_billboard_invalid_code_returns_400(self):
        response = client.get("/api/v1/billboard/INVALID")
        assert response.status_code == 400


class TestDailyBillboardAPI:
    @patch("app.services.signal_service.fetch_daily_billboard", return_value=[
        {"TRADE_DATE": "2026-05-28", "SECURITY_CODE": "002475",
         "SECURITY_NAME_ABBR": "立讯精密", "EXPLANATION": "日涨幅偏离值达7%",
         "CLOSE_PRICE": 30.0, "CHANGE_RATE": 5.0,
         "BILLBOARD_NET_AMT": 50000000, "BILLBOARD_BUY_AMT": 80000000,
         "BILLBOARD_SELL_AMT": 30000000, "TURNOVERRATE": 5.12}
    ])
    def test_daily_billboard_returns_200(self, mock_fetch):
        response = client.get("/api/v1/billboard/daily?trade_date=2026-05-28")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_records"] == 1
        assert data["data"]["stocks"][0]["code"] == "002475"


class TestLockupAPI:
    @patch("app.services.signal_service.fetch_lockup_expiry", return_value=[
        {"FREE_DATE": "2026-06-15 00:00:00", "LIMITED_STOCK_TYPE": "首发原股东限售",
         "FREE_SHARES_NUM": 5000000, "FREE_RATIO": 2.5}
    ])
    def test_lockup_returns_200(self, mock_fetch):
        response = client.get("/api/v1/lockup/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["date"] == "2026-06-15"


class TestIndustryRankingAPI:
    @patch("app.services.signal_service.fetch_industry_ranking", return_value=[
        {"f14": "白酒", "f3": 3.5, "f12": "BK0477", "f104": 15, "f105": 3, "f140": "贵州茅台", "f136": 2.1},
        {"f14": "半导体", "f3": -1.2, "f12": "BK0478", "f104": 5, "f105": 20, "f140": "中芯国际", "f136": -0.5},
    ])
    def test_industry_ranking_returns_200(self, mock_fetch):
        response = client.get("/api/v1/industry-ranking?top_n=1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["top"]) == 1
        assert data["data"]["total"] == 2


# === Capital layer tests ===

class TestBlockTradeAPI:
    @patch("app.services.capital_service.fetch_block_trade", return_value=[
        {"TRADE_DATE": "2026-05-28 00:00:00", "DEAL_PRICE": 1800.0, "CLOSE_PRICE": 1780.0,
         "DEAL_VOLUME": 10000, "DEAL_AMT": 18000000,
         "BUYER_NAME": "机构专用", "SELLER_NAME": "中信证券"}
    ])
    def test_block_trade_returns_200(self, mock_fetch):
        response = client.get("/api/v1/block-trade/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["buyer"] == "机构专用"
        assert data["data"][0]["premium_pct"] != 0


class TestHolderNumAPI:
    @patch("app.services.capital_service.fetch_holder_num", return_value=[
        {"END_DATE": "2026-03-31 00:00:00", "HOLDER_NUM": 80000,
         "HOLDER_NUM_CHANGE": -2000, "HOLDER_NUM_RATIO": -2.44, "AVG_FREE_SHARES": 15000}
    ])
    def test_holder_num_returns_200(self, mock_fetch):
        response = client.get("/api/v1/holder-num/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"][0]["holder_num"] == 80000
        assert data["data"][0]["change_ratio"] == -2.44


class TestDividendAPI:
    @patch("app.services.capital_service.fetch_dividend_history", return_value=[
        {"EX_DIVIDEND_DATE": "2026-06-30 00:00:00", "PRETAX_BONUS_RMB": 27.46,
         "TRANSFER_RATIO": 0, "BONUS_RATIO": 0, "ASSIGN_PROGRESS": "实施方案"}
    ])
    def test_dividend_returns_200(self, mock_fetch):
        response = client.get("/api/v1/dividend/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"][0]["bonus_rmb"] == 27.46


class TestFundFlowDailyAPI:
    @responses.activate
    def test_fund_flow_daily_returns_200(self):
        responses.add(
            responses.GET,
            "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get",
            json={"data": {"klines": [
                "2026-05-28,100000,-50000,30000,70000,80000",
                "2026-05-27,200000,-60000,40000,80000,90000",
            ]}},
            status=200,
        )
        response = client.get("/api/v1/fund-flow/daily/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["date"] == "2026-05-28"


# === News layer tests ===

class TestTelegraphAPI:
    @responses.activate
    def test_telegraph_returns_200(self):
        responses.add(
            responses.GET,
            "https://www.cls.cn/nodeapi/telegraphList",
            json={"data": {"roll_data": [
                {"title": "快讯标题", "content": "快讯内容", "ctime": "1716883200"}
            ]}},
            status=200,
        )
        response = client.get("/api/v1/telegraph")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["source"] == ["cls"]


class TestGlobalNewsAPI:
    @responses.activate
    def test_global_news_returns_200(self):
        responses.add(
            responses.GET,
            "https://np-weblist.eastmoney.com/comm/web/getFastNewsList",
            json={"data": {"fastNewsList": [
                {"title": "全球快讯", "summary": "内容摘要", "showTime": "2026-05-28 10:00"}
            ]}},
            status=200,
        )
        response = client.get("/api/v1/global-news")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["source"] == ["eastmoney"]
