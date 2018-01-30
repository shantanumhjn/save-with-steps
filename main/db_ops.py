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

    conn.close()

def add_goal(goal_name, goal_amount = -1):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    sql = '''
        insert into goals (goal_name, goal_amount)
        values (?, ?)
    '''
    cur.execute(sql, (goal_name, goal_amount))

    conn.commit()
    conn.close()

def make_a_save(week_id):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # get the amount
    cur.execute('select sum(save_amount) from daily_steps where week_id = ?', (week_id, ))
    save_amount = int(round(cur.fetchone()[0], -2))

    # get goals
    cur.execute('select goal_id, total_saved from goals where is_active = 1')
    goals = cur.fetchall()
    num_goals = len(goals)

    # divide the amount amongst the goals
    if num_goals > 0:
        save_per_goal = save_amount/num_goals
        for i in range(num_goals):
            this_save = goals[i][1]
            this_save += save_per_goal
            if (i+1) <= (save_amount - (save_per_goal*num_goals)):
                this_save += 1
            goals[i] = (this_save, goals[i][0])

        cur.executemany('update goals set total_saved = ? where goal_id = ?', goals)
        conn.commit()

    # mark as saved
    cur.execute('update weekly_steps set action_taken = 1 where week_id = ?', (week_id, ))
    conn.commit()

    conn.close()

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
        week_id = "{}-{}".format(activity_date.isocalendar()[0], activity_date.isocalendar()[1])
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
    if slabs is None: slabs = [(5000, 0.05), (99999999, 0.15)]

    high_val = 20000
    esteps = max(high_val-steps, 0)
    save_amount = 0

    for slab in slabs:
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

if __name__ == "__main__":
    None
    # create_schema()
    # print get_last_activity_date()
    # update_save_amomunt()
    # add_goal("RainyDay")
    # add_goal("New Badminton Racket")
    # make_a_save("2017-46")
    # make_a_save("2017-52")
