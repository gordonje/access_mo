-- 86 percent of the bill_actions records come from open states
select source_id, sources.name, count(*)::float / (select count(*) from bills.bill_actions)
from bills.bill_actions
join data.sources
on sources.id = source_id
group by 1, 2
order by 3 desc;