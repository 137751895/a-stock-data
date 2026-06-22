from app.core.normalize import (
    normalize_code,
    get_prefix,
    to_tencent_symbol,
    to_eastmoney_secid,
    to_cninfo_org_id,
)


class TestNormalizeCode:
    def test_pure_digits(self):
        assert normalize_code("688017") == "688017"

    def test_sh_prefix(self):
        assert normalize_code("SH688017") == "688017"

    def test_sh_prefix_lowercase(self):
        assert normalize_code("sh688017") == "688017"

    def test_sh_suffix(self):
        assert normalize_code("688017.SH") == "688017"

    def test_sh_suffix_lowercase(self):
        assert normalize_code("688017.sh") == "688017"

    def test_sz_prefix(self):
        assert normalize_code("SZ000001") == "000001"

    def test_bj_prefix(self):
        assert normalize_code("BJ832000") == "832000"

    def test_whitespace(self):
        assert normalize_code("  600519  ") == "600519"


class TestGetPrefix:
    def test_shanghai_6(self):
        assert get_prefix("600519") == "sh"

    def test_shanghai_9(self):
        assert get_prefix("900001") == "sh"

    def test_shenzhen(self):
        assert get_prefix("000001") == "sz"

    def test_shenzhen_3(self):
        assert get_prefix("300476") == "sz"

    def test_beijing(self):
        assert get_prefix("832000") == "bj"


class TestToTencentSymbol:
    def test_shanghai(self):
        assert to_tencent_symbol("600519") == "sh600519"

    def test_shenzhen(self):
        assert to_tencent_symbol("000858") == "sz000858"

    def test_with_prefix_input(self):
        assert to_tencent_symbol("SH600519") == "sh600519"


class TestToEastmoneySecid:
    def test_shanghai(self):
        assert to_eastmoney_secid("600519") == "1.600519"

    def test_shenzhen(self):
        assert to_eastmoney_secid("000858") == "0.000858"


class TestToCninfoOrgId:
    def test_shanghai(self):
        assert to_cninfo_org_id("600519") == "gssh0600519"

    def test_shenzhen(self):
        assert to_cninfo_org_id("000001") == "gssz0000001"

    def test_beijing(self):
        assert to_cninfo_org_id("832000") == "gsbj0832000"

    def test_shenzhen_3xx(self):
        assert to_cninfo_org_id("300476") == "gssz0300476"

    def test_bj_4xx(self):
        assert to_cninfo_org_id("430047") == "gsbj0430047"
