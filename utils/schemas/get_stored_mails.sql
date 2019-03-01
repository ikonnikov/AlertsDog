SELECT
  Mails.ID as ID,
  Mails.ReceiveDate as ReceiveDate,
  Mails.Subject as Subject,
  Mails.Sender as Sender
FROM Mails as Mails
WHERE
  Mails.ReceiveDate >= :session_start
  AND Mails.ReceiveDate <= :session_end
ORDER BY
  Mails.ReceiveDate ASC,
  Mails.ID ASC