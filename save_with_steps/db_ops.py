import sqlite3
import datetime
import json

db_file = "fitbit_data.db"

def str_to_date(date_str):
    if date_str:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return datetime.date(dt.year, dt.month, dt.day)
    else:
        return None

def create_schema():
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # daily table
    sql = '''
    create table if not exists daily_steps (
        activity_date   date primary key,
        week_id         text,
        step_count      int,
        save_amount     real
    )
    '''
    cur.execute(sql)

    sql = '''
    create index if not exists daily_steps_idx1 on daily_steps (week_info)
    '''

    # weekly table
    sql = '''
    create table if not exists weekly_steps (
        week_id         text primary key,
        action_taken    int default 0
    )
    '''
    cur.execute(sql)

    # goals table
    sql = '''
        create table if not exists goals (
            goal_id     integer primary key,
            goal_name   text,
            goal_amount int,
            total_saved int default 0,
            is_active   int default 1
        )
    '''
    cur.execute(sql)

    # goal_logs table
    sql = """
        create table if not exists goal_logs (
            date        date default (datetime('now', 'localtime')),
            goal_name   text,
            operation   text,
            old_saved   int,
            old_target  int,
            new_saved   int,
            new_target  int,
            comment     text
        )
    """
    cur.execute(sql)

    sql = 'create index if not exists goal_logs_idx1 on goal_logs (goal_name, operation)'
    cur.execute(sql)


    conn.close()

def log_goal_change(goal_name, operation, old_saved = 0, old_target = 0, new_saved = 0, new_target = 0, comment = None):
    conn = sqlite3.connect(db_file)
    sql = '''
        insert into goal_logs (
            goal_name, operation, old_saved, old_target, new_saved, new_target, comment
        ) values (
            ?, ?, ?, ?, ?, ?, ?
        )
    '''
    conn.execute(sql, (goal_name, operation, old_saved, old_target, new_saved, new_target, comment))
    conn.commit()
    conn.close()

def get_goal_info(goal_name = None, goal_id = None):
    sql = '''
        select  goal_id, goal_name, goal_amount, total_saved, is_active
        from    goals
        where   goal_id = ?
        or      goal_name = ?
    '''
    goal = {}
    conn = sqlite3.connect(db_file)
    r = conn.execute(sql, (goal_id, goal_name)).fetchone()
    conn.close()
    if r is not None:
        goal["id"] = r[0]
        goal["name"] = r[1]
        goal["target"] = r[2]
        goal["saved"] = r[3]
        goal["is_acitve"] = r[4]

    return goal

def add_goal(goal_name, goal_amount = 0):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    sql = '''
        insert into goals (goal_name, goal_amount)
        values (?, ?)
    '''
    cur.execute(sql, (goal_name, goal_amount))

    conn.commit()
    conn.close()

    log_goal_change(
        goal_name = goal_name,
        operation = 'add_goal',
        new_target = goal_amount
    )

def get_goals():
    sql = '''
        select  goal_id,
                goal_name,
                goal_amount,
                total_saved,
                is_active
        from    goals
        order   by goal_id
    '''
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql)
    rs = cur.fetchall()
    conn.close()

    data = []
    for r in rs:
        row = {
            "goal_id": int(r[0]),
            "goal_name": str(r[1]),
            "goal_amount": int(r[2]),
            "amount_saved": int(r[3]),
            "active": (lambda x: "yes" if x == 1 else "no")(int(r[4]))
        }
        data.append(row)
    return data

def round_up_save_amount(amount):
    return int(round(amount, -2))

def disable_enable_goal(disable = True, goal_name = None, goal_id = None):
    goal = get_goal_info(goal_name = goal_name, goal_id = goal_id)
    if not goal.get("id", None): return

    disable_val = not(disable) and 1 or 0
    sql = 'update goals set is_active = ? where goal_id = ?'

    conn = sqlite3.connect(db_file)
    conn.execute(sql, (disable_val, goal_id))
    conn.commit()
    conn.close()

    log_goal_change(
        goal_name = goal["name"],
        operation = "disable_goal" if disable else "enable_goal",
        old_saved = goal["saved"],
        old_target = goal["target"],
        new_saved = goal["saved"],
        new_target = goal["target"]
    )

