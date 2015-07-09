-- there are 50,250 duplicate bill actions
select count(*)
from (
        -- there are, at most, 16 duplicates per bill_action
        select bill_id, description, actor_id, count(*)
        from bills.bill_actions
        where bill_id is not null
        group by 1, 2, 3
        having count(*) > 1
        order by 4 desc
) as foo;