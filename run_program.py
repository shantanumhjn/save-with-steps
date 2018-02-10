from save_with_steps import db_ops
from save_with_steps import fitbit
import datetime

def take_input(msg):
    print msg,
    inp = str(raw_input())
    # print "input provided:", inp, "of type:", type(inp)
    return inp

keep_running = True
def quit_program():
    global keep_running
    keep_running = False

def wait_after_output(wait = None):
    global keep_running
    if wait:
        if keep_running: take_input("Press enter to continue...")

def invalid_input():
    print
    print "invalid input"
    return True

def none():
    print
    print "i do nothing yet"
    return True

def print_header(output_format, header_cols):
    output_format = output_format.replace(',', '')
    print output_format.format(*header_cols)
    print output_format.format(*['-'*len(header) for header in header_cols])

def show_summary(show_all = False):
    print
    print "showing summary"
    data = db_ops.get_summary(show_all)
    output_format = "{:10}{:12}{:12}{:>6}{:>10,}{:>10,}{:>10,}"
    print_header(output_format, ["Week ID", "From Date", "To Date", "Days", "Steps", "Average", "Save"])
    for r in data:
        print output_format.format(
        r["week_id"], r["from_date"], r["to_date"],
        r["num_days"], r["total_steps"], r["avg_steps"], r["save_amount"]
        )
    return True

def show_full_summary():
    return show_summary(True)

def show_goals(wait = False):
    print
    print "Showing Goals"
    data = db_ops.get_goals()
    output_format = "{:25}{:>20}  {}"
    print_header(output_format, ["Goal Name", "Amount Saved", "Active"])
    for r in data:
        goal_name = "{} ({})".format(r["goal_name"], r["goal_id"])
        amount = (lambda x, y: "{:,}".format(y) if x <= 0 else "{:,}".format(y)+"/"+"{:,}".format(x))(r["goal_amount"], r["amount_saved"])
        print output_format.format(goal_name, amount, r["active"])
    return wait

def add_goal():
    goal_name = str(take_input("goal name:"))
    goal_amount = int((lambda x: x if x.isdigit() else '0')(take_input("goal amount (0 for unknown):")))
    db_ops.add_goal(goal_name, goal_amount)
    print "created a goal named '{}' with a target of {:d}".format(goal_name, goal_amount)

def fetch_new_data():
    print
    fitbit.fetch_n_save_new_data()
    print "Data fetched successfully."
    return True

def make_a_save():
    week_id = str(take_input("Enter week id to save against:"))
    amount = db_ops.make_a_save(week_id)
    print "{:,} saved.".format(amount)
    return True

def show_last_10():
    return show_detail(False)

def show_detail(use_week_id = True):
    week_id = None
    begin_date = None
    end_date = None

    if use_week_id:
        week_id = str(take_input("Enter week id:"))
        msg = "Showing Details for week: {}".format(week_id)
    else:
        begin_date = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
        end_date = datetime.date.today().isoformat()
        msg = "Showing Details from {} to {}".format(begin_date, end_date)

    print
    print msg

    data = db_ops.get_details(week_id = week_id, begin_date = begin_date, end_date = end_date)

    output_format = "{:20}{:>12,}{:>13}"
    headers = ["Activity Date", "Steps Taken", "Save Amount"]
    print_header(output_format, headers)
    for r in data:
        print output_format.format(r["date"].strftime("%a - %b %d, %y"), r["steps"], r["save_amount"])
    return True

def take_goal_input(prompt):
    goal_id = None
    goal_name = str(take_input(prompt))
    if goal_name.isdigit():
        goal_id = int(goal_name)
        goal_name = None
    return (goal_name, goal_id)

def delete_goal():
    (goal_name, goal_id) = take_goal_input("Enter goal name (or id) to delete:")
    redistribute = str(take_input("Redistribute funds (y/[n]):")) or 'n'
    db_ops.delete_goal(goal_name, goal_id, not(redistribute == 'n'))
    out_str = "{} deleted.".format(goal_name)
    if goal_id:
        out_str = "({}) deleted.".format(goal_id)
    print out_str
    return True

