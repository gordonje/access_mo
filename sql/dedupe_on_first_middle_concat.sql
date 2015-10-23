-- update the person_id of the race_candidate records to be the lowest person_id
UPDATE race_candidate
SET person_id = distinct_person
FROM (
        SELECT 
                  first_name || middle_name as first_middle
                , last_name
                , name_suffix
                , MIN(person_id) AS distinct_person
                , COUNT(distinct person_id) person_count
        FROM person_name
        GROUP BY 1, 2, 3
        HAVING COUNT(distinct person_id) > 1
) AS dist
JOIN person_name
ON dist.first_middle = person_name.first_name || person_name.middle_name
AND dist.last_name = person_name.last_name
AND dist.name_suffix = person_name.name_suffix
WHERE race_candidate.person_id = person_name.person_id;

-- update the person_id of the person_name records to the lowest person_id
UPDATE person_name
SET person_id = distinct_person
FROM (
        SELECT 
                  first_name || middle_name as first_middle
                , last_name
                , name_suffix
                , MIN(person_id) AS distinct_person
                , COUNT(distinct person_id) person_count
        FROM person_name
        GROUP BY 1, 2, 3
        HAVING COUNT(distinct person_id) > 1        
) AS dist
WHERE dist.first_middle = person_name.first_name || person_name.middle_name
AND dist.last_name = person_name.last_name
AND dist.name_suffix = person_name.name_suffix;

-- delete any person records without any person_name records
DELETE
FROM person
WHERE id NOT IN (SELECT person_id FROM person_name);
