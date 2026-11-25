-- ============================================================
-- 牙科系统：一键建库 + 建全部表 + 插测试数据
-- 用途：云服务器上第一次部署时执行一次即可
-- 用法（在服务器 SSH 里）：
--   mysql -uroot -p < /opt/dental/db/schema.sql
-- 脚本自带 CREATE DATABASE + USE，所以不用先手动建库
-- ============================================================

CREATE DATABASE IF NOT EXISTS dental
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_general_ci;
USE dental;

-- 1) 诊所（单店建模，保留以便扩展）
CREATE TABLE IF NOT EXISTS t_clinic (
  clinic_id   BIGINT       NOT NULL AUTO_INCREMENT,
  name        VARCHAR(80)  NOT NULL,
  timezone    VARCHAR(40)  NOT NULL DEFAULT 'Asia/Shanghai',
  open_time   TIME         NOT NULL DEFAULT '08:30:00',
  close_time  TIME         NOT NULL DEFAULT '18:00:00',
  PRIMARY KEY (clinic_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='诊所';

-- 2) 人（患者与员工共用的身份信息）
CREATE TABLE IF NOT EXISTS t_person (
  person_id   BIGINT      NOT NULL AUTO_INCREMENT,
  name        VARCHAR(40) NOT NULL,
  phone       VARCHAR(20) NOT NULL,
  gender      CHAR(1)     NOT NULL DEFAULT 'U',
  birth_date  DATE        NULL,
  created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (person_id),
  UNIQUE KEY uk_person_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人（患者/员工的共同身份）';

-- 3) 患者（继承自 t_person，主键即 person_id）
CREATE TABLE IF NOT EXISTS t_patient (
  patient_id  BIGINT       NOT NULL,
  remark      VARCHAR(200) NULL,
  PRIMARY KEY (patient_id),
  CONSTRAINT fk_patient_person FOREIGN KEY (patient_id)
    REFERENCES t_person (person_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='患者';

-- 4) 牙椅
CREATE TABLE IF NOT EXISTS t_dental_chair (
  chair_id    BIGINT      NOT NULL AUTO_INCREMENT,
  clinic_id   BIGINT      NOT NULL,
  code        VARCHAR(20) NOT NULL,
  status      VARCHAR(20) NOT NULL DEFAULT 'OPEN',
  PRIMARY KEY (chair_id),
  UNIQUE KEY uk_chair_code (clinic_id, code),
  CONSTRAINT fk_chair_clinic FOREIGN KEY (clinic_id) REFERENCES t_clinic (clinic_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='牙椅';

-- 5) 预约（核心表，INV-1 靠 uk_chair_slot 兜底）
CREATE TABLE IF NOT EXISTS t_appointment (
  appointment_id BIGINT      NOT NULL AUTO_INCREMENT,
  patient_id     BIGINT      NOT NULL,
  chair_id       BIGINT      NOT NULL,
  start_time     DATETIME    NOT NULL,
  end_time       DATETIME    NOT NULL,
  status         VARCHAR(20) NOT NULL DEFAULT 'BOOKED',
  month          CHAR(7)     NOT NULL COMMENT '冗余列：YYYY-MM，由域对象唯一维护',
  version        INT         NOT NULL DEFAULT 0 COMMENT '乐观锁',
  created_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (appointment_id),
  UNIQUE KEY uk_chair_slot (chair_id, start_time),
  KEY idx_patient_time (patient_id, start_time),
  KEY idx_month_status (month, status),
  CONSTRAINT fk_appt_patient FOREIGN KEY (patient_id) REFERENCES t_patient (patient_id),
  CONSTRAINT fk_appt_chair   FOREIGN KEY (chair_id)   REFERENCES t_dental_chair (chair_id),
  CONSTRAINT ck_appt_time    CHECK (end_time > start_time),
  CONSTRAINT ck_appt_status  CHECK (status IN
    ('BOOKED','CONFIRMED','ARRIVED','IN_PROGRESS','DONE','CANCELLED','NO_SHOW'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预约';

-- 6) 提醒计划（第 9 章）
CREATE TABLE IF NOT EXISTS t_reminder_plan (
  plan_id         BIGINT       AUTO_INCREMENT PRIMARY KEY,
  appointment_id  BIGINT       NOT NULL,
  openid          VARCHAR(64)  NOT NULL DEFAULT 'demo-openid',
  channel         VARCHAR(16)  NOT NULL DEFAULT 'WECHAT',
  template_id     VARCHAR(64)  NULL,
  plan_send_at    DATETIME     NOT NULL,
  status          VARCHAR(16)  NOT NULL DEFAULT 'PENDING',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_plan_appointment (appointment_id),
  CONSTRAINT fk_plan_appt FOREIGN KEY (appointment_id)
    REFERENCES t_appointment (appointment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提醒计划';

-- 7) 提醒发送记录（答辩"消息网关可替换"的物证）
CREATE TABLE IF NOT EXISTS t_reminder_log (
  log_id          BIGINT       AUTO_INCREMENT PRIMARY KEY,
  plan_id         BIGINT       NULL,
  appointment_id  BIGINT       NOT NULL,
  channel         VARCHAR(16)  NOT NULL,
  title           VARCHAR(64)  NOT NULL,
  content         VARCHAR(255) NOT NULL,
  result          VARCHAR(16)  NOT NULL,
  fail_reason     VARCHAR(255) NULL,
  sent_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提醒发送记录';

-- ============ 测试数据 ============
INSERT INTO t_clinic (name) VALUES ('示例牙科诊所');

INSERT INTO t_person (name, phone, gender, birth_date) VALUES
  ('张三', '13800000001', 'M', '1990-05-12'),
  ('李四', '13800000002', 'F', '1985-11-03'),
  ('王医生', '13900000001', 'M', '1980-02-20');

INSERT INTO t_patient (patient_id, remark) VALUES (1, '对青霉素过敏'), (2, NULL);

INSERT INTO t_dental_chair (clinic_id, code) VALUES (1, 'A1'), (1, 'A2');
