-- update the person_id of the race_candidate records to be the lowest person_id
UPDATE race_candidate
SET person_id = distinct_person
FROM (
     -- set of dupes on first name, middle initial, last name and name suffix
        SELECT 
                  first_name
                , substring(middle_name from 1 for 1) as mi
                , last_name
                , name_suffix
                -- include the lowest person_id
                , MIN(person_id) AS distinct_person
                , COUNT(distinct person_id) person_count
        FROM person_name
        -- don't include person_name records without a middle_name in the dupe set
        WHERE middle_name <> ''
        GROUP BY 1, 2, 3, 4
        HAVING COUNT(distinct person_id) > 1        
) AS dist
JOIN person_name
ON dist.first_name = person_name.first_name
AND dist.mi = substring(person_name.middle_name from 1 for 1)
AND dist.last_name = person_name.last_name
AND dist.name_suffix = person_name.name_suffix
WHERE race_candidate.person_id = person_name.person_id;

-- update the person_id of the person_name records to the lowest person_id
UPDATE person_name
SET person_id = distinct_person
FROM (
     -- set of dupes on first name, middle initial, last name and name suffix
        SELECT 
                  first_name
                , substring(middle_name from 1 for 1) as mi
                , last_name
                , name_suffix
                -- include the lowest person_id
                , MIN(person_id) AS distinct_person
                , COUNT(distinct person_id) person_count
        FROM person_name
        WHERE middle_name <> ''
        GROUP BY 1, 2, 3, 4
        HAVING COUNT(distinct person_id) > 1        
) AS dist
WHERE dist.first_name = person_name.first_name
AND dist.mi = substring(person_name.middle_name from 1 for 1)
AND dist.last_name = person_name.last_name
AND dist.name_suffix = person_name.name_suffix;

-- delete any person records without any person_name records
DELETE
FROM person
WHERE id NOT IN (SELECT person_id FROM person_name);

-- update the middle_name of the person record to be the full middle name
UPDATE person
SET middle_name = person_name.middle_name
FROM person_name
WHERE person.id = person_id
AND char_length(person.middle_name) = 1
AND char_length(person_name.middle_name) > 1;
