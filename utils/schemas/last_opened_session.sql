SELECT
  Sess.Opened as Opened
FROM Sessions as Sess
WHERE
  Sess.Session = :session
  AND Sess.Opened <= :session_date
  AND Sess.Closed = ''
ORDER BY
  Sess.Opened DESC,
  Sess.rowid ASC
LIMIT 1