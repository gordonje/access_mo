-- there are several cases where the same district was occupied by two different people in the same election
select assembly_id, chamber_id, district, count(*)
from assembly_member
where chamber_id = 'H'
group by 1, 2, 3
having count(*) > 1
order by 1, 2 desc

select assembly_id, chamber_id, district, count(*)
from assembly_member
where chamber_id = 'H'
group by 1, 2, 3
having count(*) > 1

select *
from person
where last_name like '%Gray%'


