-- update the person_id of the race_candidate records to the id of the person with the full first name
UPDATE race_candidate
SET person_id = a.id
FROM person a
JOIN person b
ON a.nickname = b.first_name
AND a.last_name = b.last_name
AND a.name_suffix = b.name_suffix
WHERE race_candidate.person_id = b.id;

-- update the person_id of the person_name records to the id of the person with the full first name
UPDATE person_name
SET person_id = a.id
FROM person as a
WHERE a.nickname = person_name.first_name
AND a.last_name = person_name.last_name
AND a.name_suffix = person_name.name_suffix;

-- delete any person records without any person_name records
DELETE
FROM person
WHERE id NOT IN (SELECT person_id FROM person_name);
