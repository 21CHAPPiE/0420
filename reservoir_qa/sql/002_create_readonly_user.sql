USE tk_reservoir_ops;

-- 修改用户名、密码和主机范围后执行
CREATE USER IF NOT EXISTS 'app_query_ro'@'%' IDENTIFIED BY 'password';

GRANT SELECT ON tk_reservoir_ops.reservoir_basic_info TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_control_index TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_period_rule TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_dispatch_rule TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_dispatch_authority_rule TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_monthly_operation_plan TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_warning_rule TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.spillway_gate_operation_rule TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_annual_operation_stat TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_gate_operation_log TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_flood_forecast_stat TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_contact_directory TO 'app_query_ro'@'%';
GRANT SELECT ON tk_reservoir_ops.reservoir_engineering_characteristic TO 'app_query_ro'@'%';

FLUSH PRIVILEGES;
