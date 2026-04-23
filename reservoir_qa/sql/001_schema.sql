CREATE DATABASE IF NOT EXISTS tk_reservoir_ops
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE tk_reservoir_ops;

CREATE TABLE IF NOT EXISTS reservoir_basic_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    reservoir_name VARCHAR(128) NOT NULL,
    station_name VARCHAR(128) DEFAULT NULL,
    river_name VARCHAR(128) DEFAULT NULL,
    basin_name VARCHAR(128) DEFAULT NULL,
    location_desc VARCHAR(255) DEFAULT NULL,
    upstream_area_km2 DECIMAL(12,2) DEFAULT NULL,
    installed_capacity_mw DECIMAL(10,2) DEFAULT NULL,
    reservoir_type VARCHAR(64) DEFAULT NULL,
    main_functions VARCHAR(255) DEFAULT NULL,
    owner_org VARCHAR(255) DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_reservoir_code (reservoir_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_control_index (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    index_code VARCHAR(64) NOT NULL,
    index_name VARCHAR(128) NOT NULL,
    index_value DECIMAL(16,4) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    season_tag VARCHAR(64) DEFAULT NULL,
    control_type VARCHAR(64) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    valid_year INT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_reservoir_index (reservoir_code, index_code, season_tag, valid_year)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_period_rule (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    rule_year INT NOT NULL,
    period_code VARCHAR(64) NOT NULL,
    period_name VARCHAR(128) NOT NULL,
    start_date DATE DEFAULT NULL,
    end_date DATE DEFAULT NULL,
    control_water_level_m DECIMAL(10,3) DEFAULT NULL,
    upper_water_level_m DECIMAL(10,3) DEFAULT NULL,
    lower_water_level_m DECIMAL(10,3) DEFAULT NULL,
    rule_text TEXT DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_period_rule (reservoir_code, rule_year, period_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_dispatch_rule (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    rule_year INT NOT NULL,
    rule_code VARCHAR(64) NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    scenario_type VARCHAR(64) NOT NULL,
    period_code VARCHAR(64) DEFAULT NULL,
    trigger_type VARCHAR(64) DEFAULT NULL,
    min_water_level_m DECIMAL(10,3) DEFAULT NULL,
    max_water_level_m DECIMAL(10,3) DEFAULT NULL,
    threshold_flow_m3s DECIMAL(12,3) DEFAULT NULL,
    forecast_condition VARCHAR(255) DEFAULT NULL,
    action_text TEXT NOT NULL,
    action_type VARCHAR(64) DEFAULT NULL,
    priority_no INT DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_dispatch_rule (reservoir_code, rule_year, rule_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_dispatch_authority_rule (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    rule_year INT NOT NULL,
    authority_code VARCHAR(64) NOT NULL,
    period_code VARCHAR(64) DEFAULT NULL,
    trigger_desc VARCHAR(255) NOT NULL,
    min_water_level_m DECIMAL(10,3) DEFAULT NULL,
    max_water_level_m DECIMAL(10,3) DEFAULT NULL,
    min_flow_m3s DECIMAL(12,3) DEFAULT NULL,
    max_flow_m3s DECIMAL(12,3) DEFAULT NULL,
    authority_org VARCHAR(255) NOT NULL,
    copy_to_orgs TEXT DEFAULT NULL,
    remarks TEXT DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_dispatch_authority (reservoir_code, rule_year, authority_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_monthly_operation_plan (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    plan_year INT NOT NULL,
    plan_month TINYINT NOT NULL,
    rainfall_mm DECIMAL(10,2) DEFAULT NULL,
    inflow_100m_m3 DECIMAL(12,4) DEFAULT NULL,
    upstream_intake_100m_m3 DECIMAL(12,4) DEFAULT NULL,
    month_start_wl_m DECIMAL(10,3) DEFAULT NULL,
    month_end_wl_m DECIMAL(10,3) DEFAULT NULL,
    generation_water_100m_m3 DECIMAL(12,4) DEFAULT NULL,
    water_consumption_rate_m3_per_kwh DECIMAL(12,4) DEFAULT NULL,
    generation_10k_kwh DECIMAL(14,2) DEFAULT NULL,
    notes VARCHAR(255) DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_monthly_plan (reservoir_code, plan_year, plan_month)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_warning_rule (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    rule_year INT NOT NULL,
    warning_code VARCHAR(64) NOT NULL,
    warning_name VARCHAR(255) NOT NULL,
    warning_type VARCHAR(64) NOT NULL,
    trigger_desc TEXT NOT NULL,
    trigger_water_level_m DECIMAL(10,3) DEFAULT NULL,
    trigger_flow_m3s DECIMAL(12,3) DEFAULT NULL,
    lead_time_minutes INT DEFAULT NULL,
    warning_scope TEXT DEFAULT NULL,
    disposal_text TEXT DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_warning_rule (reservoir_code, rule_year, warning_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS spillway_gate_operation_rule (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    rule_year INT NOT NULL,
    gate_group_name VARCHAR(128) DEFAULT NULL,
    operation_type VARCHAR(32) NOT NULL,
    sequence_no INT NOT NULL,
    gate_no VARCHAR(16) NOT NULL,
    remarks VARCHAR(255) DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_gate_op_rule (reservoir_code, rule_year, operation_type, sequence_no)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_annual_operation_stat (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    stat_year INT DEFAULT NULL,
    rainfall_mm DECIMAL(10,2) DEFAULT NULL,
    inflow_100m_m3 DECIMAL(12,4) DEFAULT NULL,
    generation_10k_kwh DECIMAL(14,3) DEFAULT NULL,
    is_average_row TINYINT NOT NULL DEFAULT 0,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_gate_operation_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    event_time DATETIME NOT NULL,
    upstream_wl_m DECIMAL(10,3) DEFAULT NULL,
    downstream_wl_m DECIMAL(10,3) DEFAULT NULL,
    gate_1_opening_m DECIMAL(10,3) DEFAULT NULL,
    gate_2_opening_m DECIMAL(10,3) DEFAULT NULL,
    gate_3_opening_m DECIMAL(10,3) DEFAULT NULL,
    gate_4_opening_m DECIMAL(10,3) DEFAULT NULL,
    gate_5_opening_m DECIMAL(10,3) DEFAULT NULL,
    gate_6_opening_m DECIMAL(10,3) DEFAULT NULL,
    outflow_m3s DECIMAL(12,3) DEFAULT NULL,
    source_event VARCHAR(128) DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_flood_forecast_stat (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    flood_no VARCHAR(32) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    rainfall_mm DECIMAL(10,2) DEFAULT NULL,
    actual_peak_m3s DECIMAL(12,3) DEFAULT NULL,
    forecast_peak_m3s DECIMAL(12,3) DEFAULT NULL,
    forecast_accuracy_pct DECIMAL(6,2) DEFAULT NULL,
    flood_volume_100m_m3 DECIMAL(12,4) DEFAULT NULL,
    highest_wl_m DECIMAL(10,3) DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_contact_directory (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    person_name VARCHAR(64) NOT NULL,
    role_title VARCHAR(255) NOT NULL,
    phone_number VARCHAR(32) DEFAULT NULL,
    team_type VARCHAR(64) DEFAULT NULL,
    remarks VARCHAR(255) DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_engineering_characteristic (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    category_name VARCHAR(128) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value VARCHAR(255) DEFAULT NULL,
    unit VARCHAR(64) DEFAULT NULL,
    remark VARCHAR(255) DEFAULT NULL,
    source_doc VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reservoir_event_timeseries (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reservoir_code VARCHAR(64) NOT NULL,
    event_id VARCHAR(32) NOT NULL,
    observation_no INT NOT NULL,
    event_time DATETIME NOT NULL,
    rainfall_mm DECIMAL(10,4) DEFAULT NULL,
    water_level_m DECIMAL(10,3) DEFAULT NULL,
    outflow_m3s DECIMAL(12,3) DEFAULT NULL,
    inflow_m3s DECIMAL(12,3) DEFAULT NULL,
    source_filename VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_event_timeseries (reservoir_code, event_id, observation_no),
    KEY idx_event_timeseries_time (event_time),
    KEY idx_event_timeseries_event_time (event_id, event_time)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stg_pdf_section_text (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_doc VARCHAR(255) NOT NULL,
    section_code VARCHAR(64) NOT NULL,
    section_title VARCHAR(255) NOT NULL,
    section_text LONGTEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stg_pdf_table_row (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_doc VARCHAR(255) NOT NULL,
    table_code VARCHAR(64) NOT NULL,
    row_index_no INT NOT NULL,
    row_json JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
