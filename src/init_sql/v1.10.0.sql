-- https://github.com/hhyo/Archery/pull/2108
alter table instance_account
    add db_name varchar(128) default '' not null comment '数据库名（mongodb）' after host;

-- instance_account表调整唯一索引

-- 删除外键
set @drop_fk_sql=(select concat('alter table instance_account drop foreign key ',constraint_name) from information_schema.table_constraints where constraint_type='foreign key' and table_name = 'instance_account');
prepare stmt from @drop_fk_sql;
execute stmt;
drop prepare stmt;

set @drop_sql=(select concat('alter table instance_account drop index ', constraint_name) from information_schema.table_constraints where table_schema=database() and table_name='instance_account' and constraint_type='UNIQUE');
prepare stmt from @drop_sql;
execute stmt;
drop prepare stmt;
alter table instance_account add unique index uidx_instanceid_user_host_dbname(`instance_id`, `user`, `host`, `db_name`);

-- 然后在索引重建后，再重新添加外键
alter table instance_account add constraint fk_account_sql_instance_id foreign key (instance_id) references sql_instance(id);

-- 增加 ssl 支持
ALTER TABLE sql_instance ADD is_ssl tinyint(1) DEFAULT 0  COMMENT '是否启用SSL';
