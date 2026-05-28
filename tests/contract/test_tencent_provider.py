from app.providers.tencent import parse_tencent_fields, parse_tencent_response

# Build a sample with correct field positions (indices 0-52, 53 fields minimum)
# Key fields: 1=name, 3=price, 4=last_close, 5=open, 31=change_amt, 32=change_pct,
# 33=high, 34=low, 37=amount_wan, 38=turnover_pct, 39=pe_ttm,
# 43=amplitude_pct(NOT PB!), 44=mcap_yi, 45=float_mcap_yi, 46=pb,
# 47=limit_up, 48=limit_down, 49=vol_ratio, 52=pe_static
def _build_sample():
    fields = [""] * 53
    fields[1] = "贵州茅台"
    fields[2] = "600519"
    fields[3] = "1800.00"
    fields[4] = "1780.00"
    fields[5] = "1785.00"
    fields[31] = "20.00"
    fields[32] = "1.12"
    fields[33] = "1810.00"
    fields[34] = "1775.00"
    fields[37] = "900000"
    fields[38] = "5.00"
    fields[39] = "300.45"
    fields[43] = "7.22"
    fields[44] = "22600.00"
    fields[45] = "22600.00"
    fields[46] = "11.51"
    fields[47] = "1958.00"
    fields[48] = "1602.00"
    fields[49] = "1.20"
    fields[52] = "314.76"
    return fields


SAMPLE_VALS = _build_sample()
SAMPLE_RAW = 'v_sh600519="' + "~".join(SAMPLE_VALS) + '";'


class TestParseTencentFields:
    """Test that tencent field indices are correctly mapped."""

    def _get_vals(self):
        """Extract vals array from sample data."""
        return SAMPLE_VALS

    def test_name_at_index_1(self):
        vals = self._get_vals()
        result = parse_tencent_fields(vals)
        assert result["name"] == "贵州茅台"

    def test_price_at_index_3(self):
        vals = self._get_vals()
        result = parse_tencent_fields(vals)
        assert result["price"] == 1800.00

    def test_amplitude_at_index_43_not_pb(self):
        """CRITICAL REGRESSION: index 43 is amplitude, NOT PB."""
        vals = self._get_vals()
        result = parse_tencent_fields(vals)
        assert result["amplitude_pct"] == 7.22

    def test_pb_at_index_46(self):
        """CRITICAL REGRESSION: PB is at index 46."""
        vals = self._get_vals()
        result = parse_tencent_fields(vals)
        assert result["pb"] == 11.51

    def test_pe_ttm_at_index_39(self):
        vals = self._get_vals()
        result = parse_tencent_fields(vals)
        assert result["pe_ttm"] == 300.45

    def test_mcap_at_index_44(self):
        vals = self._get_vals()
        result = parse_tencent_fields(vals)
        assert result["mcap_yi"] == 22600.00

    def test_pe_static_at_index_52(self):
        vals = self._get_vals()
        result = parse_tencent_fields(vals)
        assert result["pe_static"] == 314.76


class TestParseTencentResponse:
    def test_parse_response_extracts_code(self):
        result = parse_tencent_response(SAMPLE_RAW)
        assert "600519" in result

    def test_parse_response_skips_short_lines(self):
        result = parse_tencent_response('v_sh600519="too~few~fields";')
        assert len(result) == 0

    def test_parse_response_handles_empty(self):
        result = parse_tencent_response("")
        assert result == {}
