select
  w.week_id,
  min(d.activity_date) from_date,
  max(d.activity_date) to_date,
  count(d.activity_date) num_days,
  sum(d.step_count) total_steps,
  round(avg(d.step_count)) avg_steps,
  round(sum(d.save_amount)) total_to_save,
  w.action_taken
from
  daily_steps d,
  weekly_steps w
where
  w.week_id = d.week_id
group by
  d.week_id
order by
  2;
