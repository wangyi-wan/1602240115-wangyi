-- ============================================================
-- 消息提醒相关表（第 9 章用）
-- 用法：DBeaver 里打开这个文件，全选，按 Alt+X 执行
-- 或者在命令行：mysql -uroot -p dental < C:\dental\db\reminder.sql
-- ============================================================

-- 提醒计划：预约成功时建一条，到点前 24 小时触发发送
CREATE TABLE IF NOT EXISTS t_reminder_plan (
  plan_id         BIGINT       AUTO_INCREMENT PRIMARY KEY,
  appointment_id  BIGINT       NOT NULL,
  openid          VARCHAR(64)  NOT NULL DEFAULT 'demo-openid',
  channel         VARCHAR(16)  NOT NULL DEFAULT 'WECHAT',   -- WECHAT / SMS / MANUAL
  template_id     VARCHAR(64)  NULL,
  plan_send_at    DATETIME     NOT NULL,
  status          VARCHAR(16)  NOT NULL DEFAULT 'PENDING',  -- PENDING / SENT / FAILED
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  -- INV 兜底：一个预约只应有一条提醒计划，重复提交不会插两遍
  UNIQUE KEY uk_plan_appointment (appointment_id),
  CONSTRAINT fk_plan_appt FOREIGN KEY (appointment_id)
    REFERENCES t_appointment (appointment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提醒计划';

-- 提醒发送记录：不管走哪个通道、成功还是降级，都留痕
-- 这张表就是答辩时"消息网关可替换"的证据
CREATE TABLE IF NOT EXISTS t_reminder_log (
  log_id          BIGINT       AUTO_INCREMENT PRIMARY KEY,
  plan_id         BIGINT       NULL,
  appointment_id  BIGINT       NOT NULL,
  channel         VARCHAR(16)  NOT NULL,                    -- WECHAT / SMS / MANUAL / STUB
  title           VARCHAR(64)  NOT NULL,
  content         VARCHAR(255) NOT NULL,
  result          VARCHAR(16)  NOT NULL,                    -- OK / FAIL / STUB / MANUAL
  fail_reason     VARCHAR(255) NULL,
  sent_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提醒发送记录';
