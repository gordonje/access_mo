-- update the person_id of the race_candidate records to be the lowest person_id
UPDATE race_candidate
SET person_id = distinct_person
FROM (
        SELECT 
                  group_id as name_group
                , last_name
                , name_suffix
                , MIN(person.id) AS distinct_person
                , COUNT(distinct person.id) person_count
        FROM person
        JOIN name_group
        ON first_name = name
        GROUP BY 1, 2, 3
        HAVING COUNT(distinct person.id) > 1
) AS dist
JOIN name_group
ON dist.name_group = name_group.group_id
JOIN person
ON name_group.name = person.first_name
AND dist.last_name = person.last_name
AND dist.name_suffix = person.name_suffix
WHERE race_candidate.person_id = person.id
AND person.id <> dist.distinct_person;

-- update the person_id of the person_name records to the lowest person_id
UPDATE person_name
SET person_id = distinct_person
FROM (
        SELECT 
                  group_id as name_group
                , last_name
                , name_suffix
                , MIN(person.id) AS distinct_person
                , COUNT(distinct person.id) person_count
        FROM person
        JOIN name_group
        ON first_name = name
        GROUP BY 1, 2, 3
        HAVING COUNT(distinct person.id) > 1
) AS dist
JOIN name_group
ON dist.name_group = name_group.group_id
JOIN person
ON name_group.name = person.first_name
AND dist.last_name = person.last_name
AND dist.name_suffix = person.name_suffix
WHERE person_name.person_id = person.id
AND dist.distinct_person <> person_name.person_id;

-- delete any person records without any person_name records
DELETE
FROM person
WHERE id NOT IN (SELECT person_id FROM person_name);
