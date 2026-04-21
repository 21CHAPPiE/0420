from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import get_config
from app.etl.pdf_text_extractor import extract_pdf_text


@dataclass
class MonthlyPlanRow:
    plan_month: int
    rainfall_mm: float
    inflow_100m_m3: float
    upstream_intake_100m_m3: float
    month_start_wl_m: float
    month_end_wl_m: float
    generation_water_100m_m3: float
    water_consumption_rate_m3_per_kwh: float
    generation_10k_kwh: float


def _read_text() -> str:
    text_path = extract_pdf_text(force=False)
    return Path(text_path).read_text(encoding="utf-8")


def _clean_text(text: str) -> str:
    text = text.replace("\x0c", "\n")
    text = text.replace("\u0000", "")
    text = text.replace("\r\n", "\n")
    return text


def _extract_between(text: str, start: str, end: str) -> str:
    pattern = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), flags=re.S)
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Could not find section between `{start}` and `{end}`")
    return match.group(1)


def _extract_float(pattern: str, text: str) -> float:
    match = re.search(pattern, text, flags=re.S)
    if not match:
        raise ValueError(f"Pattern not found: {pattern}")
    return float(match.group(1))


def parse_basic_info(text: str) -> Dict[str, object]:
    return {
        "reservoir_code": "TANKENG",
        "reservoir_name": "滩坑水电站",
        "station_name": "滩坑水电站",
        "river_name": "小溪干流下游",
        "basin_name": "瓯江流域",
        "location_desc": "青田县境内小溪干流下游",
        "upstream_area_km2": 3330.0,
        "installed_capacity_mw": 604.0,
        "reservoir_type": "多年调节",
        "main_functions": "发电、防洪、综合利用",
        "owner_org": "浙江浙能北海水力发电有限公司",
        "source_doc": "tankeng_2025_plan.pdf",
    }


def parse_control_indices(text: str) -> List[Dict[str, object]]:
    return [
        {"index_code": "CHECK_FLOOD_WL", "index_name": "校核洪水位", "index_value": 169.15, "unit": "m", "season_tag": "全年", "control_type": "水位"},
        {"index_code": "DESIGN_FLOOD_WL", "index_name": "设计洪水位", "index_value": 165.87, "unit": "m", "season_tag": "全年", "control_type": "水位"},
        {"index_code": "FLOOD_HIGH_WL", "index_name": "防洪高水位", "index_value": 161.50, "unit": "m", "season_tag": "全年", "control_type": "水位"},
        {"index_code": "NORMAL_WL", "index_name": "正常蓄水位", "index_value": 160.00, "unit": "m", "season_tag": "全年", "control_type": "水位"},
        {"index_code": "MEIYU_LIMIT_WL", "index_name": "梅汛期限制水位", "index_value": 160.00, "unit": "m", "season_tag": "梅汛期", "control_type": "水位"},
        {"index_code": "TYPHOON_LIMIT_WL", "index_name": "台汛期限制水位", "index_value": 156.50, "unit": "m", "season_tag": "台汛期", "control_type": "水位"},
        {"index_code": "DEAD_WL", "index_name": "死水位", "index_value": 120.00, "unit": "m", "season_tag": "全年", "control_type": "水位"},
        {"index_code": "TOTAL_CAPACITY", "index_name": "总库容", "index_value": 41.90, "unit": "亿m3", "season_tag": "全年", "control_type": "库容"},
        {"index_code": "NORMAL_CAPACITY", "index_name": "正常库容", "index_value": 35.20, "unit": "亿m3", "season_tag": "全年", "control_type": "库容"},
        {"index_code": "REGULATION_CAPACITY", "index_name": "调节库容", "index_value": 21.26, "unit": "亿m3", "season_tag": "全年", "control_type": "库容"},
        {"index_code": "FLOOD_CAPACITY", "index_name": "防洪库容", "index_value": 3.50, "unit": "亿m3", "season_tag": "汛期", "control_type": "库容"},
        {"index_code": "ASSURED_OUTPUT", "index_name": "设计保证出力", "index_value": 87.75, "unit": "MW", "season_tag": "全年", "control_type": "装机"},
        {"index_code": "AVG_ANNUAL_GENERATION", "index_name": "多年平均年发电量", "index_value": 10.23, "unit": "亿kWh", "season_tag": "全年", "control_type": "发电"},
    ]


