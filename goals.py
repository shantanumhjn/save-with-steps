import sqlite3
import sys
from save_with_steps.db_ops import get_goals
import mytabprint

db_file = "fitbit_data.db"

def print_goals(goal_names):
    headers = ['goal_name', 'amount_saved', 'goal_amount', 'active']
    goals = get_goals()
    goal_names_dict = dict()
    if goal_names:
        for i, goal in enumerate(goals):
            tokens = goal['goal_name'].lower().split()
            for token in tokens:
                if not goal_names_dict.has_key(token):
                    goal_names_dict[token] = []
                goal_names_dict[token].append(i)

    if goal_names:
        goals_to_print = []
        for goal_name in goal_names:
            for _ in goal_names_dict.get(goal_name.lower(), []):
                goals_to_print.append(goals[_])
    else:
        goals_to_print = goals

    mytabprint.print_data(goals_to_print, headers)

def print_goal_logs(goal_names):
    sql = '''
        select  *
        from    (
            select  l.date,
                    l.goal_name,
                    l.operation,
                    l.new_saved - l.old_saved save_change,
                    l.new_saved final_saved,
                    l.new_target - l.old_target target_change,
                    l.new_target final_target,
                    l.comment
            from    goal_logs l
            <where clause>
            order   by l.date desc
            <limit clause>
        )
        order   by date
    '''

    where_clause_replacement = ''
    limit_clause_replacement = ''
    query_data = ()
    if goal_names:
        for i, goal_name in enumerate(goal_names):
            if i == 0:
                where_clause_replacement = '''
                    where    lower(goal_name) like ?
                '''
            else:
                where_clause_replacement += '''
                    or      lower(goal_name) like ?
                '''
            query_data += ('%{}%'.format(goal_name.lower()), )
    else:
        limit_clause_replacement = 'limit 15'

    sql = sql.replace('<where clause>', where_clause_replacement)
    sql = sql.replace('<limit clause>', limit_clause_replacement)

    with sqlite3.connect(db_file) as con:
        con.row_factory = sqlite3.Row
        data = con.execute(sql, query_data).fetchall()

    to_print = []
    for row in data:
        to_print.append({
            'date': row['date'],
            'goal_name': row['goal_name'],
            'operation': row['operation'],
            'save_change': row['save_change'],
            'final_saved': row['final_saved'],
            'target_change': row['target_change'],
            'final_target': row['final_target'],
            'comment': row['comment'],
        })

    headers = ['date', 'goal_name', 'operation', 'save_change', 'final_saved', 'target_change', 'final_target', 'comment']
    mytabprint.print_data(to_print, headers)

if __name__ == "__main__":
    print_goals(sys.argv[1:])
    print
    print_goal_logs(sys.argv[1:])
