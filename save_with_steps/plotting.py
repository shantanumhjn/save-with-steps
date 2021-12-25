import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import dateutil.parser as dateparser

'''
    # need to convert the date strings into date
    import dateutil.parser as dateparser
    # grouping data by date
    data_by_date = {}
    for entry in goal_logs["logs"]:
        ts = dateparser.parse(entry["date"])
        new_saved = entry["new_saved"]

        previous_entry = data_by_date.setdefault(ts.date(), (ts, new_saved))
        if ts > previous_entry[0]:
            data_by_date[ts.date()] = (ts, new_saved)

    # print data_by_date

    sorted_data = sorted(data_by_date.items(), key = lambda k: k[0])

    x = [i[0] for i in sorted_data]
    y = [i[1][1] for i in sorted_data]
    # print y

    sorted_data = sorted(goal_logs['logs'])

'''

def fix_data(goals_with_logs):
    # convert to date, group by date and then sort
    fixed_data = {}

    # grouping data by date
    data_by_date = {}
    for goal_name, logs in goals_with_logs.items():
        for entry in logs:
            this_ts = dateparser.parse(entry["date"])
            new_saved = entry["new_saved"]

            previous_entry = data_by_date.setdefault(this_ts.date(), (this_ts, new_saved))
            if this_ts > previous_entry[0]:
                data_by_date[this_ts.date()] = (this_ts, new_saved)

        sorted_data = sorted(data_by_date.items(), key = lambda k: k[0])
        x = [i[0] for i in sorted_data]
        y = [i[1][1] for i in sorted_data]

        fixed_data[goal_name] = (x, y)

    return fixed_data


def plot_goal_log(goals_with_logs):
    fixed_data = fix_data(goals_with_logs)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    # plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    # plt.plot(x, y, 'b+')
    # print x

    plt.gcf().autofmt_xdate()
    plt.grid(True)

    for goal_name, data in fixed_data.items():
        plt.plot(data[0], data[1], label=goal_name)
    plt.legend()

    plt.show()


if __name__ == "__main__":
    a = [1, 2, 3]
    plot(range(len(a)), a)
