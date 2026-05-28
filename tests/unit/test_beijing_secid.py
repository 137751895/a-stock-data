"""Unit tests for Beijing stock exchange code handling.

Covers: to_eastmoney_secid, get_prefix, to_tencent_symbol, to_cninfo_org_id
for Beijing exchange codes (8xxxxx main board, 4xxxxx innovation board).
"""
from app.core.normalize import (
    to_eastmoney_secid,
    get_prefix,
    to_tencent_symbol,
    to_cninfo_org_id,
    validate_code,
)


class TestBeijingSecid:
    def test_bj_8xx_secid(self):
        """BJ main board 8xxxxx -> 0.{code}"""
        assert to_eastmoney_secid("832000") == "0.832000"

    def test_bj_4xx_secid(self):
        """BJ innovation board 4xxxxx -> 0.{code}"""
        assert to_eastmoney_secid("430047") == "0.430047"

    def test_bj_8xx_with_prefix(self):
        assert to_eastmoney_secid("BJ832000") == "0.832000"

    def test_shanghai_9xx_secid(self):
        """Shanghai B-shares 9xxxxx -> 1.{code}"""
        assert to_eastmoney_secid("900001") == "1.900001"


class TestBeijingPrefix:
    def test_8xx_is_bj(self):
        assert get_prefix("832000") == "bj"

    def test_4xx_is_bj(self):
        assert get_prefix("430047") == "bj"


class TestBeijingTencentSymbol:
    def test_8xx_tencent(self):
        assert to_tencent_symbol("832000") == "bj832000"

    def test_4xx_tencent(self):
        assert to_tencent_symbol("430047") == "bj430047"


class TestBeijingOrgId:
    def test_8xx_org_id(self):
        assert to_cninfo_org_id("832000") == "gsbj0832000"

    def test_4xx_org_id(self):
        assert to_cninfo_org_id("430047") == "gsbj0430047"


class TestBeijingValidation:
    def test_8xx_valid(self):
        assert validate_code("832000") == "832000"

    def test_4xx_valid(self):
        assert validate_code("430047") == "430047"

    def test_bj_prefix_valid(self):
        assert validate_code("BJ832000") == "832000"
