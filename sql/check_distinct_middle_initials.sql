-- shouldn't be more than middle initial for each combo of first, last and suffix
SELECT first_name, last_name, name_suffix, COUNT(DISTINCT substring(middle_name from 1 for 1))
FROM person_name
WHERE middle_name <> ''
GROUP BY 1, 2, 3
HAVING COUNT(DISTINCT substring(middle_name from 1 for 1)) > 1;