def parse_period_rules() -> List[Dict[str, object]]:
    return [
        {"rule_year": 2025, "period_code": "MEIYU", "period_name": "梅汛期", "start_date": "2025-04-15", "end_date": "2025-06-30", "control_water_level_m": 160.0, "upper_water_level_m": 160.0, "lower_water_level_m": None, "rule_text": "梅汛期限制水位和起调水位为160.00m"},
        {"rule_year": 2025, "period_code": "TRANSITION", "period_name": "过渡期", "start_date": "2025-07-01", "end_date": "2025-07-15", "control_water_level_m": None, "upper_water_level_m": 160.0, "lower_water_level_m": 156.5, "rule_text": "梅汛期到台汛期过渡期，水位由160.00m逐渐过渡至156.50m"},
        {"rule_year": 2025, "period_code": "TYPHOON", "period_name": "台汛期", "start_date": "2025-07-16", "end_date": "2025-10-15", "control_water_level_m": 156.5, "upper_water_level_m": 156.5, "lower_water_level_m": None, "rule_text": "台汛期限制水位和起调水位为156.50m"},
        {"rule_year": 2025, "period_code": "NON_FLOOD", "period_name": "非汛期", "start_date": "2025-11-01", "end_date": "2026-03-31", "control_water_level_m": 160.0, "upper_water_level_m": 160.0, "lower_water_level_m": 120.0, "rule_text": "非汛期兴利上限水位160.00m，兴利下限水位120.00m"},
    ]


def parse_dispatch_rules() -> List[Dict[str, object]]:
    return [
        {
            "rule_year": 2025,
            "rule_code": "DISPATCH_001",
            "rule_name": "台汛期超过汛限后补偿凑泄",
            "scenario_type": "FLOOD",
            "period_code": "TYPHOON",
            "trigger_type": "WATER_LEVEL",
            "min_water_level_m": 156.5,
            "max_water_level_m": 161.5,
            "threshold_flow_m3s": 14000,
            "forecast_condition": "考虑滩坑至鹤城站区间流量及5小时传播时间",
            "action_text": "按补偿凑泄方式调度，控制滩坑水库下泄流量，使组合流量不超过14000m3/s",
            "action_type": "COMPENSATED_RELEASE",
            "priority_no": 1,
        },
        {
            "rule_year": 2025,
            "rule_code": "DISPATCH_002",
            "rule_name": "梅汛期和枯水期超过正常蓄水位后补偿凑泄",
            "scenario_type": "FLOOD",
            "period_code": "MEIYU",
            "trigger_type": "WATER_LEVEL",
            "min_water_level_m": 160.0,
            "max_water_level_m": 161.5,
            "threshold_flow_m3s": None,
            "forecast_condition": None,
            "action_text": "按补偿凑泄方式调度，最小下泄流量为机组发电流量",
            "action_type": "COMPENSATED_RELEASE",
            "priority_no": 2,
        },
        {
            "rule_year": 2025,
            "rule_code": "DISPATCH_003",
            "rule_name": "防洪高水位以上小超限控制流量下泄",
            "scenario_type": "FLOOD",
            "period_code": None,
            "trigger_type": "WATER_LEVEL",
            "min_water_level_m": 161.5,
            "max_water_level_m": 161.7,
            "threshold_flow_m3s": 6000,
            "forecast_condition": None,
            "action_text": "当161.5m<Z<=161.7m时，按6000m3/s控制流量下泄洪水",
            "action_type": "CONTROLLED_RELEASE",
            "priority_no": 3,
        },
        {
            "rule_year": 2025,
            "rule_code": "DISPATCH_004",
            "rule_name": "超161.7m全开溢洪道并机组参与泄洪",
            "scenario_type": "FLOOD",
            "period_code": None,
            "trigger_type": "WATER_LEVEL",
            "min_water_level_m": 161.7,
            "max_water_level_m": 165.27,
            "threshold_flow_m3s": None,
            "forecast_condition": None,
            "action_text": "溢洪道闸门全部打开下泄洪水，电站机组参与泄洪",
            "action_type": "FULL_SPILLWAY_OPEN",
            "priority_no": 4,
        },
        {
            "rule_year": 2025,
            "rule_code": "DISPATCH_005",
            "rule_name": "超0.2%洪水位开启泄洪洞并停发",
            "scenario_type": "EXTREME_FLOOD",
            "period_code": None,
            "trigger_type": "WATER_LEVEL",
            "min_water_level_m": 165.27,
            "max_water_level_m": None,
            "threshold_flow_m3s": None,
            "forecast_condition": None,
            "action_text": "溢洪道闸门全部打开，并开启泄洪洞参与泄洪，发电暂停",
            "action_type": "SPILLWAY_AND_TUNNEL",
            "priority_no": 5,
        },
    ]


