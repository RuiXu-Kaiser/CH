DECLARE @scanhistory xml

set @scanhistory = (SELECT CONVERT(XML, BulkColumn, 2)AS Bulkcolumn
FROM OPENROWSET (BULK '\\csc2cwn21113408.cloud.kp.org\Client$\scanhistory.xml', SINGLE_BLOB) as X)
    
SELECT @scanhistory
    
DECLARE @DocHandle int
    
EXEC sp_xml_preparedocument @DocHandle OUTPUT, @scanhistory
INSERT INTO [Qualys].[dbo].[ScanHistory]
SELECT *
FROM OPENXML (@DocHandle, '/SCAN_LIST_OUTPUT/RESPONSE/SCAN_LIST/SCAN')
WITH(
	DATETIME Datetime '../../../DATETIME',
    REF VARCHAR(50) '../REF',
    TYPE VARCHAR(30) '../TYPE',
	TITLE VARCHAR(200) '../TITLE',
	USER_LOGIN VARCHAR(50) '../USER_LOGIN',
	LAUNCH_DATETIME Datetime '../LAUNCH_DATETIME',
	DURATION VARCHAR(50) '../DURATION',
	PROCESSING_PRIORITY VARCHAR(50) '../PROCESSING_PRIORITY',
	PROCESSED INT '../PROCESSED',
    )
     
EXEC sp_xml_removedocument @DocHandle