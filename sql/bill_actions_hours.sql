-- the action_dates are time_stamped at 6 pm, 7 pm and midnight (which is a default)
select extract(hour from action_date), count(*)
from bills.bill_actions
group by 1
order by 2 desc;