def parse_dispatch_authority_rules() -> List[Dict[str, object]]:
    return [
        {"rule_year": 2025, "authority_code": "AUTH_001", "period_code": "MEIYU", "trigger_desc": "梅汛期库水位不超过160.00m", "min_water_level_m": None, "max_water_level_m": 160.0, "min_flow_m3s": None, "max_flow_m3s": None, "authority_org": "浙江浙能北海水力发电有限公司", "copy_to_orgs": None, "remarks": None},
        {"rule_year": 2025, "authority_code": "AUTH_002", "period_code": "MEIYU", "trigger_desc": "梅汛期库水位超过160.00m", "min_water_level_m": 160.0, "max_water_level_m": None, "min_flow_m3s": None, "max_flow_m3s": None, "authority_org": "丽水市水利局", "copy_to_orgs": None, "remarks": None},
        {"rule_year": 2025, "authority_code": "AUTH_003", "period_code": "TYPHOON", "trigger_desc": "台汛期库水位低于156.50m", "min_water_level_m": None, "max_water_level_m": 156.5, "min_flow_m3s": None, "max_flow_m3s": None, "authority_org": "浙江浙能北海水力发电有限公司", "copy_to_orgs": None, "remarks": None},
        {"rule_year": 2025, "authority_code": "AUTH_004", "period_code": "TYPHOON", "trigger_desc": "台汛期库水位超过156.50m", "min_water_level_m": 156.5, "max_water_level_m": None, "min_flow_m3s": None, "max_flow_m3s": None, "authority_org": "丽水市水利局", "copy_to_orgs": None, "remarks": None},
    ]


def parse_monthly_plan() -> List[MonthlyPlanRow]:
    return [
        MonthlyPlanRow(1, 50, 0.45, 0.0, 150.93, 150.28, 0.85, 3.38, 2500),
        MonthlyPlanRow(2, 100, 1.4, 0.0, 150.28, 150.63, 1.19, 3.40, 3500),
        MonthlyPlanRow(3, 155, 3.0, 0.0, 150.63, 151.10, 2.71, 3.39, 8000),
        MonthlyPlanRow(4, 135, 2.6, 0.0184, 151.10, 150.33, 3.05, 3.39, 9000),
        MonthlyPlanRow(5, 205, 4.25, 0.0188, 150.33, 150.02, 4.42, 3.40, 13000),
        MonthlyPlanRow(6, 290, 7.8, 0.0250, 150.02, 151.61, 6.80, 3.40, 20000),
        MonthlyPlanRow(7, 150, 3.2, 0.0340, 151.61, 150.16, 4.06, 3.38, 12000),
        MonthlyPlanRow(8, 135, 3.0, 0.0330, 150.16, 150.01, 3.06, 3.40, 9000),
        MonthlyPlanRow(9, 155, 3.3, 0.0323, 150.01, 150.35, 3.06, 3.40, 9000),
        MonthlyPlanRow(10, 55, 1.2, 0.0340, 150.35, 149.18, 1.87, 3.40, 5500),
        MonthlyPlanRow(11, 75, 1.4, 0.0340, 149.18, 148.32, 1.88, 3.42, 5500),
        MonthlyPlanRow(12, 55, 1.1, 0.0275, 148.32, 147.52, 1.54, 3.43, 4500),
    ]


def parse_warning_rules() -> List[Dict[str, object]]:
    return [
        {
            "rule_year": 2025,
            "warning_code": "WARN_001",
            "warning_name": "高水位预警",
            "warning_type": "HIGH_WL",
            "trigger_desc": "蓄水位超过160.00m且预报最高水位将达到161.50m",
            "trigger_water_level_m": 160.0,
            "trigger_flow_m3s": None,
            "lead_time_minutes": None,
            "warning_scope": "景宁大均、红星、鹤溪、渤海、九龙，青田北山、岭根",
            "disposal_text": "提前发布风险预警，做好人员转移、堤防巡防查险及抢险救援准备",
        },
        {
            "rule_year": 2025,
            "warning_code": "WARN_002",
            "warning_name": "泄洪放水预警",
            "warning_type": "RELEASE",
            "trigger_desc": "梅汛期逼近159.50m或台汛期逼近156.00m，根据气象预报实施主动性预泄",
            "trigger_water_level_m": None,
            "trigger_flow_m3s": None,
            "lead_time_minutes": 60,
            "warning_scope": "上游坝前300m，下游至左右岸交通桥",
            "disposal_text": "在预定闸门开启时间前1小时拉泄洪警报，并派人巡逻检查",
        },
    ]


