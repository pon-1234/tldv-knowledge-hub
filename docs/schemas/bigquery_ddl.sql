CREATE TABLE `proj-tldv-knowledge.knowledge_ds.transcripts`
(
  meeting_id STRING,
  text STRING,
  start_time FLOAT64,
  end_time FLOAT64,
  speaker_name STRING,
  turn_index INT64,
  inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY TIMESTAMP_TRUNC(inserted_at, DAY);
-- meetings, highlightsテーブルも同様に定義 