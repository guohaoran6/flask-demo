#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unittest of project related interface."""
import json
import unittest

from app_test import ApiUnitTest


class ExperimentKpisUnitTest(ApiUnitTest):
    endpoint = '/api/v2/experiments/{}/kpis'
    expected_reaction_query = '''SET mapred.job.name=generate_reaction_6;
SET mapred.job.queue.name=bis;
SET mapred.job.priority=NORMAL;
SET mapred.reduce.tasks=1000;
SET mapred.output.compress=true;
SET hive.exec.compress.output=true;
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
USE regpitari_reports;
CREATE TABLE IF NOT EXISTS reaction_table (
session_id STRING,
easy_id STRING,
page_visits INT,
landing_time TIMESTAMP,
pattern_id STRING,
phxpattern STRING,
device_type STRING,
conversion_time TIMESTAMP,
reaction_type STRING,
reaction_count INT
)
PARTITIONED BY (
experiment_id INT,
period_end TIMESTAMP
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ''
COLLECTION ITEMS TERMINATED BY ''
MAP KEYS TERMINATED BY ''
STORED AS RCFILE
;
INSERT OVERWRITE TABLE reaction_table
PARTITION (experiment_id, period_end)
SELECT
    impressions.session_id
  , impressions.easy_id
  , impressions.page_visits
  , impressions.landing_time
  , impressions.pattern_id
  , impressions.phxpattern
  , impressions.device_type
  , reactions.conversion_time
  , reactions.reaction_type
  , reactions.reaction_count
  , 6 AS experiment_id
  , impressions.period_end

FROM
(SELECT
    30min_session_id_all AS session_id
  , easy_id
  , count(1) AS page_visits
  , min(unix_timestamp(time_stamp)) AS landing_time
  , custom_parameter['phxbanditpattern'] AS pattern_id
  , custom_parameter['phxpattern'] AS phxpattern
  , CASE
        WHEN device_code in ('0') then 'PC'
        WHEN device_code in ('11','12') then 'SP'
        WHEN device_code in ('21','22') then 'TABLET'
    END AS device_type
  , from_unixtime(unix_timestamp(dt, 'yyyy-MM-dd') + 1440*60)  AS period_end
FROM rat_log.rat_log_normalized
WHERE device_code in ('0','11','12','21','22')
  AND service_type = 'phoenix'
  AND event_type = 'async'
  AND dt = '{0}'
  AND time_stamp BETWEEN '2016-01-01 00:00:00' AND '2216-12-31 23:59:59'
AND custom_parameter['phxexperiment'] = '6'
  AND custom_parameter['phxbanditpattern'] IN ('default')
GROUP BY
    30min_session_id_all
  , easy_id
  , custom_parameter['phxbanditpattern']
  , custom_parameter['phxpattern']
  , CASE
        WHEN device_code in ('0') then 'PC'
        WHEN device_code in ('11','12') then 'SP'
        WHEN device_code in ('21','22') then 'TABLET'
    END
  , from_unixtime(unix_timestamp(dt, 'yyyy-MM-dd') + 1440*60)
 ) impressions
LEFT OUTER JOIN
(SELECT
    30min_session_id_all AS session_id
  , easy_id
  , 'conversion_hdcjshd' AS reaction_type
  , count(1) AS reaction_count
  , min(unix_timestamp(time_stamp)) AS conversion_time
FROM rat_log.rat_log_normalized
WHERE
      device_code in ('0','11','12','21','22')
  AND event_type = 'pv'
  AND dt = '{0}'
AND (
(domain = 'else.rakuten.co.jp'
      AND path IN  (
                  '/fashion/yukata/'
                  , '/fashion/swimwear/'
                  )
      )
    
    OR (domain = 'event.rakuten.co.jp'
      AND path IN  (
                  '/fashion/yukata/'
                  , '/fashion/swimwear/'
                  )
      )
    
    OR url LIKE '/fashion/swimwear/%'
         
    OR url LIKE '%/fashion/swimwear/'
         
    OR url LIKE '%/fashion/swimwear/%'
         )
AND (
(domain = 'else.rakuten.co.jp'
      AND path IN  (
                  '/fashion/yukata/'
                  , '/fashion/swimwear/'
                  )
      )
    
    OR (domain = 'event.rakuten.co.jp'
      AND path IN  (
                  '/fashion/yukata/'
                  , '/fashion/swimwear/'
                  )
      )
    
    OR url LIKE '/fashion/swimwear/%'
         
    OR url LIKE '%/fashion/swimwear/'
         
    OR url LIKE '%/fashion/swimwear/%'
         )
AND (
equal_key = 'equal_value'
    
    OR starts_with_key LIKE 'starts_with_value%'
    
    OR ends_with_key LIKE '%ends_with_value'
    
    OR like_key LIKE '%like_value%'
    )
AND (
equal_key2 = 'equal_value2'
    
    )
AND (
(
        page_type IN ('cart_checkout','sp_cart_checkout')
    AND page_name IN ('Cart:Purchase','sp_Cart:Purchase','step5_purchase_complete')
   )
)
GROUP BY
   30min_session_id_all
  , easy_id
) reactions
ON
    impressions.easy_id = reactions.easy_id
AND impressions.session_id = reactions.session_id
;'''

    expected_report_query = '''SET mapred.job.name=generate_report_6;
SET mapred.job.queue.name=bis;
SET mapred.reduce.tasks=1000;
SET mapred.job.priority=NORMAL;
SET mapred.output.compress=true;
SET hive.exec.compress.output=true;
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
USE regpitari_reports;

CREATE TABLE IF NOT EXISTS report_table (
  device_type STRING,
  variation_id INT,
  segment_name STRING,
  condition_id INT,
  pattern_name STRING,
  data MAP<STRING,MAP<STRING,BIGINT>>
)
PARTITIONED BY (
  experiment_id INT,
  period_end TIMESTAMP
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ''
COLLECTION ITEMS TERMINATED BY ''
MAP KEYS TERMINATED BY ''
STORED AS RCFILE
;
INSERT OVERWRITE TABLE report_table
PARTITION (experiment_id, period_end)
SELECT
device_type,
CASE WHEN (pattern_id = 'default') THEN NULL
     ELSE split(pattern_id, '__')[1]
     END AS variation_id,
CASE WHEN (phxpattern = 'default') THEN 'default'
     ELSE split(phxpattern, '__')[1]
     END AS segment_name,
CASE WHEN (pattern_id = 'default') THEN NULL
     ELSE split(pattern_id, '__')[2]
     END AS condition_id,
CASE WHEN (phxpattern = 'default') THEN 'default'
     ELSE split(phxpattern, '__')[2]
     END AS pattern_name,
map('conversion_hdcjshd', map('easy_id_based',count(DISTINCT CASE WHEN (reaction_type='conversion_hdcjshd'
                                                                 AND reaction_count > 0)
                                                           THEN easy_id
                                                           ELSE NULL
                                                            END),

                       'session_based',count(DISTINCT CASE WHEN (reaction_type='conversion_hdcjshd'
                                                                 AND reaction_count > 0 )
                                                           THEN session_id
                                                           ELSE NULL
                                                            END),
                       'overall',SUM(CASE WHEN reaction_type='conversion_hdcjshd'
                                      AND reaction_count > 0
                                      THEN reaction_count
                                      ELSE cast(0 as BIGINT)
                                      END) ),
             'impressions', map('easy_id_based',COUNT(DISTINCT easy_id),
                       'session_based',COUNT(DISTINCT session_id),
                       'overall',cast(SUM(page_visits)/1 as BIGINT)  ) ) AS data,
experiment_id,
period_end
FROM reaction_table
WHERE experiment_id = 6
AND period_end = from_unixtime(unix_timestamp('{0}', 'yyyy-MM-dd') + 1440*60)
AND pattern_id IN ('default')
GROUP BY device_type,
         pattern_id,
         phxpattern,
         experiment_id,
         period_end
;'''

    expected_r2d2_reaction_query = '''SET mapred.job.name=generate_reaction_7;
SET mapred.job.queue.name=bis;
SET mapred.job.priority=NORMAL;
SET mapred.reduce.tasks=1000;
SET mapred.output.compress=true;
SET hive.exec.compress.output=true;
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
USE regpitari_reports;
CREATE TABLE IF NOT EXISTS reaction_table (
session_id STRING,
easy_id STRING,
page_visits INT,
landing_time TIMESTAMP,
pattern_id STRING,
phxpattern STRING,
device_type STRING,
conversion_time TIMESTAMP,
reaction_type STRING,
reaction_count INT
)
PARTITIONED BY (
experiment_id INT,
period_end TIMESTAMP
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ''
COLLECTION ITEMS TERMINATED BY ''
MAP KEYS TERMINATED BY ''
STORED AS RCFILE
;
INSERT OVERWRITE TABLE reaction_table
PARTITION (experiment_id, period_end)
SELECT
    impressions.session_id
  , impressions.easy_id
  , impressions.page_visits
  , impressions.landing_time
  , impressions.pattern_id
  , impressions.phxpattern
  , impressions.device_type
  , reactions.conversion_time
  , reactions.reaction_type
  , reactions.reaction_count
  , 7 AS experiment_id
  , impressions.period_end

FROM
(SELECT
    30min_session_id_all AS session_id
  , CASE
     WHEN easy_id IS NOT NULL AND easy_id NOT IN ('','0') THEN easy_id
     WHEN complemented_easy_id IS NOT NULL AND complemented_easy_id NOT IN ('','0') THEN complemented_easy_id
     ELSE NULL
    END AS easy_id
  , count(1) AS page_visits
  , min(unix_timestamp(time_stamp)) AS landing_time
  , custom_parameter['phxbanditpattern'] AS pattern_id
  , custom_parameter['phxpattern'] AS phxpattern
  , CASE
        WHEN device_code in ('0') then 'PC'
        WHEN device_code in ('11','12') then 'SP'
        WHEN device_code in ('21','22') then 'TABLET'
    END AS device_type
  , from_unixtime(unix_timestamp(dt, 'yyyy-MM-dd') + 1440*60)  AS period_end
  ,rp_cookie
FROM rat_log.rat_log_normalized
WHERE device_code in ('0','11','12','21','22')
  AND service_type = 'phoenix'
  AND event_type = 'async'
  AND dt = '{0}'
  AND time_stamp BETWEEN '2016-01-01 00:00:00' AND '2216-12-31 23:59:59'
AND custom_parameter['phxexperiment'] = '7'
  AND custom_parameter['phxbanditpattern'] IN ('default')
GROUP BY
    30min_session_id_all
  , CASE
     WHEN easy_id IS NOT NULL AND easy_id NOT IN ('','0') THEN easy_id
     WHEN complemented_easy_id IS NOT NULL AND complemented_easy_id NOT IN ('','0') THEN complemented_easy_id
     ELSE NULL
    END
  , custom_parameter['phxbanditpattern']
  , custom_parameter['phxpattern']
  , CASE
        WHEN device_code in ('0') then 'PC'
        WHEN device_code in ('11','12') then 'SP'
        WHEN device_code in ('21','22') then 'TABLET'
    END
  , from_unixtime(unix_timestamp(dt, 'yyyy-MM-dd') + 1440*60)
  ,rp_cookie
 ) impressions
LEFT OUTER JOIN
(SELECT
    session_id
  , easyid AS easy_id
  , 'test_kpi_r2d2' AS reaction_type
  , count(1) AS reaction_count
  , min(from_utc_timestamp(from_unixtime(request_unixtime),'JST')) AS conversion_time
  , rp_cookie
FROM mbs_logana.rlog
WHERE dt = '{0}'
  AND raw_referer LIKE '%://www.rakuten.co.jp%' AND raw_request LIKE '%/s/?%'
  AND type = 'ct'
  AND parse_url(concat('https://rd.rakuten.co.jp',raw_request), 'QUERY','D2') IS NOT NULL
  AND rp_cookie IS NOT NULL
  AND from_utc_timestamp(from_unixtime(request_unixtime),'JST') BETWEEN '2016-01-01 00:00:00' AND '2216-12-31 23:59:59'
AND (
parse_url(concat('https://rd.rakuten.co.jp',raw_request), 'QUERY','D2') = 'parameter'
    )
GROUP BY
   session_id
  , easyid
  , rp_cookie
) reactions
ON impressions.rp_cookie = reactions.rp_cookie
;'''

    expected_reaction_query_with_special_chars = '''SET mapred.job.name=generate_reaction_105;
SET mapred.job.queue.name=bis;
SET mapred.job.priority=NORMAL;
SET mapred.reduce.tasks=1000;
SET mapred.output.compress=true;
SET hive.exec.compress.output=true;
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
USE regpitari_reports;
CREATE TABLE IF NOT EXISTS reaction_table (
session_id STRING,
easy_id STRING,
page_visits INT,
landing_time TIMESTAMP,
pattern_id STRING,
phxpattern STRING,
device_type STRING,
conversion_time TIMESTAMP,
reaction_type STRING,
reaction_count INT
)
PARTITIONED BY (
experiment_id INT,
period_end TIMESTAMP
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ''
COLLECTION ITEMS TERMINATED BY ''
MAP KEYS TERMINATED BY ''
STORED AS RCFILE
;
INSERT OVERWRITE TABLE reaction_table
PARTITION (experiment_id, period_end)
SELECT
    impressions.session_id
  , impressions.easy_id
  , impressions.page_visits
  , impressions.landing_time
  , impressions.pattern_id
  , impressions.phxpattern
  , impressions.device_type
  , reactions.conversion_time
  , reactions.reaction_type
  , reactions.reaction_count
  , 105 AS experiment_id
  , impressions.period_end

FROM
(SELECT
    30min_session_id_all AS session_id
  , easy_id
  , count(1) AS page_visits
  , min(unix_timestamp(time_stamp)) AS landing_time
  , custom_parameter['phxbanditpattern'] AS pattern_id
  , custom_parameter['phxpattern'] AS phxpattern
  , CASE
        WHEN device_code in ('0') then 'PC'
        WHEN device_code in ('11','12') then 'SP'
        WHEN device_code in ('21','22') then 'TABLET'
    END AS device_type
  , from_unixtime(unix_timestamp(dt, 'yyyy-MM-dd') + 1440*60)  AS period_end
FROM rat_log.rat_log_normalized
WHERE device_code in ('0','11','12','21','22')
  AND service_type = 'phoenix'
  AND event_type = 'async'
  AND dt = '{0}'
  AND time_stamp BETWEEN '2016-01-01 00:00:00' AND '2216-12-31 23:59:59'
AND custom_parameter['phxexperiment'] = '105'
  AND custom_parameter['phxbanditpattern'] IN ('default')
GROUP BY
    30min_session_id_all
  , easy_id
  , custom_parameter['phxbanditpattern']
  , custom_parameter['phxpattern']
  , CASE
        WHEN device_code in ('0') then 'PC'
        WHEN device_code in ('11','12') then 'SP'
        WHEN device_code in ('21','22') then 'TABLET'
    END
  , from_unixtime(unix_timestamp(dt, 'yyyy-MM-dd') + 1440*60)
 ) impressions
LEFT OUTER JOIN
(SELECT
    30min_session_id_all AS session_id
  , easy_id
  , 'test_kpi' AS reaction_type
  , count(1) AS reaction_count
  , min(unix_timestamp(time_stamp)) AS conversion_time
FROM rat_log.rat_log_normalized
WHERE
      device_code in ('0','11','12','21','22')
  AND event_type = 'pv'
  AND dt = '{0}'
AND (
(domain = '/sumit/test.co.jp/'
      AND path IN  (
                  '/test/page\;rd=https://www.rakuten.ne.jp/gold/'
                  )
      )
    
    OR (domain = 'event.rakuten.co.jp'
      AND path IN  (
                  '/fashion/yukata/\--&rt=amp\;rd=https://www.rakuten.ne.jp/gold/'
                  , '/fashion/swimwear/'
                  )
      )
    
    )
GROUP BY
   30min_session_id_all
  , easy_id
) reactions
ON
    impressions.easy_id = reactions.easy_id
AND impressions.session_id = reactions.session_id
;'''

    expected_report_query_with_special_chars = '''SET mapred.job.name=generate_report_105;
SET mapred.job.queue.name=bis;
SET mapred.reduce.tasks=1000;
SET mapred.job.priority=NORMAL;
SET mapred.output.compress=true;
SET hive.exec.compress.output=true;
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
USE regpitari_reports;

CREATE TABLE IF NOT EXISTS report_table (
  device_type STRING,
  variation_id INT,
  segment_name STRING,
  condition_id INT,
  pattern_name STRING,
  data MAP<STRING,MAP<STRING,BIGINT>>
)
PARTITIONED BY (
  experiment_id INT,
  period_end TIMESTAMP
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ''
COLLECTION ITEMS TERMINATED BY ''
MAP KEYS TERMINATED BY ''
STORED AS RCFILE
;
INSERT OVERWRITE TABLE report_table
PARTITION (experiment_id, period_end)
SELECT
device_type,
CASE WHEN (pattern_id = 'default') THEN NULL
     ELSE split(pattern_id, '__')[1]
     END AS variation_id,
CASE WHEN (phxpattern = 'default') THEN 'default'
     ELSE split(phxpattern, '__')[1]
     END AS segment_name,
CASE WHEN (pattern_id = 'default') THEN NULL
     ELSE split(pattern_id, '__')[2]
     END AS condition_id,
CASE WHEN (phxpattern = 'default') THEN 'default'
     ELSE split(phxpattern, '__')[2]
     END AS pattern_name,
map('test_kpi', map('easy_id_based',count(DISTINCT CASE WHEN (reaction_type='test_kpi'
                                                                 AND reaction_count > 0)
                                                           THEN easy_id
                                                           ELSE NULL
                                                            END),

                       'session_based',count(DISTINCT CASE WHEN (reaction_type='test_kpi'
                                                                 AND reaction_count > 0 )
                                                           THEN session_id
                                                           ELSE NULL
                                                            END),
                       'overall',SUM(CASE WHEN reaction_type='test_kpi'
                                      AND reaction_count > 0
                                      THEN reaction_count
                                      ELSE cast(0 as BIGINT)
                                      END) ),
             'impressions', map('easy_id_based',COUNT(DISTINCT easy_id),
                       'session_based',COUNT(DISTINCT session_id),
                       'overall',cast(SUM(page_visits)/1 as BIGINT)  ) ) AS data,
experiment_id,
period_end
FROM reaction_table
WHERE experiment_id = 105
AND period_end = from_unixtime(unix_timestamp('{0}', 'yyyy-MM-dd') + 1440*60)
AND pattern_id IN ('default')
GROUP BY device_type,
         pattern_id,
         phxpattern,
         experiment_id,
         period_end
;'''

    def test_get_kpis_success(self):
        """test with correct request of fetching list of kpis (the area which belong to the project)"""
        print("1. test with correct request of fetching list of kpis (the area which belong to the project)")
        experiment_id = 1
        rv = self.app.get(self.endpoint.format(experiment_id))
        assert 200 == rv.status_code
        assert 'based_on' in rv.data
        assert 'experimentId' in rv.data
        assert 'if_reactionQuery_customized' in rv.data
        assert 'if_reportQuery_customized' in rv.data
        assert 'kpiId' in rv.data
        assert 'kpi_definitions' in rv.data
        assert 'reactionQuery' in rv.data
        assert 'reportQuery' in rv.data

    def test_kpi_existence_for_experiment(self):
        """ test experiment which has not been tagged to a KPI """
        print("2. test experiment which has not been tagged to a KPI")
        experiment_id = 6
        rv = self.app.get(self.endpoint.format(experiment_id))
        print(rv.data)
        assert 200 == rv.status_code

    def test_get_kpis_experiment_not_found(self):
        """test with correct request but the experiment is not in db. The server returns error 404"""
        print("3. test with correct request but the experiment is not in db. The server returns error 404")
        rv = self.app.get(self.endpoint.format("1321312"))
        assert 404 == rv.status_code
        assert 'does not exist' in rv.data

    def test_get_kpis_experiment_invalid_format(self):
        """ test with invalid exp id format """
        print("4. test with invalid exp id format")
        rv = self.app.get(self.endpoint.format("ioioiio"))
        assert 400 == rv.status_code

    def test_delete_kpis_success(self):
        """ test delete method for soft delete kpis """
        print("5. test delete method for soft delete kpis")
        experiment_id = 1
        rv = self.app.delete(self.endpoint.format(experiment_id))
        print (rv.data)
        assert 200 == rv.status_code
        assert 'kpiId' in rv.data

    def test_delete_kpis_invalid_experiment(self):
        """ test delete method for invalid experiment sent """
        print("6. test delete method for invalid experiment sent")
        experiment_id = 44
        rv = self.app.delete(self.endpoint.format(experiment_id))
        print (rv.data)
        assert 404 == rv.status_code
        assert "does not exist" in rv.data

    def test_post_kpis_success(self):
        """ testing POST KPI API for success """
        print("7. testing POST KPI API for success")
        experiment_id = 6
        rv = self.app.post(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                           data=json.dumps(
                               {
                                   "based_on": "session",
                                   "kpi_definitions": [
                                       {
                                           "kpi_definition_name": "conversion_hdcjshd",
                                           "main_kpi": True,
                                           "kpi_type": "conversion",
                                           "kpi_conditions": [
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "custom_parameter",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "key": "equal_key",
                                                           "value": "equal_value"
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "key": "starts_with_key",
                                                           "value": "starts_with_value"
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "key": "ends_with_key",
                                                           "value": "ends_with_value"
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "key": "like_key",
                                                           "value": "like_value"
                                                       },
                                                   ]
                                               },
                                               {
                                                   "condition_type": "custom_parameter",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "key": "equal_key2",
                                                           "value": "equal_value2"
                                                       },
                                                   ]
                                               }
                                               ,
                                               {
                                                   "condition_type": "add_to_cart"
                                               }
                                           ]
                                       }
                                   ]
                               }
                           ))
        print(rv.data)
        assert 201 == rv.status_code
        assert 'kpiId' in rv.data
        rv = self.app.get(self.endpoint.format(experiment_id))
        rv_data_json = json.loads(rv.data)
        assert 'starts_with_value%' in rv.data
        assert '%like_value%' in rv.data
        assert '%ends_with_value' in rv.data
        self.assertEquals(self.expected_reaction_query, rv_data_json['reactionQuery'])
        self.assertEquals(self.expected_report_query, rv_data_json['reportQuery'])
        assert 200 == rv.status_code

    def test_post_kpis_with_pattern_mapping(self):
        """ testing POST KPI API with Pattern mapping """
        print("7. testing POST KPI API with Pattern mapping")
        experiment_id = 102
        rv = self.app.post(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                           data=json.dumps(
                               {
                                   "based_on": "session",
                                   "kpi_definitions": [
                                       {
                                           "kpi_definition_name": "conversion_hdcjshd",
                                           "main_kpi": True,
                                           "pattern_name": "seed_data_condition_105",
                                           "kpi_type": "conversion",
                                           "kpi_conditions": [
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "custom_parameter",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "key": "equal_key",
                                                           "value": "equal_value"
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "key": "starts_with_key",
                                                           "value": "starts_with_value"
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "key": "ends_with_key",
                                                           "value": "ends_with_value"
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "key": "like_key",
                                                           "value": "like_value"
                                                       },
                                                   ]
                                               },
                                               {
                                                   "condition_type": "custom_parameter",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "key": "equal_key2",
                                                           "value": "equal_value2"
                                                       },
                                                   ]
                                               }
                                               ,
                                               {
                                                   "condition_type": "add_to_cart"
                                               }
                                           ]
                                       }
                                   ]
                               }
                           ))
        print(rv.data)
        assert 201 == rv.status_code
        assert 'kpiId' in rv.data
        rv = self.app.get(self.endpoint.format(experiment_id))
        rv_data_json = json.loads(rv.data)
        assert 'seed_data_condition_105' in rv.data
        assert 'target__203__111' in rv.data
        assert 200 == rv.status_code

    def test_post_kpis_with_special_characters(self):
        """ testing POST KPI API for special characters in KPI settings """
        print("7. testing POST KPI API for special characters in KPI settings")
        experiment_id = 105
        rv = self.app.post(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                           data=json.dumps(
                               {
                                   "based_on": "easy_id",
                                   "kpi_definitions": [
                                       {
                                           "kpi_definition_name": "test_kpi",
                                           "main_kpi": True,
                                           "pattern_name": "pattern1",
                                           "kpi_type": "conversion",
                                           "kpi_conditions": [
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "/sumit/test.co.jp/",
                                                           "paths": [
                                                               "/test/page;rd=https://www.rakuten.ne.jp/gold/"
                                                           ]
                                                       }, {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/--&rt=amp;rd=https://www.rakuten.ne.jp/gold/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                   ]
                                               }
                                           ]
                                       }
                                   ]
                               }
                           ))
        print(rv.data)
        assert 201 == rv.status_code
        assert 'kpiId' in rv.data
        rv = self.app.get(self.endpoint.format(experiment_id))
        rv_data_json = json.loads(rv.data)
        self.assertEqual(str(self.expected_reaction_query_with_special_chars), str(rv_data_json['reactionQuery']))
        self.assertEqual(str(self.expected_report_query_with_special_chars), rv_data_json['reportQuery'])
        assert 200 == rv.status_code

    def test_post_kpis_success_r2d2(self):
        """ testing POST KPI API for success """
        print("Testing POST KPI API with r2d2 condition")
        experiment_id = 7
        rv = self.app.post(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                           data=json.dumps(
                               {
                                   "based_on": "session",
                                   "kpi_definitions": [
                                       {
                                           "kpi_definition_name": "test_kpi_r2d2",
                                           "main_kpi": True,
                                           "kpi_type": "click",
                                           "kpi_conditions": [
                                               {
                                                   "condition_type": "r2d2",
                                                   "conditions": [
                                                       {
                                                            "operator": "equal",
                                                            "value": "parameter"
                                                       }
                                                   ]
                                               }
                                           ]
                                       }
                                   ]
                               }
                           ))
        print(rv.data)
        assert 201 == rv.status_code
        assert 'kpiId' in rv.data
        rv = self.app.get(self.endpoint.format(experiment_id))
        rv_data_json = json.loads(rv.data)
        assert "'D2') = 'parameter'" in rv.data
        assert self.expected_r2d2_reaction_query == rv_data_json['reactionQuery']
        assert 200 == rv.status_code

    def test_post_kpis_failure(self):
        """ testing POST KPI API for failure"""
        print("8. testing POST KPI API for failure")
        experiment_id = 3
        rv = self.app.post(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                           data=json.dumps(
                               {
                                   "based_on": "session_based",
                                   "kpi_definitions": [
                                       {
                                           "kpi_definition_name": "conversion_hdcjshd",
                                           "main_kpi": True,
                                           "kpi_type": "conversion",
                                           "kpi_conditions": [
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "custom_parameter",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "key": "hgjh",
                                                           "value": "event.rakuten.co.jp"
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "add_to_cart"
                                               }
                                           ]
                                       }
                                   ]
                               }
                           ))
        print(rv.data)
        assert 400 == rv.status_code

    def test_post_kpis_failure_wrong_kpi_definitions(self):
        """ testing POST KPI API failure for wrong KPI definitions """
        print("9. testing POST KPI API failure for wrong KPI definitions")
        experiment_id = 3
        rv = self.app.post(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                           data=json.dumps(
                               {
                                   "based_on": "session",
                                   "kpi_definition": [
                                       {
                                           "kpi_definition_name": "conversion_hdcjshd",
                                           "main_kpi": True,
                                           "kpi_type": "conversion",
                                           "kpi_conditions": [
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "custom_parameter",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "key": "hgjh",
                                                           "value": "event.rakuten.co.jp"
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "add_to_cart"
                                               }
                                           ]
                                       }
                                   ]
                               }
                           ))
        print(rv.data)
        assert 400 == rv.status_code

    def test_post_kpis_failure_kpi_exists(self):
        """ testing post KPI API for failure if KPI already exists """
        print("10. testing post KPI API for failure if KPI already exists")
        experiment_id = 3
        rv = self.app.post(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                           data=json.dumps(
                               {
                                   "based_on": "session",
                                   "kpi_definitions": [
                                       {
                                           "kpi_definition_name": "conversion_hdcjshd",
                                           "main_kpi": True,
                                           "kpi_type": "conversion",
                                           "kpi_conditions": [
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "url",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "domain": "else.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "equal",
                                                           "domain": "event.rakuten.co.jp",
                                                           "paths": [
                                                               "/fashion/yukata/",
                                                               "/fashion/swimwear/"
                                                           ]
                                                       },
                                                       {
                                                           "operator": "starts_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "ends_with",
                                                           "urls": ["/fashion/swimwear/"]
                                                       },
                                                       {
                                                           "operator": "like",
                                                           "urls": ["/fashion/swimwear/"]
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "custom_parameter",
                                                   "conditions": [
                                                       {
                                                           "operator": "equal",
                                                           "key": "hgjh",
                                                           "value": "event.rakuten.co.jp"
                                                       }
                                                   ]
                                               },
                                               {
                                                   "condition_type": "add_to_cart"
                                               }
                                           ]
                                       }
                                   ]
                               }
                           ))
        print(rv.data)
        assert 409 == rv.status_code

    def test_put_kpis_success(self):
        """ testing put KPI API for correct settings """
        print("11. testing put KPI API for correct settings")
        experiment_id = 3
        rv = self.app.put(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                          data=json.dumps(
                              {
                                  "based_on": "session",
                                  "kpi_definitions": [
                                      {
                                          "kpi_definition_name": "conversion_testqqqq",
                                          "main_kpi": True,
                                          "kpi_type": "conversion",
                                          "kpi_conditions": [
                                              {
                                                  "condition_type": "url",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "domain": "else.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "equal",
                                                          "domain": "event.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "starts_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "ends_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "like",
                                                          "urls": ["/fashion/swimwear/"]
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "url",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "domain": "else.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "equal",
                                                          "domain": "event.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "starts_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "ends_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "like",
                                                          "urls": ["/fashion/swimwear/"]
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "custom_parameter",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "key": "hgjh",
                                                          "value": "event.rakuten.co.jp"
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "add_to_cart"
                                              }
                                          ]
                                      }
                                  ]
                              }
                          ))
        print rv.data
        assert 200 == rv.status_code

    def test_put_kpis_with_pattern_mapping(self):
        """ testing put KPI API with Pattern mapping """
        print("11. testing put KPI API for with Pattern mapping")
        experiment_id = 102
        rv = self.app.put(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                          data=json.dumps(
                              {
                                  "based_on": "session",
                                  "kpi_definitions": [
                                      {
                                          "kpi_definition_name": "conversion_testqqqq",
                                          "main_kpi": True,
                                          "pattern_name": "seed_data_condition_105",
                                          "kpi_type": "conversion",
                                          "kpi_conditions": [
                                              {
                                                  "condition_type": "url",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "domain": "else.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "equal",
                                                          "domain": "event.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "starts_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "ends_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "like",
                                                          "urls": ["/fashion/swimwear/"]
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "url",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "domain": "else.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "equal",
                                                          "domain": "event.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "starts_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "ends_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "like",
                                                          "urls": ["/fashion/swimwear/"]
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "custom_parameter",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "key": "hgjh",
                                                          "value": "event.rakuten.co.jp"
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "add_to_cart"
                                              }
                                          ]
                                      }
                                  ]
                              }
                          ))
        print rv.data
        assert 200 == rv.status_code

    def test_put_kpis_failure_wrong_kpi_setting(self):
        """ testing put KPI API for wrong kpi setting sent """
        print("12. testing put KPI API for wrong kpi setting sent")
        experiment_id = 3
        rv = self.app.put(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                          data=json.dumps(
                              {
                                  "based_on": "session",
                                  "kpi_definitions": [
                                      {
                                          "kpi_definition_name": "conversion_test",
                                          "main_kpi": False,
                                          "kpi_type": "conversion",
                                          "kpi_conditions": [
                                              {
                                                  "condition_type": "url",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "domain": "else.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "equal",
                                                          "domain": "event.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "starts_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "ends_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "like",
                                                          "urls": ["/fashion/swimwear/"]
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "url",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "domain": "else.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "equal",
                                                          "domain": "event.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "starts_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "ends_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "like",
                                                          "urls": ["/fashion/swimwear/"]
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "custom_parameter",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "key": "hgjh",
                                                          "value": "event.rakuten.co.jp"
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "add_to_cart"
                                              }
                                          ]}
                                  ]
                              }
                          ))
        print(rv.data)
        assert 400 == rv.status_code
        assert "Wrong KPI Setting" in rv.data

    def test_put_kpis_failure_wrong_enum_value(self):
        """ testing put API for wrong enum values sent """
        print("13. testing put API for wrong enum values sent")
        experiment_id = 3
        rv = self.app.put(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                          data=json.dumps(
                              {
                                  "based_on": "session_based",
                                  "kpi_definitions": [
                                      {
                                          "kpi_definition_name": "conversion_test",
                                          "main_kpi": False,
                                          "kpi_type": "conversion",
                                          "kpi_conditions": None}
                                  ]
                              }
                          ))
        print rv.data
        assert 400 == rv.status_code

    def test_put_kpis_failure_empty_request_body(self):
        """ testing put API for empty request """
        print("14. testing put API for empty request")
        experiment_id = 3
        rv = self.app.put(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                          data=json.dumps(
                              {}
                          ))
        print rv.data
        assert 400 == rv.status_code

    def test_put_kpis_unique_definition_name(self):
        """ testing for unique kpi definition name """
        print("15. testing for unique kpi definition name")
        experiment_id = 3
        rv = self.app.put(self.endpoint.format(experiment_id), content_type='application/json;charset=utf-8',
                          data=json.dumps(
                              {
                                  "based_on": "session",
                                  "kpi_definitions": [
                                      {
                                          "kpi_definition_name": "conversion_test",
                                          "main_kpi": False,
                                          "kpi_type": "conversion",
                                          "kpi_conditions": [
                                              {
                                                  "condition_type": "url",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "domain": "else.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "equal",
                                                          "domain": "event.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "starts_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "ends_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "like",
                                                          "urls": ["/fashion/swimwear/"]
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "url",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "domain": "else.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "equal",
                                                          "domain": "event.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "starts_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "ends_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "like",
                                                          "urls": ["/fashion/swimwear/"]
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "custom_parameter",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "key": "hgjh",
                                                          "value": "event.rakuten.co.jp"
                                                      }
                                                  ]
                                              },
                                              {
                                                  "condition_type": "add_to_cart"
                                              }
                                          ]},
                                      {
                                          "kpi_definition_name": "conversion_test",
                                          "main_kpi": False,
                                          "kpi_type": "conversion",
                                          "kpi_conditions": [
                                              {
                                                  "condition_type": "url",
                                                  "conditions": [
                                                      {
                                                          "operator": "equal",
                                                          "domain": "else.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "equal",
                                                          "domain": "event.rakuten.co.jp",
                                                          "paths": [
                                                              "/fashion/yukata/",
                                                              "/fashion/swimwear/"
                                                          ]
                                                      },
                                                      {
                                                          "operator": "starts_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "ends_with",
                                                          "urls": ["/fashion/swimwear/"]
                                                      },
                                                      {
                                                          "operator": "like",
                                                          "urls": ["/fashion/swimwear/"]
                                                      }
                                                  ]
                                              }
                                          ]
                                      }
                                  ]
                              }
                          ))
        assert 400 == rv.status_code


if __name__ == '__main__':
    unittest.main()
