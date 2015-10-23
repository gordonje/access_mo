-- Insert a party primary race for each party
-- Creates 2747 new race records
INSERT INTO public.race (
            election_id
          , race_type_id
          , district
          , party
          , unexpired
          , num_precincts
          , total_votes
          , created_date
)
SELECT 
          race.election_id
        , race.race_type_id
        , race.district
        , race_candidate.party
        , race.unexpired
        , race.num_precincts
        , SUM(votes) as total_votes
        , race.created_date
FROM public.race_candidate
JOIN public.race
ON race.id = race_candidate.race_id
JOIN public.race_type
ON race.race_type_id = race_type.id
JOIN public.election
ON race.election_id = election.id
JOIN public.election_type
ON election.election_type_id = election_type.id
WHERE race_type.name in ('State Senator', 'State Representative')
AND election_type.name = 'Primary'
GROUP BY 1, 2, 3, 4, 5, 6, 8;

-- Add an old_race_id column to the race_candidate table
ALTER TABLE race_candidate
ADD COLUMN old_race_id INT;

UPDATE public.race_candidate
SET old_race_id = race_id;

-- Insert new race_candidate records
-- Creates 3658 new race_candidate records
INSERT INTO public.race_candidate (
          race_id
        , raw_name
        , person_id
        , party
        , votes
        , pct_votes
        , old_race_id
        , created_date
) 
SELECT 
          new_race.id as race_id
        , race_candidate.raw_name
        , race_candidate.person_id
        , race_candidate.party
        , race_candidate.votes
        , race_candidate.pct_votes
        , race_candidate.old_race_id
        , race_candidate.created_date
FROM public.race_candidate
JOIN public.race as old_race
ON race_candidate.old_race_id = old_race.id
JOIN public.race as new_race
ON old_race.election_id = new_race.election_id
AND old_race.district = new_race.district
AND old_race.race_type_id = new_race.race_type_id
AND race_candidate.party = new_race.party;

-- Delete the race candidate records linked to primary races without a party
DELETE 
FROM public.race_candidate
WHERE race_id in (
        SELECT race.id 
        FROM public.race
        JOIN public.race_type
        ON race.race_type_id = race_type.id
        JOIN public.election
        ON race.election_id = election.id
        JOIN public.election_type
        ON election.election_type_id = election_type.id
        WHERE race_type.name in ('State Senator', 'State Representative')
        AND election_type.name = 'Primary'
        AND race.party IS NULL
);

-- Delete the race records for primary races that don't have a party
DELETE 
FROM public.race
WHERE race.id in (
        SELECT race.id 
        FROM public.race
        JOIN public.race_type
        ON race.race_type_id = race_type.id
        JOIN public.election
        ON race.election_id = election.id
        JOIN public.election_type
        ON election.election_type_id = election_type.id
        WHERE race_type.name in ('State Senator', 'State Representative')
        AND election_type.name = 'Primary'
        AND race.party IS NULL
);

-- Drop the old_race_id column
ALTER TABLE public.race_candidate
DROP COLUMN old_race_id;