-- bills with most duplicate actions
select bill_id, bills.name, bills.session_id, sessions.display_name, count(*) as num_dupe_actions
from (
        select bill_id, description, actor_id, count(*)
        from bills.bill_actions
        where bill_id is not null
        group by 1, 2, 3
        having count(*) > 1
) as sub
join bills.bills
on sub.bill_id = bills.id
join legislative.sessions
on bills.session_id = sessions.id
group by 1, 2, 3, 4
order by count(*) desc;