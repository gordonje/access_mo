SELECT 
          table_name
        , column_name
        , data_type
        , character_maximum_length
        , ordinal_position
        , col_description(table_name::regclass, ordinal_position)
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;