def update_goal_target(amount, goal_name = None, goal_id = None):
    goal = get_goal_info(goal_name, goal_id)
    if not goal.get("id", None): return

    sql = 'update goals set goal_amount = ? where goal_id = ?'

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql, (amount, goal['id']))
    conn.commit()
    conn.close()

    log_goal_change(
        goal_name = goal['name'],
        operation = 'update_target',
        old_saved = goal['saved'],
        old_target = goal['target'],
        new_saved = goal['saved'],
        new_target = amount
    )

def add_funds_to_goal(amount, goal_name = None, goal_id = None, from_save = False, comment = None):
    goal = get_goal_info(goal_name, goal_id)

    # if invalid input, return
    if not goal.get("id", None): return

    goal_id = goal["id"]
    old_saved = goal["saved"]
    target = goal["target"]
    new_saved = old_saved + amount

    sql = 'update goals set total_saved = ? where goal_id = ?'

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql, (new_saved, goal_id))
    conn.commit()
    conn.close()

    operation = 'add_funds'
    if from_save:
        operation = 'save'
    elif new_saved < old_saved:
        operation = 'remove_funds'

    log_goal_change(
        goal_name = goal["name"],
        operation = operation,
        old_saved = old_saved,
        old_target = target,
        new_saved = new_saved,
        new_target = target,
        comment = comment
    )

def make_a_save(week_id = None, amount = None):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # get the amount if week_id is specified
    if week_id:
        cur.execute('select sum(save_amount), max(activity_date) from daily_steps where week_id = ?', (week_id, ))
        row = cur.fetchone()
        save_amount = round_up_save_amount(row[0])
        high_date = str_to_date(row[1])
        if datetime.date.today() <= high_date:
            return 0
    else:
        save_amount = amount or 0

    # get goals
    cur.execute('select goal_id, total_saved from goals where is_active = 1')
    goals = cur.fetchall()
    num_goals = len(goals)
    conn.close()

    # divide the amount amongst the goals
    if num_goals > 0:
        save_per_goal = save_amount/num_goals
        for i in range(num_goals):
            this_save = 0
            this_save += save_per_goal
            if (i+1) <= (save_amount - (save_per_goal*num_goals)):
                this_save += 1
            add_funds_to_goal(
                amount = this_save,
                goal_id = goals[i][0],
                from_save = True,
                comment = "week_id: {}".format(week_id) if week_id else 'from delete'
            )

    # mark as saved if week_id is specified
    if week_id:
        conn = sqlite3.connect(db_file)
        conn.execute('update weekly_steps set action_taken = 1 where week_id = ?', (week_id, ))
        conn.commit()

    return save_amount

def delete_goal(goal_name = None, goal_id = None, redistribute = True):
    goal = get_goal_info(goal_name = goal_name, goal_id = goal_id)
    if not goal.get("id", None): return

    saved = goal["saved"]

    conn = sqlite3.connect(db_file)
    conn.execute('delete from goals where goal_id = ?', (goal["id"], ))
    conn.commit()
    conn.close()

    log_goal_change(
        goal_name = goal['name'],
        operation = 'delete',
        old_saved = goal['saved'],
        old_target = goal['target'],
        comment = "Redistribute: {}".format(redistribute)
    )

    # now redistribute
    if redistribute: make_a_save(amount = saved)

def get_last_activity_date():
    sql = """
    select  max(strftime('%Y-%m-%d', activity_date))
    from    daily_steps
    """

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql)
    rs = cur.fetchone()
    conn.close()
    return str_to_date(rs[0])

def create_save_object(data):
    save_amount = 0
    daily_data = []
    week_ids = {}
    for row in data["activities-steps"]:
        activity_date = str_to_date(row["dateTime"])
        week_id = "{}-{:02d}".format(activity_date.isocalendar()[0], activity_date.isocalendar()[1])
        week_ids[week_id] = 1
        steps = int(row["value"])
        save_amount = get_save_amount(steps)

        new_row = {}
        new_row["activity_date"] = activity_date
        new_row["activity_date_str"] = activity_date.isoformat()
        new_row["week_id"] = week_id
        new_row["steps"] = steps
        new_row["save_amount"] = save_amount

        daily_data.append(new_row)
    return daily_data, week_ids.keys()