def parse_gate_operation_rules() -> List[Dict[str, object]]:
    open_sequence = ["#1", "#6", "#3", "#4", "#2", "#5"]
    close_sequence = ["#5", "#2", "#4", "#3", "#6", "#1"]
    rows = []
    for idx, gate_no in enumerate(open_sequence, start=1):
        rows.append({"rule_year": 2025, "gate_group_name": "spillway_main", "operation_type": "OPEN", "sequence_no": idx, "gate_no": gate_no, "remarks": "多数孔开启，切忌少数孔高开度泄洪"})
    for idx, gate_no in enumerate(close_sequence, start=1):
        rows.append({"rule_year": 2025, "gate_group_name": "spillway_main", "operation_type": "CLOSE", "sequence_no": idx, "gate_no": gate_no, "remarks": "多数孔开启，切忌少数孔高开度泄洪"})
    return rows


def parse_annual_operation_stats() -> List[Dict[str, object]]:
    rows = [
        (2009, 1680.8, 30.2565, 40896.576),
        (2010, 2299.8, 52.6591, 140658.984),
        (2011, 1341.0, 22.1600, 87673.384),
        (2012, 2087.1, 44.5758, 113708.472),
        (2013, 1863.5, 39.2533, 113118.640),
        (2014, 2000.1, 44.2930, 137666.144),
        (2015, 2138.6, 44.5687, 121682.408),
        (2016, 2242.7, 52.1648, 155347.456),
        (2017, 1674.4, 31.7282, 110080.744),
        (2018, 1576.3, 26.1557, 72057.728),
        (2019, 1810.2, 41.5838, 133844.392),
        (2020, 1398.2, 21.3109, 77354.712),
        (2021, 1855.0, 34.2142, 84825.080),
        (2022, 1882.5, 40.5796, 112062.496),
        (2023, 1510.9, 24.6739, 76555.456),
        (2024, 1995.4, 43.5677, 113442.504),
    ]
    result = []
    for year, rainfall, inflow, generation in rows:
        result.append(
            {
                "stat_year": year,
                "rainfall_mm": rainfall,
                "inflow_100m_m3": inflow,
                "generation_10k_kwh": generation,
                "is_average_row": 0,
            }
        )
    result.append(
        {
            "stat_year": None,
            "rainfall_mm": 1834.8,
            "inflow_100m_m3": 37.1091,
            "generation_10k_kwh": 110005.240,
            "is_average_row": 1,
        }
    )
    return result


def parse_gate_operation_log() -> List[Dict[str, object]]:
    rows = [
        ("2016-09-28 16:00:00", 156.98, 35.32, [2.45, None, 2.45, 2.45, None, 2.45], 1500),
        ("2016-09-28 18:50:00", 157.92, 37.22, [3.58, None, 3.58, 3.58, None, 3.58], 2000),
        ("2016-09-28 21:30:00", 158.78, 38.12, [3.58, 2.45, 3.58, 3.58, 2.45, 3.58], 2500),
        ("2016-09-28 22:00:00", 158.86, 38.73, [3.58, 4.70, 3.58, 3.58, 4.70, 3.58], 3000),
        ("2016-09-28 22:47:00", 159.05, 39.20, [2.20, None, None, None, None, 2.20], 1000),
        ("2016-09-29 02:30:00", 159.66, 36.49, [2.20, None, 2.45, 2.45, None, 2.20], 1500),
        ("2016-09-29 04:07:00", 159.84, 37.36, [3.00, None, 3.00, 3.00, None, 3.00], 2000),
        ("2016-09-29 08:00:00", 160.35, 37.77, [3.00, 2.09, 3.00, 3.00, 2.09, 3.00], 2500),
        ("2016-09-29 11:15:00", 160.58, 38.41, [3.00, 4.50, 3.00, 3.00, 4.50, 3.00], 3000),
        ("2016-09-30 00:30:00", 159.93, 38.83, [2.00, None, 2.00, 2.00, None, 2.00], 1500),
        ("2016-10-01 20:30:00", 158.07, 36.81, [None, None, None, None, None, None], 540),
    ]
    result = []
    for event_time, up_wl, down_wl, gates, outflow in rows:
        result.append(
            {
                "event_time": event_time,
                "upstream_wl_m": up_wl,
                "downstream_wl_m": down_wl,
                "gate_1_opening_m": gates[0],
                "gate_2_opening_m": gates[1],
                "gate_3_opening_m": gates[2],
                "gate_4_opening_m": gates[3],
                "gate_5_opening_m": gates[4],
                "gate_6_opening_m": gates[5],
                "outflow_m3s": outflow,
                "source_event": "2016-09 flood",
            }
        )
    return result


