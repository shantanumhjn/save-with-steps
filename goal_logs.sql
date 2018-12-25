.mode column
.header on
.width 0, 20, 14, 0, 0, 0, 0, 20

select  l.date,
        l.goal_name,
        l.operation,
        l.new_saved - l.old_saved save_change,
        l.new_saved final_Saved,
        l.new_target - l.old_target target_change,
        l.new_target final_target,
        -- l.old_saved,
        -- l.old_target,
        l.comment
from    goal_logs l
-- where   l.goal_id = ?
order   by l.date desc
limit   15
;
