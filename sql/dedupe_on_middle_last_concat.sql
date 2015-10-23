-- update the person_id of the race_candidate records to the id of the person with the full last name
UPDATE race_candidate
SET person_id = a.person_id
FROM person_name as a
JOIN person_name as b
ON a.first_name = b.first_name
AND a.last_name ~~ (b.middle_name || '%' || b.last_name)
AND a.name_suffix = b.name_suffix
WHERE race_candidate.person_id = b.person_id
AND b.middle_name <> '';

-- update the person_id of the person_name records to the id of the person with the full last name
UPDATE person_name
SET person_id = a.person_id
FROM person_name as a
WHERE a.first_name = person_name.first_name
AND a.last_name ~~ (person_name.middle_name || '%' || person_name.last_name)
AND a.name_suffix = person_name.name_suffix
AND person_name.middle_name <> '';

-- delete any person records without any person_name records
DELETE
FROM person
WHERE id NOT IN (SELECT person_id FROM person_name);