def parse_flood_forecast_stats() -> List[Dict[str, object]]:
    rows = [
        ("2024052720", "2024-05-27 05:00:00", "2024-05-29 23:00:00", 53.0, 1160, 1190, 97.4, 1.0539, 154.05),
        ("2024060202", "2024-05-31 14:00:00", "2024-06-05 08:00:00", 125.5, 2270, 2290, 99.1, 3.0207, 156.04),
        ("2024061623", "2024-06-10 02:00:00", "2024-06-19 11:00:00", 366.1, 3380, 3640, 92.3, 12.1054, 159.40),
        ("2024072617", "2024-07-24 11:00:00", "2024-07-28 08:00:00", 137.6, 1250, 1160, 92.8, 1.4529, 151.96),
    ]
    return [
        {
            "flood_no": flood_no,
            "start_time": start_time,
            "end_time": end_time,
            "rainfall_mm": rainfall,
            "actual_peak_m3s": actual_peak,
            "forecast_peak_m3s": forecast_peak,
            "forecast_accuracy_pct": accuracy,
            "flood_volume_100m_m3": volume,
            "highest_wl_m": highest_wl,
        }
        for flood_no, start_time, end_time, rainfall, actual_peak, forecast_peak, accuracy, volume, highest_wl in rows
    ]


def parse_contact_directory() -> List[Dict[str, object]]:
    return [
        {"person_name": "钱伟斌", "role_title": "董事长、党总支书记、总经理", "phone_number": "13867308500", "team_type": "防汛领导小组", "remarks": None},
        {"person_name": "蒋品华", "role_title": "党总支副书记、工会主席", "phone_number": "13968173503", "team_type": "防汛领导小组", "remarks": None},
        {"person_name": "缪奇", "role_title": "副总经理、党总支委员", "phone_number": "13819516272", "team_type": "防汛领导小组", "remarks": None},
        {"person_name": "陈荣洲", "role_title": "副总经理、党总支委员", "phone_number": "13732550039", "team_type": "防汛领导小组", "remarks": None},
        {"person_name": "干建丽", "role_title": "副总工程师", "phone_number": "13588779371", "team_type": "防汛领导小组", "remarks": None},
        {"person_name": "郭振兴", "role_title": "防汛办主任", "phone_number": "13732550020", "team_type": "防汛办公室", "remarks": None},
        {"person_name": "王菊芬", "role_title": "专业管理岗（水调专业）", "phone_number": "13732550049", "team_type": "防汛办公室", "remarks": None},
    ]


