-- three quarters of the bills have duplicate actions
select count(*)::float / (select count(*) from bills.bills)::float as pct_bills_w_dupes
from (
        select bill_id, count(*) as num_dupe_actions
        from (
                select bill_id, description, actor_id, count(*)
                from bills.bill_actions
                group by 1, 2, 3
                having count(*) > 1
        ) as sub2
        join bills.bills
        on sub2.bill_id = bills.id
        join legislative.sessions
        on bills.session_id = sessions.id
        group by 1
) as sub;