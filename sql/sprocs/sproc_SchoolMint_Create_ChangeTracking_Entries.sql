CREATE PROC [custom].[sproc_SchoolMint_Create_ChangeTracking_Entries]
AS
SET NOCOUNT ON
/***************************************************************************
Name: custom.sproc_SchoolMint_Create_ChangeTracking_Entries

Business Purpose: Generate change history between schoolmint_applicationdata_raw
(today) and schoolmint_applicationdata_raw_backup (yesterday).
Called daily by SchoolMint python code.

Comments:
2019-10-08	3:30PM		pkats		Initial sproc
2019-10-16	9:30AM		pkats		Modification to use lookup table
***************************************************************************/

INSERT INTO [custom].[schoolmint_ApplicationData_changehistory]
           ([Application_ID]
           ,[SM_Student_ID]
           ,[Application_Student_Id]
           ,[SIS_Student_Id]
           ,[Application_Status]
           ,[Application_Type]
           ,[Account_ID]
           ,[Enrollment_Period]
           ,[Submission_Date]
           ,[Submitted_By]
           ,[Offered_Date]
           ,[Accepted_Date]
           ,[Registration_Completed_Date]
           ,[Last_Update_Date]
           ,[Student_ID]
           ,[Last_Status_Change]
           ,[District]
           ,[Application_Status_Previous]
           ,[Last_Update_Date_Previous]
           ,[Last_Status_Change_Previous]
           ,[ChangeTracking]
           ,[SchoolYear4Digit]
		   )
SELECT  raw1.[Application_ID]
           ,raw1.[SM_Student_ID]
           ,raw1.[Application_Student_Id]
           ,raw1.[SIS_Student_Id]
           ,raw1.[Application_Status]
           ,raw1.[Application_Type]
           ,raw1.[Account_ID]
           ,lk.Enrollment_Period_str
           ,raw1.[Submission_Date]
           ,raw1.[Submitted_By]
           ,raw1.[Offered_Date]
           ,raw1.[Accepted_Date]
           ,raw1.[Registration_Completed_Date]
           ,raw1.[Last_Update_Date]
           ,raw1.[Student_ID]
           ,raw1.[Last_Status_Change]
           ,raw1.[District]
           ,back1.[Application_Status]
           ,back1.[Last_Update_Date]
           ,back1.[Last_Status_Change]
           	,CASE 
			WHEN raw1.Application_ID <> isnull(back1.Application_ID, 999999)
				THEN 'NEW'
			WHEN raw1.[Application_Status] = back1.[Application_Status]
				THEN 'NonStatusChange'
			WHEN raw1.[Application_Status] = isnull(back1.[Application_Status], raw1.[Application_Status])
				THEN 'StatusUpdate'
			WHEN raw1.[Application_Status] <> isnull(back1.[Application_Status], 999)
				THEN 'StatusChange'
			END
		   ,lk.SchoolYear4Digit_int
		FROM [custom].schoolmint_applicationdata_raw raw1
		LEFT JOIN [custom].schoolmint_applicationdata_raw_backup back1 ON raw1.Application_ID = back1.Application_ID
		LEFT JOIN [custom].SchoolMint_lk_Enrollment lk ON raw1.Enrollment_Period = lk.Enrollment_Period_id
		WHERE (
		raw1.[Application_Status] <> isnull(back1.[Application_Status], 999999)
		OR raw1.[Last_Update_Date] <> isnull(back1.[Last_Update_Date], '1970-01-01')
		OR raw1.[Last_Status_Change] <> isnull(back1.[Last_Status_Change], 999999)
		)
		/* Ensure only processing current year */
		AND raw1.SchoolYear4Digit=(SELECT max(schoolyear4digit) FROM [custom].schoolmint_applicationdata_raw)
		/* Ensure no duplicates */
		AND NOT EXISTS (SELECT 1 FROM [custom].[schoolmint_ApplicationData_changehistory] hist WHERE hist.Application_ID=raw1.Application_ID and hist.Last_Status_Change=raw1.Last_Status_Change)



SELECT @@rowcount AS rc

go