def save_data(data):
    daily_data, week_ids = create_save_object(data)
    daily_sql = '''
    insert or replace into daily_steps
    values (:activity_date_str, :week_id, :steps, :save_amount)
    '''
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.executemany(daily_sql, daily_data)
    conn.commit()

    week_sql = '''
    insert or replace into weekly_steps (week_id)
    values (?)
    '''
    week_ids = [(week_id, ) for week_id in week_ids]
    cur.executemany(week_sql, week_ids)
    conn.commit()
    conn.close()

def get_save_amount(steps, slabs = None):
    # if slabs is None: slabs = [(5000, 0.01), (99999999, 0.25)]
    # if slabs is None: slabs = [20000, (5000, 0.05), (99999999, 0.15)]
    if slabs is None:
        slabs = [
            25000,
            (5000, 0.03),
            (5000, 0.05),
            (99999999, 0.15)
        ]

    high_val = slabs[0]
    esteps = max(high_val-steps, 0)
    save_amount = 0

    for slab in slabs[1:]:
        ratio = slab[1]
        slab_high = slab[0]
        save_amount += min(esteps, slab_high) * ratio
        esteps -= min(esteps, slab_high)

    return save_amount

def update_save_amomunt():
    sql = '''
        select  d.activity_date,
                d.step_count,
                d.save_amount
        from    daily_steps d,
                weekly_steps w
        where   d.week_id = w.week_id
        order   by d.activity_date
    '''
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql)
    rs = cur.fetchall()

    data = []
    for row in rs:
        data.append((get_save_amount(row[1]), row[0]))

    sql = '''
        update  daily_steps
        set     save_amount = ?
        where   activity_date = ?
    '''
    cur.executemany(sql, data)
    conn.commit()
    conn.close()

def get_detail_sql(use_week_id):
    sql1 = '''
        select  activity_date,
                week_id,
                step_count,
                save_amount
        from    daily_steps
        where   week_id = ?
        order   by activity_date
    '''

    sql2 = '''
        select  activity_date,
                week_id,
                step_count,
                save_amount
        from    daily_steps
        where   activity_date between ? and ?
        order   by activity_date
    '''
    if use_week_id:
        return sql1
    else:
        return sql2

def get_details(week_id = None, begin_date = None, end_date = None):
    sql = get_detail_sql(week_id)

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    if week_id:
        cur.execute(sql, (week_id, ))
    else:
        cur.execute(sql, (begin_date, end_date))
    rs = cur.fetchall()
    conn.close()

    data = []
    for r in rs:
        n = {
            "date": str_to_date(r[0]),
            "week_id": r[1],
            "steps": int(r[2]),
            "save_amount": r[3]
        }
        data.append(n)
    return data

def get_summary(get_all = False):
    filter_value = 1
    if get_all: filter_value = 999
    sql = '''
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
          and w.action_taken != ?
        group by
          d.week_id
        order by
          2
    '''
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql, (filter_value, ))
    rs = cur.fetchall()
    conn.close()

    data = []
    for row in rs:
        r = {
            "week_id": row[0],
            "from_date": row[1],
            "to_date": row[2],
            "num_days": int(row[3]),
            "total_steps": int(row[4]),
            "avg_steps": int(row[5]),
            "save_amount": round_up_save_amount(float(row[6])),
            "action_taken": (lambda x: "no" if x == 0 else "yes")(row[7])
        }
        data.append(r)
    return data

def test_save_amount():
    print 'testing save amounts'
    slabs = [25000, (5000, 0.03), (5000, 0.05), (99999999, 0.15)]
    output_format = "{:>10}{:>10}{:>10}"
    print output_format.format("Steps", "Day", "Week")
    for i in range(5, 30):
        a = i*1000
        b = get_save_amount(a, slabs)
        print output_format.format(a, b, b*7)

if __name__ == "__main__":
    test_save_amount()
    # create_schema()
    # print get_last_activity_date()
    # update_save_amomunt()
    # add_goal("RainyDay")
    # add_goal("New Badminton Racket")
    # make_a_save("2017-46")
    # make_a_save("2017-52")