def parse_engineering_characteristics() -> List[Dict[str, object]]:
    return [
        {"category_name": "水文", "item_name": "坝址以上流域面积", "metric_name": "流域面积", "metric_value": "3330", "unit": "km2", "remark": None},
        {"category_name": "水文", "item_name": "多年平均流量", "metric_name": "多年平均流量", "metric_value": "120", "unit": "m3/s", "remark": None},
        {"category_name": "水文", "item_name": "年径流量", "metric_name": "年径流量", "metric_value": "37.8", "unit": "亿m3", "remark": None},
        {"category_name": "水库", "item_name": "校核洪水位", "metric_name": "校核洪水位（PMF）", "metric_value": "169.15", "unit": "m", "remark": None},
        {"category_name": "水库", "item_name": "设计洪水位", "metric_name": "设计洪水位（P=0.1%）", "metric_value": "165.87", "unit": "m", "remark": None},
        {"category_name": "水库", "item_name": "防洪高水位", "metric_name": "防洪高水位（P=5%）", "metric_value": "161.50", "unit": "m", "remark": None},
        {"category_name": "水库", "item_name": "正常蓄水位", "metric_name": "正常蓄水位", "metric_value": "160.00", "unit": "m", "remark": None},
        {"category_name": "水库", "item_name": "台汛期限制水位", "metric_name": "台汛期限制水位", "metric_value": "156.50", "unit": "m", "remark": None},
        {"category_name": "水库", "item_name": "死水位", "metric_name": "死水位", "metric_value": "120.00", "unit": "m", "remark": None},
        {"category_name": "水库", "item_name": "总库容", "metric_name": "总库容", "metric_value": "41.90", "unit": "亿m3", "remark": None},
        {"category_name": "水库", "item_name": "正常库容", "metric_name": "正常库容", "metric_value": "35.20", "unit": "亿m3", "remark": None},
        {"category_name": "水库", "item_name": "调节库容", "metric_name": "调节库容", "metric_value": "21.26", "unit": "亿m3", "remark": None},
        {"category_name": "水库", "item_name": "防洪库容", "metric_name": "防洪库容", "metric_value": "3.50", "unit": "亿m3", "remark": None},
        {"category_name": "工程效益指标", "item_name": "装机容量", "metric_name": "装机容量", "metric_value": "604", "unit": "MW", "remark": None},
        {"category_name": "工程效益指标", "item_name": "保证出力", "metric_name": "保证出力(P=90%)", "metric_value": "87.75", "unit": "MW", "remark": None},
        {"category_name": "工程效益指标", "item_name": "多年平均发电量", "metric_name": "多年平均发电量", "metric_value": "10.23", "unit": "亿kWh", "remark": None},
        {"category_name": "主要建筑物及设备", "item_name": "坝顶高程", "metric_name": "坝顶高程", "metric_value": "171.0", "unit": "m", "remark": None},
        {"category_name": "主要建筑物及设备", "item_name": "最大坝高", "metric_name": "最大坝高", "metric_value": "162.0", "unit": "m", "remark": None},
        {"category_name": "主要建筑物及设备", "item_name": "坝顶长度", "metric_name": "坝顶长度", "metric_value": "507", "unit": "m", "remark": None},
        {"category_name": "主要建筑物及设备", "item_name": "溢洪道设计泄洪流量", "metric_name": "设计泄洪流量", "metric_value": "11085", "unit": "m3/s", "remark": None},
        {"category_name": "主要建筑物及设备", "item_name": "溢洪道校核泄洪流量", "metric_name": "校核泄洪流量（PMF）", "metric_value": "14335", "unit": "m3/s", "remark": None},
        {"category_name": "主要建筑物及设备", "item_name": "泄洪洞设计泄洪流量", "metric_name": "设计泄洪流量", "metric_value": "1699", "unit": "m3/s", "remark": None},
        {"category_name": "主要建筑物及设备", "item_name": "泄洪洞校核泄洪流量", "metric_name": "校核泄洪流量", "metric_value": "1728", "unit": "m3/s", "remark": None},
    ]


