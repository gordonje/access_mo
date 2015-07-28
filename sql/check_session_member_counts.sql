-- Check to see how many members and vacancies for each chamber in each session
select session.assembly_id, session.id, session.year, session.name, sen_count, sen_vac_count, rep_count, rep_vac_count
from session
left join (
        select assembly_id, count(*) as sen_count
        from assembly_member
        where chamber_id = 'S'
        group by 1
) as sen
on session.assembly_id = sen.assembly_id
left join (
        select assembly_id, count(*) as rep_count
        from assembly_member
        where chamber_id = 'H'
        group by 1
) as rep
on session.assembly_id = rep.assembly_id
left join (
        select session_id, count(*) as sen_vac_count
        from district_vacancy
        where chamber_id = 'S'
        group by 1
) as sen_vac
on session.id = sen_vac.session_id
left join (
        select session_id, count(*) as rep_vac_count
        from district_vacancy
        where chamber_id = 'H'
        group by 1
) as rep_vac
on session.id = rep_vac.session_id
where session_type_id = 'R'
order by session.year desc;