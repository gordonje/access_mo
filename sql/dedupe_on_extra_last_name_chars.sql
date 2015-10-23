-- update the person_id of the race_candidate records to be the lowest person_id
UPDATE race_candidate
SET person_id = distinct_person
FROM (
        SELECT 
                  first_name
                , middle_name
                , regexp_replace(last_name, '[\s-]', '') as last_name
                , name_suffix
                , MIN(id) AS distinct_person
                , COUNT(id) person_count
        FROM person
        GROUP BY 1, 2, 3, 4
        HAVING COUNT(*) > 1
) AS dist
JOIN person_name
ON dist.first_name = person_name.first_name
AND dist.middle_name =  person_name.middle_name
AND dist.last_name = regexp_replace(person_name.last_name, '[\s-]', '')
AND dist.name_suffix = person_name.name_suffix
WHERE race_candidate.person_id = person_name.person_id;

-- update the person_id of the person_name records to the lowest person_id
UPDATE person_name
SET person_id = distinct_person
FROM (
        SELECT 
                  first_name
                , middle_name
                , regexp_replace(last_name, '[\s-]', '') as last_name
                , name_suffix
                , MIN(id) AS distinct_person
                , COUNT(id) person_count
        FROM person
        GROUP BY 1, 2, 3, 4
        HAVING COUNT(*) > 1
) AS dist
WHERE dist.first_name = person_name.first_name
AND dist.middle_name =  person_name.middle_name
AND dist.last_name = regexp_replace(person_name.last_name, '[\s-]', '')
AND dist.name_suffix = person_name.name_suffix;

-- delete any person records without any person_name records
DELETE
FROM person
WHERE id NOT IN (SELECT person_id FROM person_name);



