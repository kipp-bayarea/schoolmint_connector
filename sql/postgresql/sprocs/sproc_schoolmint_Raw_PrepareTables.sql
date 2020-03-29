
CREATE PROCEDURE custom."sproc_schoolmint_Raw_PrepareTables"(integer)
LANGUAGE plpgsql
AS $$
BEGIN
/***************************************************************************
Name: custom.sproc_SchoolMint_Raw_PrepareTables

Business Purpose: Prepare primary and backup tables for SchoolMint load.
If the primary table has data, then truncate the backup table and load it with data frim the primary table.
Otherwise, don't truncate the backup table.

Called daily by SchoolMint python code.

Notes:
  - $1 variable is CurrentSchoolYear

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
***************************************************************************/


--If Raw Table has data for the current year, then truncate backup table and load backup table from Raw. Otherwise, dont truncate Backup Table
IF (SELECT COUNT(1) FROM custom."schoolmint_ApplicationData_raw" WHERE "SchoolYear4Digit" = $1 ) > 0
THEN
	TRUNCATE TABLE custom."schoolmint_ApplicationData_raw_backup";

	INSERT INTO custom."schoolmint_ApplicationData_raw_backup"
	SELECT *
	FROM custom."schoolmint_ApplicationData_raw"
	WHERE "SchoolYear4Digit" = $1;

	DELETE FROM custom."schoolmint_ApplicationData_raw"
	WHERE "SchoolYear4Digit" = $1;
END IF;



SELECT COUNT(1) AS ct
FROM custom."schoolmint_ApplicationData_raw"
WHERE "SchoolYear4Digit" = $1;

    END;
$$;