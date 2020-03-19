SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [custom].[SchoolMint_ProgressMonitoring](
	[Schoolyear4digit] [int] NOT NULL,
	[School] [varchar](50) NOT NULL,
	[Grade_level] [varchar](50) NOT NULL,
	[Goal_type] [varchar](50) NOT NULL,
	[Goal_num] [varchar](50) NOT NULL,
	[Goal_date] [date] NOT NULL,
    SystemSchoolID int,
	LkSchoolID int
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
