-- there are a few folks who, within a given assembly, have multiple member records 
select person_id, first_name, last_name, assembly_id, count(*)
from assembly_member
join person
on person.id = person_id
group by 1, 2, 3, 4
having count(*) > 1
order by count(*) desc;

-- these are cases where the member transitioned from one chamber to the other
select foo.person_id, first_name, last_name, foo.assembly_id, chamber_id
from assembly_member
join (
        select person_id, first_name, last_name, assembly_id, count(*)
        from assembly_member
        join person
        on person.id = person_id
        group by 1, 2, 3, 4
        having count(*) > 1
) as foo
on assembly_member.person_id = foo.person_id
and foo.assembly_id = assembly_member.assembly_id
order by assembly_member.person_id, assembly_member.assembly_id;

