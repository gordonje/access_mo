-- 98 percent of the duplicate action groups have a 5 to 6 hour duration between the earliest and most recent action date
SELECT 
          duration
        , COUNT(*)
        , COUNT(*)::float / 49914 -- number of duplicate bill_action groups sourced to Open States
FROM (
        -- select from here to get distinct dupe groups with durations
        SELECT 
                  g.bill_id
                , g.description
                , g.actor_id
                , g.the_count
                , e.action_date
                , r.action_date
                , r.action_date - e.action_date as duration
        FROM (
                SELECT 
                          bill_id
                        , description
                        , actor_id
                        , count(*) as the_count
                FROM bills.bill_actions
                WHERE bill_id IS NOT NULL
                AND source_id = 1
                GROUP BY 1, 2, 3
                HAVING count(*) > 1
        ) as g
        JOIN (
                SELECT 
                          bill_id
                        , description
                        , actor_id
                        , action_date
                        , rank() OVER (PARTITION BY bill_id, description, actor_id  ORDER BY action_date) as the_rank
                FROM bills.bill_actions
                WHERE bill_id IS NOT NULL
                AND source_id = 1
        ) as e
        ON g.bill_id = e.bill_id
        AND g.description = e.description
        AND g.actor_id = e.actor_id
        AND e.the_rank = 1
        JOIN (
                SELECT 
                          bill_id
                        , description
                        , actor_id
                        , action_date
                        , rank() OVER (PARTITION BY bill_id, description, actor_id  ORDER BY action_date) as the_rank
                FROM bills.bill_actions
                WHERE bill_id IS NOT NULL
                AND source_id = 1
        ) as r
        ON g.bill_id = r.bill_id
        AND g.description = r.description
        AND g.actor_id = r.actor_id
        AND r.the_rank = g.the_count
        ORDER BY g.the_count
        -- end here to get distinct dupe groups with durations
) AS foo
GROUP BY 1
ORDER BY 2 DESC;