def build_semantic_docs(parsed: Dict[str, object]) -> Dict[str, str]:
    monthly = parsed["monthly_operation_plan"]
    control_index = parsed["control_indices"]
    return {
        "sql_semantics.txt": "\n".join(
            [
                "# 滩坑水库 SQL 语义说明",
                "",
                "## 核心问法映射",
                "- 正常蓄水位 -> reservoir_control_index.NORMAL_WL",
                "- 防洪高水位 -> reservoir_control_index.FLOOD_HIGH_WL",
                "- 梅汛期限制水位 -> reservoir_control_index.MEIYU_LIMIT_WL",
                "- 台汛期限制水位 -> reservoir_control_index.TYPHOON_LIMIT_WL",
                "- 月初水位 -> reservoir_monthly_operation_plan.month_start_wl_m",
                "- 月末水位 -> reservoir_monthly_operation_plan.month_end_wl_m",
                "- 发电量 -> reservoir_monthly_operation_plan.generation_10k_kwh",
                "- 联系电话 -> reservoir_contact_directory.phone_number",
                "",
                "## 单位约定",
                "- 所有 *_100m_m3 字段在本项目中统一表示 亿m3。",
                "- 例如 inflow_100m_m3 = 7.8 表示 7.8 亿m3，不是 780 万m3。",
                "- generation_10k_kwh 表示 万kWh。",
                "- month_start_wl_m 和 month_end_wl_m 表示 m。",
                "",
                "## 关键控制指标",
            ]
            + [f"- {row['index_name']}: {row['index_value']}{row['unit']}" for row in control_index]
            + [
                "",
                "## 2025 分月调度计划摘要",
            ]
            + [
                f"- {row['plan_month']}月: 来水{row['inflow_100m_m3']}亿m3, 月末水位{row['month_end_wl_m']}m, 发电量{row['generation_10k_kwh']}万kWh"
                for row in monthly
            ]
        ),
        "dispatch_rules.txt": "\n".join(
            [
                "# 滩坑水库调度规则摘要",
                "",
                "1. 台汛期 156.5m < Z <= 161.5m 时，按补偿凑泄方式调度。",
                "2. 梅汛期和枯水期 160.0m < Z <= 161.5m 时，按补偿凑泄方式调度。",
                "3. 161.5m < Z <= 161.7m 时，按 6000m3/s 控制流量下泄。",
                "4. Z > 161.7m 时，溢洪道闸门全部打开，机组参与泄洪。",
                "5. Z > 165.27m 时，开启泄洪洞参与泄洪，发电暂停。",
                "",
                "## 闸门顺序",
                "- 开启顺序: #1 -> #6 -> #3 -> #4 -> #2 -> #5",
                "- 关闭顺序: #5 -> #2 -> #4 -> #3 -> #6 -> #1",
            ]
        ),
        "flood_control_explanations.txt": "\n".join(
            [
                "# 滩坑水库防洪与分期控制解释",
                "",
                "## 汛期划分",
                "- 梅汛期: 4月15日到6月30日",
                "- 过渡期: 7月1日到7月15日",
                "- 台汛期: 7月16日到10月15日",
                "",
                "## 为什么台汛期限制水位更低",
                "- 滩坑水电站梅汛期限制水位和起调水位为160.00m。",
                "- 台汛期限制水位和起调水位为156.50m。",
                "- 台汛期比梅汛期低3.50m，目的在于预留更多防洪库容，应对台风暴雨和更强的洪水风险。",
                "- 过渡期内，当预报有台风影响时，滩坑水库通过机组满发和开启溢洪道泄洪等方式，在台风影响前将水位降至156.50m。",
                "- 因此，台汛期限制水位更低的直接原因，是台风期需要更大的调洪空间和更保守的防洪调度策略。",
                "",
                "## 防洪调度关键阈值",
                "- 防洪高水位: 161.50m",
                "- 当 161.5m < Z <= 161.7m 时，按6000m3/s控制流量下泄。",
                "- 当 Z > 161.7m 时，溢洪道闸门全部打开，机组参与泄洪。",
                "- 当 Z > 165.27m 时，开启泄洪洞参与泄洪，发电暂停。",
            ]
        ),
    }


def parse_pdf_to_structure() -> Dict[str, object]:
    raw_text = _clean_text(_read_text())
    parsed = {
        "reservoir_basic_info": parse_basic_info(raw_text),
        "control_indices": parse_control_indices(raw_text),
        "period_rules": parse_period_rules(),
        "dispatch_rules": parse_dispatch_rules(),
        "dispatch_authority_rules": parse_dispatch_authority_rules(),
        "monthly_operation_plan": [asdict(row) for row in parse_monthly_plan()],
        "warning_rules": parse_warning_rules(),
        "gate_operation_rules": parse_gate_operation_rules(),
        "annual_operation_stats": parse_annual_operation_stats(),
        "gate_operation_log": parse_gate_operation_log(),
        "flood_forecast_stats": parse_flood_forecast_stats(),
        "contact_directory": parse_contact_directory(),
        "engineering_characteristics": parse_engineering_characteristics(),
    }
    return parsed


def export_parsed_artifacts() -> Path:
    config = get_config()
    config.parsed_dir.mkdir(parents=True, exist_ok=True)
    config.rag_docs_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_pdf_to_structure()
    config.parsed_json_path.write_text(
        json.dumps(parsed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for filename, content in build_semantic_docs(parsed).items():
        (config.rag_docs_dir / filename).write_text(content, encoding="utf-8")

    return config.parsed_json_path


if __name__ == "__main__":
    path = export_parsed_artifacts()
    print(f"Parsed JSON written to: {path}")