def remove_funds():
    (goal_name, goal_id) = take_goal_input("Enter goal name (or id) to remove funds from:")
    amount = int(take_input("Enter amount:"))
    out_str = "{:,} removed from {}".format(amount, goal_name)
    if goal_id:
        out_str = "{:,} removed from ({})".format(amount, goal_id)
    db_ops.add_funds_to_goal(-amount, goal_name, goal_id)
    print out_str
    return True

def add_funds():
    (goal_name, goal_id) = take_goal_input("Enter goal name (or id) to add funds to:")
    amount = int(take_input("Enter amount:"))
    out_str = "{:,} added to {}".format(amount, goal_name)
    if goal_id:
        out_str = "{:,} added to ({})".format(amount, goal_id)
    db_ops.add_funds_to_goal(amount, goal_name, goal_id)
    print out_str
    return True

def update_goal_target():
    (goal_name, goal_id) = take_goal_input("Enter goal name (or id) to update target:")
    amount = int(take_input("Enter amount:"))
    out_str = "Updated target for {} to {:,}".format(goal_name, amount)
    if goal_id:
        out_str = "Updated target for ({}) to {:,}".format(goal_id, amount)
    db_ops.update_goal_target(amount, goal_name, goal_id)
    print out_str
    return True

def disable_enable_goal(disable = True):
    disable_str = disable and "disable" or "enable"
    (goal_name, goal_id) = take_goal_input("Enter goal name (or id) to {}:".format(disable_str))
    disable_str += "d"
    out_str = "Goal {} {}.".format(goal_name, disable_str)
    if goal_id:
        out_str = "Goal ({}) {}.".format(goal_id, disable_str)
    db_ops.disable_enable_goal(disable, goal_name, goal_id)
    print out_str
    return True

def disable_goal():
    return disable_enable_goal()

def enable_goal():
    return disable_enable_goal(False)

def print_goal_options():
    show_goals()
    print
    print "Manage Goals, quit to go back"
    print
    for i in range(len(goal_options)):
        print "{}) {}".format((i+1), goal_options[i][0])

def run_goal_program():
    global keep_running
    while keep_running:
        print_goal_options()
        wait_after_output(goal_options_dict.get(take_input("Whatup!"), invalid_input)())
    keep_running = True

def create_options_dict(options):
    d = {}
    for i in range(len(options)):
        d[str(i+1)] = options[i][1]
        if len(options[i]) > 2:
            for k in options[i][2]:
                d[str(k)] = options[i][1]
    d['q'] = quit_program
    d['quit'] = quit_program
    d['exit'] = quit_program
    return d

main_options = [
    ("View Summary", show_summary, ['v', 'summary']),
    ("Manage Goals", run_goal_program, ['g', 'goals']),
    ("View Last 10 Days", show_last_10, ['l']),
    ("View Week Details", show_detail, ['d']),
    ("Make Save", make_a_save, ['s', 'save']),
    ("Fetch New Data", fetch_new_data, ['r']),
    ("View Full Summary", show_full_summary, ['all']),
    ("Quit", quit_program)
]

main_options_dict = create_options_dict(main_options)
# print main_options_dict

goal_options = [
    ("Add Goal", add_goal, ['n']),
    ("Add Funds to Goal", add_funds),
    ("Delete Goal", delete_goal, ['d']),
    ("Update Goal Target", update_goal_target),
    ("Take out Funds from Goal", remove_funds),
    ("Disable Goal", disable_goal),
    ("Enable Goal", enable_goal),
    ("Quit", quit_program)
]
goal_options_dict = create_options_dict(goal_options)

def print_main_options():
    print
    print "Main Program:"
    for i in range(len(main_options)):
        print "{}) {}".format((i+1), main_options[i][0])

def main():
    global keep_running
    while keep_running:
        print_main_options()
        wait_after_output(main_options_dict.get(take_input("Whatup!"), invalid_input)())

if __name__ == "__main__":
    main()
