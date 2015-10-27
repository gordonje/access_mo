-- Insert assembly member records for winning race candidates
INSERT INTO assembly_member (
          assembly_id
        , person_id
        , chamber_id
        , district
        , party
        , counties
        , race_candidate_id
        , source_doc_id
        , created_date
)
SELECT 
          election.assembly_id
        , race_candidate.person_id
        , CASE 
                WHEN race_type.name = 'State Senator' THEN 'S'
                WHEN race_type.name = 'State Representative' THEN 'H'
          END as chamber_id
        , race.district
        , NULL as party
        , NULL as counties
        , race_candidate.id
        , NULL as source_doc
        , now() as created_date
FROM race_candidate
JOIN race
ON race_id = race.id
JOIN race_type
ON race_type_id = race_type.id
JOIN election
ON election_id = election.id
WHERE rank = 1
-- this excludes primary races
AND election.assembly_id IS NOT NULL
ORDER BY assembly_id, district;

-- since senators serve four years, insert records for their second assembly
INSERT INTO assembly_member (
          assembly_id
        , person_id
        , chamber_id
        , district
        , party
        , counties
        , race_candidate_id
        , source_doc_id
        , created_date
)
SELECT 
          assembly_member.assembly_id + 1 as assembly_id
        , assembly_member.person_id
        , assembly_member.chamber_id
        , assembly_member.district
        , NULL as party
        , NULL as counties
        , assembly_member.race_candidate_id
        , NULL as source_doc
        , now() as created_date
FROM assembly_member
JOIN race_candidate
ON race_candidate.id = race_candidate_id
JOIN race
ON race.id = race_id
JOIN election 
ON election.id = election_id
JOIN election_type
ON election_type_id = election_type.id
WHERE chamber_id = 'S'
-- excluding special elections, these need to be handled separately
AND election.election_type_id <> 'S';


-- Jack Goodman was elected to Senate District 29 in Nov. 2005, making sure he is added to the 94th Assembly
INSERT INTO assembly_member (
          assembly_id
        , person_id
        , chamber_id
        , district
        , party
        , counties
        , race_candidate_id
        , source_doc_id
        , created_date
)
SELECT
          94 as assembly_id
        , assembly_member.person_id
        , 'S' as chamber_id
        , 29 as district
        , NULL as party
        , NULL as counties
        , assembly_member.race_candidate_id
        , NULL as source_doc
        , now() as created_date
FROM assembly_member
JOIN race_candidate
ON assembly_member.person_id = race_candidate.person_id
JOIN race
ON race.id = race_id
JOIN election
ON election.id = election_id
WHERE assembly_member.assembly_id = 93
AND assembly_member.district = 29
AND chamber_id = 'S'
AND election_type_id  = 'S';

-- Maida Coleman was elected to the Senate District 5 in Feb. 2002, making sure she is added to the 92nd Assembly
INSERT INTO assembly_member (
          assembly_id
        , person_id
        , chamber_id
        , district
        , party
        , counties
        , race_candidate_id
        , source_doc_id
        , created_date
)
SELECT
          92 as assembly_id
        , assembly_member.person_id
        , 'S' as chamber_id
        , 5 as district
        , NULL as party
        , NULL as counties
        , assembly_member.race_candidate_id
        , NULL as source_doc
        , now() as created_date
FROM assembly_member
JOIN race_candidate
ON assembly_member.person_id = race_candidate.person_id
JOIN race
ON race.id = race_id
JOIN election
ON election.id = election_id
WHERE assembly_member.assembly_id = 91
AND assembly_member.district = 5
AND chamber_id = 'S'
AND election_date = '2002-02-05';

-- Harry Kennedy was elected to Senate District 3 in Dec 2001, making sure he is in the 92 Assembly
INSERT INTO assembly_member (
          assembly_id
        , person_id
        , chamber_id
        , district
        , party
        , counties
        , race_candidate_id
        , source_doc_id
        , created_date
)
SELECT
          92 as assembly_id
        , assembly_member.person_id
        , 'S' as chamber_id
        , 3 as district
        , NULL as party
        , NULL as counties
        , assembly_member.race_candidate_id
        , NULL as source_doc
        , now() as created_date
FROM assembly_member
JOIN race_candidate
ON assembly_member.person_id = race_candidate.person_id
JOIN race
ON race.id = race_id
JOIN election
ON election.id = election_id
WHERE assembly_member.assembly_id = 91
AND assembly_member.district = 3
AND chamber_id = 'S'
AND election_type_id  = 'S';

-- Mary Bland was elected to the Senate District 9 in Dec 1998, making sure she is added to the 90th General Assembly
INSERT INTO assembly_member (
          assembly_id
        , person_id
        , chamber_id
        , district
        , party
        , counties
        , race_candidate_id
        , source_doc_id
        , created_date
)
SELECT
          90 as assembly_id
        , assembly_member.person_id
        , 'S' as chamber_id
        , 9 as district
        , NULL as party
        , NULL as counties
        , race_candidate_id
        , NULL as source_doc
        , now() as created_date
FROM assembly_member
JOIN race_candidate
ON assembly_member.person_id = race_candidate.person_id
JOIN race
ON race.id = race_id
JOIN election
ON election.id = election_id
WHERE assembly_member.assembly_id = 89
AND assembly_member.district = 9
AND chamber_id = 'S'
AND election_type_id  = 'S';